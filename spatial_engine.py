#!/usr/bin/env python3
"""Spatial Engine - Polygon Processing and Risk Analysis
========================================================

Processes GeoJSON polygons for Digital Twin analysis, calculating:
- Polygon area in square kilometers
- Fractional exposure to climate risks
- Scaled financial risk based on exposure

This module enables true spatial analysis beyond single point coordinates.
"""

from typing import Dict, Any, Tuple, Optional
import math
import json

try:
    from shapely.geometry import shape, Point, Polygon
    from shapely.ops import transform
    import pyproj
    SHAPELY_AVAILABLE = True
except ImportError:
    SHAPELY_AVAILABLE = False


def validate_geojson(geojson: Dict[str, Any]) -> bool:
    """Validate that a dictionary is a valid GeoJSON Feature or Geometry.
    
    Args:
        geojson: Dictionary containing GeoJSON data
        
    Returns:
        True if valid, False otherwise
    """
    if not isinstance(geojson, dict):
        return False
    
    # Check if it's a Feature
    if geojson.get('type') == 'Feature':
        return 'geometry' in geojson and geojson['geometry'] is not None
    
    # Check if it's a Geometry
    geometry_types = ['Point', 'LineString', 'Polygon', 'MultiPoint', 
                     'MultiLineString', 'MultiPolygon', 'GeometryCollection']
    if geojson.get('type') in geometry_types:
        return 'coordinates' in geojson
    
    return False


def extract_geometry(geojson: Dict[str, Any]) -> Dict[str, Any]:
    """Extract geometry from GeoJSON Feature or Geometry.
    
    Args:
        geojson: GeoJSON Feature or Geometry object
        
    Returns:
        Geometry dictionary
    """
    if geojson.get('type') == 'Feature':
        return geojson['geometry']
    return geojson


def calculate_polygon_area_sqkm(geometry: Dict[str, Any]) -> float:
    """Calculate the area of a polygon in square kilometers.
    
    Uses geodetic calculations for accurate area on Earth's surface.
    Falls back to simple planar approximation if shapely is unavailable.
    
    Args:
        geometry: GeoJSON Geometry object (must be Polygon or MultiPolygon)
        
    Returns:
        Area in square kilometers
    """
    if not SHAPELY_AVAILABLE:
        # Fallback: simple planar approximation
        return _calculate_area_fallback(geometry)
    
    try:
        # Convert GeoJSON to shapely geometry
        geom = shape(geometry)
        
        # Define WGS84 (lat/lon) and a suitable projection for area calculation
        # Using Albers Equal Area for accurate area calculations
        wgs84 = pyproj.CRS('EPSG:4326')
        
        # Get centroid to determine appropriate UTM zone or use World Mollweide
        centroid = geom.centroid
        
        # Use World Mollweide projection (ESRI:54009) for global equal-area calculations
        equal_area = pyproj.CRS('ESRI:54009')
        
        # Create transformer
        project = pyproj.Transformer.from_crs(wgs84, equal_area, always_xy=True).transform
        
        # Transform geometry to equal-area projection
        geom_projected = transform(project, geom)
        
        # Calculate area in square meters and convert to square kilometers
        area_sqm = geom_projected.area
        area_sqkm = area_sqm / 1_000_000
        
        return round(area_sqkm, 4)
        
    except Exception as e:
        # Fallback if projection fails
        return _calculate_area_fallback(geometry)


def _calculate_area_fallback(geometry: Dict[str, Any]) -> float:
    """Fallback area calculation using simple planar approximation.
    
    Uses the Shoelace formula with rough lat/lon to meter conversion.
    Not accurate but better than nothing when shapely is unavailable.
    
    Args:
        geometry: GeoJSON Geometry object
        
    Returns:
        Approximate area in square kilometers
    """
    geom_type = geometry.get('type')
    
    if geom_type == 'Polygon':
        coords = geometry['coordinates'][0]  # Outer ring
    elif geom_type == 'MultiPolygon':
        # Sum all polygon areas
        total_area = 0
        for polygon_coords in geometry['coordinates']:
            coords = polygon_coords[0]  # Outer ring of each polygon
            total_area += _shoelace_area(coords)
        return round(total_area, 4)
    else:
        return 0.0
    
    return round(_shoelace_area(coords), 4)


def _shoelace_area(coords: list) -> float:
    """Calculate area using Shoelace formula with lat/lon approximation.
    
    Args:
        coords: List of [lon, lat] coordinate pairs
        
    Returns:
        Area in square kilometers
    """
    if len(coords) < 3:
        return 0.0
    
    # Get average latitude for conversion factor
    avg_lat = sum(coord[1] for coord in coords) / len(coords)
    
    # Convert degrees to approximate meters at this latitude
    # 1 degree latitude ≈ 111 km
    # 1 degree longitude ≈ 111 km * cos(latitude)
    lat_to_km = 111.0
    lon_to_km = 111.0 * math.cos(math.radians(avg_lat))
    
    # Shoelace formula
    area = 0.0
    for i in range(len(coords) - 1):
        x1, y1 = coords[i][0] * lon_to_km, coords[i][1] * lat_to_km
        x2, y2 = coords[i + 1][0] * lon_to_km, coords[i + 1][1] * lat_to_km
        area += (x1 * y2) - (x2 * y1)
    
    return abs(area) / 2.0


def calculate_centroid(geometry: Dict[str, Any]) -> Tuple[float, float]:
    """Calculate the centroid (center point) of a polygon.
    
    Args:
        geometry: GeoJSON Geometry object
        
    Returns:
        Tuple of (latitude, longitude)
    """
    if SHAPELY_AVAILABLE:
        try:
            geom = shape(geometry)
            centroid = geom.centroid
            return (centroid.y, centroid.x)  # (lat, lon)
        except Exception:
            pass
    
    # Fallback: simple average of coordinates
    coords = []
    geom_type = geometry.get('type')
    
    if geom_type == 'Polygon':
        coords = geometry['coordinates'][0]
    elif geom_type == 'MultiPolygon':
        for polygon_coords in geometry['coordinates']:
            coords.extend(polygon_coords[0])
    
    if not coords:
        return (0.0, 0.0)
    
    avg_lat = sum(coord[1] for coord in coords) / len(coords)
    avg_lon = sum(coord[0] for coord in coords) / len(coords)
    
    return (avg_lat, avg_lon)


def simulate_fractional_exposure(
    geometry: Dict[str, Any],
    risk_type: str,
    scenario_params: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """Simulate fractional exposure of polygon to climate risk.
    
    This is a mock implementation that simulates what a real Google Earth Engine
    analysis would return: what percentage of the polygon is exposed to risk.
    
    In production, this would:
    - Query GEE for flood depth, sea level rise, or heat stress layers
    - Perform spatial intersection with the input polygon
    - Calculate the percentage of area exposed
    
    Args:
        geometry: GeoJSON Geometry object
        risk_type: Type of risk ('flood', 'coastal', 'heat', 'drought')
        scenario_params: Optional parameters like flood_depth_m, slr_m, etc.
        
    Returns:
        Dictionary with fractional_exposure_pct and related metadata
    """
    if scenario_params is None:
        scenario_params = {}
    
    # Get centroid for location-based variation
    lat, lon = calculate_centroid(geometry)
    
    # Calculate area for size-based variation
    area_sqkm = calculate_polygon_area_sqkm(geometry)
    
    # Mock fractional exposure based on location, risk type, and scenario
    # In reality, this would come from GEE spatial analysis
    
    # Create deterministic but varied exposure based on location
    location_seed = int((abs(lat) * 100 + abs(lon) * 100)) % 100
    
    # Base exposure varies by risk type
    risk_base_exposure = {
        'flood': 0.45,
        'coastal': 0.35,
        'heat': 0.60,
        'drought': 0.40,
        'agriculture': 0.50
    }
    
    base_exposure = risk_base_exposure.get(risk_type, 0.40)
    
    # Add location-based variation (-20% to +20%)
    location_factor = (location_seed / 100.0) * 0.4 - 0.2
    
    # Scenario intensity affects exposure
    intensity_factor = 0.0
    if 'flood_depth_m' in scenario_params:
        intensity_factor = min(scenario_params['flood_depth_m'] * 0.15, 0.3)
    elif 'slr_m' in scenario_params:
        intensity_factor = min(scenario_params['slr_m'] * 0.20, 0.3)
    elif 'temp_delta' in scenario_params:
        intensity_factor = min(scenario_params['temp_delta'] * 0.10, 0.25)
    
    # Larger areas tend to have more varied exposure
    size_factor = min(area_sqkm / 100.0, 0.1) * ((location_seed % 10) / 10.0 - 0.5)
    
    # Calculate final exposure percentage
    fractional_exposure = base_exposure + location_factor + intensity_factor + size_factor
    fractional_exposure = max(0.05, min(0.95, fractional_exposure))  # Clamp between 5% and 95%
    
    # Calculate exposed area
    exposed_area_sqkm = area_sqkm * fractional_exposure
    
    return {
        'fractional_exposure_pct': round(fractional_exposure * 100, 2),
        'total_area_sqkm': round(area_sqkm, 4),
        'exposed_area_sqkm': round(exposed_area_sqkm, 4),
        'risk_type': risk_type,
        'centroid': {'lat': round(lat, 6), 'lon': round(lon, 6)},
        'data_source': 'mock_gee_simulation',
        'note': 'This is a mock simulation. Production would use real GEE spatial intersection.'
    }


def calculate_scaled_risk(
    asset_value_usd: float,
    fractional_exposure_pct: float,
    damage_factor: float = 1.0
) -> Dict[str, float]:
    """Calculate financial risk scaled by fractional exposure.
    
    If only 34% of a polygon is exposed to flood risk, and the asset is worth $5M,
    the Value at Risk should be $5M * 0.34 * damage_factor.
    
    Args:
        asset_value_usd: Total asset value in USD
        fractional_exposure_pct: Percentage of polygon exposed (0-100)
        damage_factor: Expected damage ratio for exposed areas (0-1, default 1.0)
        
    Returns:
        Dictionary with value_at_risk, exposed_value, and protected_value
    """
    exposure_ratio = fractional_exposure_pct / 100.0
    
    exposed_value = asset_value_usd * exposure_ratio
    value_at_risk = exposed_value * damage_factor
    protected_value = asset_value_usd - exposed_value
    
    return {
        'total_asset_value_usd': round(asset_value_usd, 2),
        'exposed_value_usd': round(exposed_value, 2),
        'value_at_risk_usd': round(value_at_risk, 2),
        'protected_value_usd': round(protected_value, 2),
        'exposure_ratio': round(exposure_ratio, 4),
        'damage_factor': damage_factor
    }


def process_polygon_request(
    geojson: Dict[str, Any],
    risk_type: str,
    asset_value_usd: float = 5_000_000.0,
    scenario_params: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """Complete pipeline for processing a polygon risk analysis request.
    
    This is the main entry point for polygon-based Digital Twin analysis.
    
    Args:
        geojson: GeoJSON Feature or Geometry
        risk_type: Type of risk analysis
        asset_value_usd: Total asset value
        scenario_params: Scenario parameters (flood depth, SLR, etc.)
        
    Returns:
        Complete analysis dictionary
    """
    # Validate GeoJSON
    if not validate_geojson(geojson):
        raise ValueError("Invalid GeoJSON format")
    
    # Extract geometry
    geometry = extract_geometry(geojson)
    
    # Calculate spatial metrics
    exposure = simulate_fractional_exposure(geometry, risk_type, scenario_params)
    
    # Calculate financial risk
    financial_risk = calculate_scaled_risk(
        asset_value_usd=asset_value_usd,
        fractional_exposure_pct=exposure['fractional_exposure_pct'],
        damage_factor=scenario_params.get('damage_factor', 1.0) if scenario_params else 1.0
    )
    
    return {
        'spatial_analysis': exposure,
        'financial_risk': financial_risk,
        'geometry_type': geometry.get('type'),
        'analysis_type': 'polygon_digital_twin'
    }
