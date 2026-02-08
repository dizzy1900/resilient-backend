# =============================================================================
# Coastal Resilience Engine - Flood Risk Analysis
# =============================================================================

import json
import os
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


def analyze_flood_risk(lat: float, lon: float, slr_meters: float, surge_meters: float) -> dict:
    """
    Analyze flood risk at a coastal location based on sea level rise and storm surge.
    
    Uses elevation data to determine if a location will be underwater and calculates
    flood depth based on combined sea level rise and storm surge.
    
    Args:
        lat: Latitude
        lon: Longitude
        slr_meters: Sea level rise in meters (e.g., 0.5 for 50cm)
        surge_meters: Storm surge height in meters (e.g., 2.0 for 2m surge)
    
    Returns:
        Dictionary with:
        - 'elevation_m': Ground elevation in meters above sea level
        - 'is_underwater': Boolean indicating if location will be flooded
        - 'flood_depth_m': Depth of flooding in meters (0 if not flooded)
        - 'risk_category': Risk level (Low, Moderate, High, Extreme)
    """
    authenticate_gee()
    
    # Create point geometry
    point = ee.Geometry.Point([lon, lat])
    
    # Load NASA NASADEM (30m resolution global elevation model)
    # This is the latest version of SRTM data
    elevation_dataset = ee.Image('NASA/NASADEM_HGT/001').select('elevation')
    
    # Get elevation at the point
    elevation_value = elevation_dataset.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=point,
        scale=30  # 30m resolution
    ).get('elevation')
    
    # Convert to Python value
    elevation_m = ee.Number(elevation_value).getInfo()
    
    # Handle case where elevation data is not available (e.g., over ocean)
    if elevation_m is None:
        elevation_m = 0.0
    
    # Calculate total water level
    total_water_level = slr_meters + surge_meters
    
    # Determine if location is underwater
    is_underwater = elevation_m < total_water_level
    
    # Calculate flood depth (0 if not flooded)
    flood_depth_m = max(0.0, total_water_level - elevation_m)
    
    # Determine risk category based on flood depth
    if flood_depth_m == 0:
        risk_category = "Low"
    elif flood_depth_m < 0.5:
        risk_category = "Moderate"
    elif flood_depth_m < 1.5:
        risk_category = "High"
    else:
        risk_category = "Extreme"
    
    return {
        'elevation_m': round(elevation_m, 2),
        'is_underwater': is_underwater,
        'flood_depth_m': round(flood_depth_m, 2),
        'risk_category': risk_category
    }


def calculate_flood_frequency(slr_meters: float) -> dict:
    """
    Calculate flood frequency depths for different storm return periods.
    
    Uses research-based baseline surge heights and projects future depths
    by adding sea level rise.
    
    Args:
        slr_meters: Sea level rise in meters (e.g., 0.5 for 50cm)
    
    Returns:
        Dictionary with:
        - 'storm_chart_data': List of objects with period, current_depth, future_depth
    """
    # Baseline Surge Heights (from research)
    base_surges = {
        '1yr': 0.6,
        '10yr': 1.2,
        '50yr': 1.9,
        '100yr': 2.5
    }
    
    # Calculate future depths by adding sea level rise
    storm_chart_data = []
    
    for period, current_depth in base_surges.items():
        future_depth = current_depth + slr_meters
        
        storm_chart_data.append({
            'period': period,
            'current_depth': round(current_depth, 2),
            'future_depth': round(future_depth, 2)
        })
    
    # Sort by severity (1yr, 10yr, 50yr, 100yr)
    # Define custom sort order
    period_order = {'1yr': 1, '10yr': 2, '50yr': 3, '100yr': 4}
    storm_chart_data.sort(key=lambda x: period_order.get(x['period'], 999))
    
    return {
        'storm_chart_data': storm_chart_data
    }


def analyze_urban_impact(lat: float, lon: float, total_water_level: float) -> dict:
    """
    Analyze urban flood impact within a 5km buffer around a coastal location.
    
    Identifies built-up areas using land cover data and calculates how much
    urban area will be flooded based on elevation and water level.
    
    Args:
        lat: Latitude
        lon: Longitude
        total_water_level: Combined sea level rise + surge in meters
    
    Returns:
        Dictionary with:
        - 'total_urban_km2': Total urban/built-up area in square kilometers
        - 'flooded_urban_km2': Urban area that will be flooded in square kilometers
        - 'urban_impact_pct': Percentage of urban area impacted
    """
    authenticate_gee()
    
    # Create 5km buffer around the point
    point = ee.Geometry.Point([lon, lat])
    buffer = point.buffer(5000)  # 5km in meters
    
    # Load ESA WorldCover 10m land cover dataset
    # Class 50 = Built-up
    land_cover = ee.ImageCollection('ESA/WorldCover/v200') \
        .first() \
        .select('Map')
    
    # Create built-up area mask (value 50 = Built-up)
    urban_mask = land_cover.eq(50)
    
    # Load NASA NASADEM elevation data
    elevation = ee.Image('NASA/NASADEM_HGT/001').select('elevation')
    
    # Create flood mask (areas where elevation < total_water_level)
    flood_mask = elevation.lt(total_water_level)
    
    # Combine masks: urban areas that are flooded
    flooded_urban_mask = urban_mask.And(flood_mask)
    
    # Calculate pixel areas in square meters
    pixel_area = ee.Image.pixelArea()
    
    # Calculate total urban area
    total_urban_area_m2 = urban_mask.multiply(pixel_area).reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=buffer,
        scale=100,  # 100m resolution for faster processing
        maxPixels=1e9
    ).get('Map')
    
    # Calculate flooded urban area
    flooded_urban_area_m2 = flooded_urban_mask.multiply(pixel_area).reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=buffer,
        scale=100,
        maxPixels=1e9
    ).get('Map')
    
    # Convert to Python values
    total_urban_area_m2 = ee.Number(total_urban_area_m2).getInfo()
    flooded_urban_area_m2 = ee.Number(flooded_urban_area_m2).getInfo()
    
    # Handle None values (no urban area found)
    if total_urban_area_m2 is None:
        total_urban_area_m2 = 0.0
    if flooded_urban_area_m2 is None:
        flooded_urban_area_m2 = 0.0
    
    # Convert from square meters to square kilometers
    total_urban_km2 = total_urban_area_m2 / 1_000_000
    flooded_urban_km2 = flooded_urban_area_m2 / 1_000_000
    
    # Calculate impact percentage
    if total_urban_km2 > 0:
        urban_impact_pct = (flooded_urban_km2 / total_urban_km2) * 100
    else:
        urban_impact_pct = 0.0
    
    return {
        'total_urban_km2': round(total_urban_km2, 2),
        'flooded_urban_km2': round(flooded_urban_km2, 2),
        'urban_impact_pct': round(urban_impact_pct, 2)
    }
