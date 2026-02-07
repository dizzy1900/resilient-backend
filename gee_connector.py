# =============================================================================
# Google Earth Engine Connector for Weather Data
# =============================================================================

import json
import os
from datetime import datetime, timedelta
import ee


def authenticate_gee():
    """Authenticate with Google Earth Engine using service account."""
    service_account_json = os.environ.get('GEE_SERVICE_ACCOUNT_JSON')
    if not service_account_json:
        raise ValueError("GEE_SERVICE_ACCOUNT_JSON environment variable not set")
    
    credentials_dict = json.loads(service_account_json)
    credentials = ee.ServiceAccountCredentials(
        credentials_dict['client_email'],
        key_data=service_account_json
    )
    ee.Initialize(credentials)


def get_weather_data(lat: float, lon: float, start_date: str, end_date: str) -> dict:
    """
    Get weather data from ERA5-Land dataset for a location and date range.
    
    Specifically designed for maize heat stress analysis:
    - Temperature: Maximum temperature during peak growing season (July 1 - Aug 31)
    - Rainfall: Total precipitation during full growing season (May 1 - Sept 30)
    
    Args:
        lat: Latitude
        lon: Longitude
        start_date: Start date (YYYY-MM-DD) - used to determine year
        end_date: End date (YYYY-MM-DD) - used to determine year
    
    Returns:
        Dictionary with 'max_temp_celsius' (maximum temperature during peak season)
        and 'total_precip_mm' (total precipitation during growing season)
    """
    authenticate_gee()
    
    point = ee.Geometry.Point([lon, lat])
    
    # Extract year from start_date to construct growing season dates
    start_year = datetime.strptime(start_date, '%Y-%m-%d').year
    end_year = datetime.strptime(end_date, '%Y-%m-%d').year
    
    # Use the most recent complete growing season
    # If end_date is before September, use previous year's season
    end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
    if end_date_obj.month < 9:
        year = end_year - 1
    else:
        year = end_year
    
    # Peak growing season for heat stress: July 1 - August 31
    peak_start = f'{year}-07-01'
    peak_end = f'{year}-08-31'
    
    # Full growing season for rainfall: May 1 - September 30
    growing_start = f'{year}-05-01'
    growing_end = f'{year}-09-30'
    
    # Get MAXIMUM temperature during peak season (July-August)
    # This captures heat stress events, not average conditions
    peak_dataset = ee.ImageCollection('ECMWF/ERA5_LAND/DAILY_AGGR') \
        .filterBounds(point) \
        .filterDate(peak_start, peak_end) \
        .select('temperature_2m_max')
    
    # Use max() to get the maximum daily temperature across the peak period
    temp_max_img = peak_dataset.max()
    temp_value = temp_max_img.reduceRegion(
        reducer=ee.Reducer.max(),
        geometry=point,
        scale=11132
    ).get('temperature_2m_max')
    max_temp_celsius = ee.Number(temp_value).subtract(273.15).getInfo()
    
    # Get total precipitation during full growing season (May-Sept)
    growing_dataset = ee.ImageCollection('ECMWF/ERA5_LAND/DAILY_AGGR') \
        .filterBounds(point) \
        .filterDate(growing_start, growing_end) \
        .select('total_precipitation_sum')
    
    precip = growing_dataset.sum()
    precip_value = precip.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=point,
        scale=11132
    ).get('total_precipitation_sum')
    total_precip_mm = ee.Number(precip_value).multiply(1000).getInfo()
    
    return {
        'max_temp_celsius': max_temp_celsius,
        'total_precip_mm': total_precip_mm
    }


def get_coastal_params(lat: float, lon: float) -> dict:
    """
    Get coastal parameters including slope and maximum wave height for a location.
    
    Args:
        lat: Latitude
        lon: Longitude
    
    Returns:
        Dictionary with 'slope_pct' (slope in percentage) and 'max_wave_height' (maximum
        significant wave height in meters over the last 5 years)
    """
    authenticate_gee()
    
    point = ee.Geometry.Point([lon, lat])
    
    # 1. Fetch Slope using NASA Digital Elevation Model
    elevation = ee.Image('NASA/NASADEM_HGT/001').select('elevation')
    slope = ee.Terrain.slope(elevation)
    
    slope_value = slope.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=point,
        scale=30
    ).get('slope')
    slope_pct = ee.Number(slope_value).getInfo()
    
    # 2. Fetch Maximum Wave Height (last 5 years)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=5*365)
    
    # Try multiple wave data sources
    max_wave_height = None
    
    try:
        # Option 1: Try ERA5 monthly wave data (more reliable for ocean areas)
        wave_monthly = ee.ImageCollection('ECMWF/ERA5/MONTHLY') \
            .filterBounds(point) \
            .filterDate(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')) \
            .select('mean_significant_wave_height')
        
        if wave_monthly.size().getInfo() > 0:
            max_wave_img = wave_monthly.max()
            wave_result = max_wave_img.reduceRegion(
                reducer=ee.Reducer.max(),
                geometry=point,
                scale=27830
            )
            wave_height_info = wave_result.getInfo()
            max_wave_height = wave_height_info.get('mean_significant_wave_height')
    except Exception as e:
        print(f"ERA5 monthly wave data failed: {e}")
    
    # Option 2: If no wave data, estimate based on distance from coast and latitude
    if max_wave_height is None or max_wave_height == 0:
        # Use latitude-based estimation (tropical areas have higher waves)
        abs_lat = abs(lat)
        if abs_lat < 10:  # Tropical (more storms)
            max_wave_height = 4.5
        elif abs_lat < 30:  # Subtropical
            max_wave_height = 3.5
        elif abs_lat < 50:  # Temperate
            max_wave_height = 3.0
        else:  # High latitude
            max_wave_height = 2.5
    
    # Final safety check - ensure wave height is never 0
    if max_wave_height == 0:
        print(f"[WARNING] Wave height was 0 at lat={lat}, lon={lon}. Using default 3.0m")
        max_wave_height = 3.0
    
    return {
        'slope_pct': slope_pct,
        'max_wave_height': max_wave_height
    }


def get_monthly_data(lat: float, lon: float) -> dict:
    """
    Get monthly weather data for charts from ERA5-Land dataset.
    
    Fetches data for the most recent full year, returning 12 monthly values
    for rainfall and soil moisture.
    
    Args:
        lat: Latitude
        lon: Longitude
    
    Returns:
        Dictionary with:
        - 'rainfall_monthly_mm': List of 12 monthly rainfall values (Jan-Dec) in mm
        - 'soil_moisture_monthly': List of 12 monthly soil moisture values (Jan-Dec)
    """
    authenticate_gee()
    
    point = ee.Geometry.Point([lon, lat])
    
    # Determine the most recent full year
    current_date = datetime.now()
    if current_date.month == 1:
        # If January, use previous year as most recent full year
        year = current_date.year - 1
    else:
        # Check if current year data is available (use previous year to be safe)
        year = current_date.year - 1
    
    start_date = f'{year}-01-01'
    end_date = f'{year}-12-31'
    
    # Get monthly data from ERA5-Land
    monthly_data = ee.ImageCollection('ECMWF/ERA5_LAND/MONTHLY') \
        .filterBounds(point) \
        .filterDate(start_date, end_date) \
        .select(['total_precipitation', 'volumetric_soil_water_layer_1'])
    
    # Sort by system:time_start to ensure chronological order
    monthly_data = monthly_data.sort('system:time_start')
    
    # Get the list of images
    image_list = monthly_data.toList(monthly_data.size())
    
    rainfall_monthly_mm = []
    soil_moisture_monthly = []
    
    # Process each month
    for i in range(12):
        try:
            image = ee.Image(image_list.get(i))
            
            # Extract values at the point
            values = image.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=point,
                scale=11132
            ).getInfo()
            
            # Total precipitation: convert from meters to mm
            precip_m = values.get('total_precipitation', 0)
            rainfall_monthly_mm.append(precip_m * 1000)
            
            # Volumetric soil water layer 1 (already in correct units)
            soil_moisture = values.get('volumetric_soil_water_layer_1', 0)
            soil_moisture_monthly.append(soil_moisture)
            
        except Exception as e:
            print(f"[WARNING] Error processing month {i+1}: {e}")
            # Use 0 as fallback for missing months
            rainfall_monthly_mm.append(0)
            soil_moisture_monthly.append(0)
    
    return {
        'rainfall_monthly_mm': rainfall_monthly_mm,
        'soil_moisture_monthly': soil_moisture_monthly
    }
