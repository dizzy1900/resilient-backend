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
    
    Args:
        lat: Latitude
        lon: Longitude
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
    
    Returns:
        Dictionary with 'avg_temp_c' (average max temperature in Celsius)
        and 'total_precip_mm' (total precipitation in mm)
    """
    authenticate_gee()
    
    point = ee.Geometry.Point([lon, lat])
    
    dataset = ee.ImageCollection('ECMWF/ERA5_LAND/DAILY_AGGR') \
        .filterBounds(point) \
        .filterDate(start_date, end_date)
    
    # Get average of max temperature (Kelvin to Celsius)
    temp_max = dataset.select('temperature_2m_max').mean()
    temp_value = temp_max.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=point,
        scale=11132
    ).get('temperature_2m_max')
    avg_temp_c = ee.Number(temp_value).subtract(273.15).getInfo()
    
    # Get total precipitation (already in meters, convert to mm)
    precip = dataset.select('total_precipitation_sum').sum()
    precip_value = precip.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=point,
        scale=11132
    ).get('total_precipitation_sum')
    total_precip_mm = ee.Number(precip_value).multiply(1000).getInfo()
    
    return {
        'avg_temp_c': avg_temp_c,
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
    
    wave_collection = ee.ImageCollection('ECMWF/ERA5/DAILY') \
        .filterBounds(point) \
        .filterDate(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')) \
        .select('significant_wave_height_of_combined_wind_waves_and_swell')
    
    max_wave_height = wave_collection.max().reduceRegion(
        reducer=ee.Reducer.max(),
        geometry=point,
        scale=11132
    ).get('significant_wave_height_of_combined_wind_waves_and_swell')
    max_wave_height = ee.Number(max_wave_height).getInfo()
    
    return {
        'slope_pct': slope_pct,
        'max_wave_height': max_wave_height
    }
