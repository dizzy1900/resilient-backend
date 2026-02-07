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
