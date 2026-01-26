# =============================================================================
# Google Earth Engine Connector for Weather Data
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
