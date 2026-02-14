#!/usr/bin/env python3
"""Headless Runner for AdaptMetric Cloud Agents
=============================================

Runs climate impact calculations without starting a web server.
Accepts input via CLI arguments and outputs JSON to stdout.

Usage:
    python headless_runner.py --lat 40.7 --lon -74.0 --scenario_year 2050 --project_type agriculture

Arguments:
    --lat: Latitude coordinate (required)
    --lon: Longitude coordinate (required)
    --scenario_year: Future year for climate projections (required)
    --project_type: Type of project analysis (required)
                    Options: agriculture, coastal, flood, health

    Optional arguments (project-specific):
    --crop_type: Crop type for agriculture projects (default: maize)
                 Options: maize, cocoa, rice, soy, wheat
    --temp_delta: Temperature increase in degrees Celsius (default: 0.0)
    --rain_pct_change: Percentage change in rainfall (default: 0.0)
    --mangrove_width: Width of mangrove buffer in meters for coastal projects (default: 0.0)
    --slr_projection: Sea level rise projection in meters (default: 0.0)
    --rain_intensity: Rain intensity increase percentage for flood projects (default: 0.0)
    --workforce_size: Number of workers for health projects (default: 100)
    --daily_wage: Daily wage per worker in USD for health projects (default: 15.0)

Output:
    JSON object with calculation results printed to stdout
"""

import argparse
import json
import math
import sys
from datetime import datetime, timedelta

# Import calculation engines
from physics_engine import calculate_yield
from financial_engine import calculate_roi_metrics, calculate_npv, calculate_payback_period


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Headless runner for AdaptMetric climate impact calculations',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Required arguments
    parser.add_argument('--lat', type=float, required=True,
                        help='Latitude coordinate (-90 to 90)')
    parser.add_argument('--lon', type=float, required=True,
                        help='Longitude coordinate (-180 to 180)')
    parser.add_argument('--scenario_year', type=int, required=True,
                        help='Future year for climate projections (e.g., 2050)')
    parser.add_argument('--project_type', type=str, required=True,
                        choices=['agriculture', 'coastal', 'flood', 'health'],
                        help='Type of project analysis')

    # Optional arguments
    parser.add_argument('--crop_type', type=str, default='maize',
                        choices=['maize', 'cocoa', 'rice', 'soy', 'wheat'],
                        help='Crop type for agriculture projects (default: maize)')
    parser.add_argument('--temp_delta', type=float, default=0.0,
                        help='Temperature increase in degrees Celsius (default: 0.0)')
    parser.add_argument('--rain_pct_change', type=float, default=0.0,
                        help='Percentage change in rainfall (default: 0.0)')
    parser.add_argument('--mangrove_width', type=float, default=0.0,
                        help='Width of mangrove buffer in meters (default: 0.0)')
    parser.add_argument('--slr_projection', type=float, default=0.0,
                        help='Sea level rise projection in meters (default: 0.0)')
    parser.add_argument('--rain_intensity', type=float, default=0.0,
                        help='Rain intensity increase percentage (default: 0.0)')
    parser.add_argument('--workforce_size', type=int, default=100,
                        help='Number of workers for health projects (default: 100)')
    parser.add_argument('--daily_wage', type=float, default=15.0,
                        help='Daily wage per worker in USD (default: 15.0)')
    
    # Testing/mock data flag
    parser.add_argument('--use-mock-data', action='store_true',
                        help='Use mock data instead of Google Earth Engine (for testing)')
    
    return parser.parse_args()


def validate_coordinates(lat, lon):
    """Validate latitude and longitude ranges."""
    if not (-90 <= lat <= 90):
        raise ValueError(f'Latitude must be between -90 and 90, got {lat}')
    if not (-180 <= lon <= 180):
        raise ValueError(f'Longitude must be between -180 and 180, got {lon}')


def get_weather_data_fallback(lat, lon):
    """
    Get fallback weather data when GEE is unavailable.
    Uses simple climate zone approximation based on latitude.
    """
    # Approximate climate zones by latitude
    abs_lat = abs(lat)
    
    if abs_lat < 23.5:  # Tropical
        temp_c = 28.5
        rain_mm = 1800.0
    elif abs_lat < 35:  # Subtropical
        temp_c = 25.0
        rain_mm = 900.0
    elif abs_lat < 50:  # Temperate
        temp_c = 20.0
        rain_mm = 700.0
    else:  # Cold
        temp_c = 15.0
        rain_mm = 500.0
    
    return {
        'max_temp_celsius': temp_c,
        'total_precip_mm': rain_mm,
        'data_source': 'fallback_climate_zone'
    }


def run_agriculture_analysis(args, weather_data):
    """Run agriculture yield analysis."""
    temp_c = weather_data['max_temp_celsius']
    rain_mm = weather_data['total_precip_mm']
    
    # Define seed types
    SEED_TYPES = {
        'standard': 0,
        'resilient': 1
    }
    
    # Calculate yields for both seed types
    standard_yield = calculate_yield(
        temp=temp_c,
        rain=rain_mm,
        seed_type=SEED_TYPES['standard'],
        crop_type=args.crop_type,
        temp_delta=args.temp_delta,
        rain_pct_change=args.rain_pct_change
    )
    
    resilient_yield = calculate_yield(
        temp=temp_c,
        rain=rain_mm,
        seed_type=SEED_TYPES['resilient'],
        crop_type=args.crop_type,
        temp_delta=args.temp_delta,
        rain_pct_change=args.rain_pct_change
    )
    
    avoided_loss = resilient_yield - standard_yield
    percentage_improvement = (avoided_loss / standard_yield * 100) if standard_yield > 0 else 0.0
    
    # Calculate ROI (using research-based defaults)
    capex = 2000.0
    opex = 425.0
    yield_benefit_pct = 30.0

    # Approximate commodity prices (USD/ton) for comparative ROI.
    # These are coarse defaults and are NOT meant to be market-accurate.
    prices_per_ton = {
        'maize': 4800.0,
        'cocoa': 2500.0,
        'rice': 4000.0,
        'soy': 5000.0,
        'wheat': 3500.0,
    }
    price_per_ton = prices_per_ton.get(args.crop_type, 4000.0)

    analysis_years = 10
    discount_rate = 0.10
    
    # Generate cash flows
    incremental_cash_flows = []
    for year in range(analysis_years + 1):
        revenue_bau = standard_yield * price_per_ton
        yield_project = resilient_yield * (1 + (yield_benefit_pct / 100))
        revenue_project = yield_project * price_per_ton
        
        if year == 0:
            cost_project = capex
        else:
            cost_project = opex
        
        net_project = revenue_project - cost_project
        net_bau = revenue_bau
        incremental = net_project - net_bau
        
        if year == 0:
            incremental = -capex
        
        incremental_cash_flows.append(round(incremental, 2))
    
    npv = calculate_npv(incremental_cash_flows, discount_rate)
    payback_years = calculate_payback_period(incremental_cash_flows)
    
    return {
        'project_type': 'agriculture',
        'location': {'lat': args.lat, 'lon': args.lon},
        'scenario_year': args.scenario_year,
        'climate_conditions': {
            'temperature_c': round(temp_c, 2),
            'rainfall_mm': round(rain_mm, 2),
            'temp_delta': args.temp_delta,
            'rain_pct_change': args.rain_pct_change,
            'data_source': weather_data.get('data_source', 'unknown')
        },
        'crop_analysis': {
            'crop_type': args.crop_type,
            'standard_yield_pct': round(standard_yield, 2),
            'resilient_yield_pct': round(resilient_yield, 2),
            'avoided_loss_pct': round(avoided_loss, 2),
            'percentage_improvement': round(percentage_improvement, 2),
            'recommendation': 'resilient' if avoided_loss > 0 else 'standard'
        },
        'financial_analysis': {
            'npv_usd': round(npv, 2),
            'payback_years': round(payback_years, 2) if payback_years is not None else None,
            'incremental_cash_flows': incremental_cash_flows,
            'assumptions': {
                'capex': capex,
                'opex': opex,
                'yield_benefit_pct': yield_benefit_pct,
                'price_per_ton': price_per_ton,
                'discount_rate_pct': discount_rate * 100,
                'analysis_years': analysis_years
            }
        }
    }


def _coastal_flood_risk_fallback(lat: float, lon: float, slr_meters: float, surge_meters: float, mangrove_width_m: float) -> dict:
    """Offline/credential-free coastal flood risk approximation.

    This fallback avoids Google Earth Engine and provides deterministic, location-varying
    outputs suitable for batch/orchestration pipelines.
    """
    # Mangrove attenuation: simple exponential decay of surge height.
    # 200m ~ ~63% attenuation; 500m ~ ~92% attenuation.
    attenuation = math.exp(-max(0.0, mangrove_width_m) / 200.0) if surge_meters > 0 else 1.0
    effective_surge_m = surge_meters * attenuation

    total_water_level_m = slr_meters + effective_surge_m

    # Deterministic pseudo-elevation in [1, 5] meters (varies by location).
    seed = int((abs(lat) * 1000.0) + (abs(lon) * 1000.0)) % 1000
    elevation_m = 1.0 + (seed / 1000.0) * 4.0

    is_underwater = elevation_m < total_water_level_m
    flood_depth_m = max(0.0, total_water_level_m - elevation_m)

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
        'is_underwater': bool(is_underwater),
        'flood_depth_m': round(flood_depth_m, 2),
        'risk_category': risk_category,
        'data_source': 'fallback_parametric'
    }


def run_coastal_analysis(args, weather_data):
    """Run coastal flood risk analysis.

    Prefers Google Earth Engine-backed analysis when available; falls back to an offline
    approximation if GEE/credentials are missing.
    """
    # Set surge based on scenario
    include_surge = args.slr_projection > 0.5  # Include surge for significant SLR
    surge_m = 2.5 if include_surge else 0.0
    total_water_level = args.slr_projection + surge_m

    # Calculate flood risk
    try:
        from coastal_engine import analyze_flood_risk
        flood_risk = analyze_flood_risk(args.lat, args.lon, args.slr_projection, surge_m)
        flood_risk['data_source'] = flood_risk.get('data_source', 'google_earth_engine')
    except Exception as e:
        flood_risk = _coastal_flood_risk_fallback(
            lat=args.lat,
            lon=args.lon,
            slr_meters=args.slr_projection,
            surge_meters=surge_m,
            mangrove_width_m=args.mangrove_width
        )
        flood_risk['warning'] = f"GEE coastal analysis unavailable; used fallback: {e}"

    return {
        'project_type': 'coastal',
        'location': {'lat': args.lat, 'lon': args.lon},
        'scenario_year': args.scenario_year,
        'input_conditions': {
            'slr_projection_m': args.slr_projection,
            'include_surge': include_surge,
            'surge_m': surge_m,
            'total_water_level_m': total_water_level,
            'mangrove_width_m': args.mangrove_width
        },
        'flood_risk': flood_risk
    }


def _calculate_rainfall_frequency_fallback(intensity_increase_pct: float) -> dict:
    """Pure-python fallback for rainfall frequency curves (no GEE required)."""
    baseline_depths_mm = {
        '1yr': 70.0,
        '10yr': 121.5,
        '50yr': 159.7,
        '100yr': 179.4
    }

    rain_chart_data = []
    for period, baseline_mm in baseline_depths_mm.items():
        future_mm = baseline_mm * (1 + (intensity_increase_pct / 100.0))
        rain_chart_data.append({
            'period': period,
            'baseline_mm': round(baseline_mm, 2),
            'future_mm': round(future_mm, 2)
        })

    period_order = {'1yr': 1, '10yr': 2, '50yr': 3, '100yr': 4}
    rain_chart_data.sort(key=lambda x: period_order.get(x['period'], 999))

    return {'rain_chart_data': rain_chart_data}


def _flash_flood_fallback(lat: float, lon: float, rain_intensity_increase_pct: float) -> dict:
    """Offline flash-flood risk approximation.

    Returns a simple scaling of flood-prone area with rainfall intensity increase.
    """
    # Deterministic baseline area varies modestly by location.
    seed = int((abs(lat) * 100.0) + (abs(lon) * 10.0)) % 100
    baseline_area_km2 = 50.0 + seed  # 50-149 km^2

    scale = 1.0 + max(0.0, rain_intensity_increase_pct) * 0.02  # +2% area per +1% intensity
    future_area_km2 = baseline_area_km2 * scale

    if baseline_area_km2 > 0:
        risk_increase_pct = ((future_area_km2 - baseline_area_km2) / baseline_area_km2) * 100.0
    else:
        risk_increase_pct = 0.0

    return {
        'baseline_flood_area_km2': round(baseline_area_km2, 2),
        'future_flood_area_km2': round(future_area_km2, 2),
        'risk_increase_pct': round(risk_increase_pct, 2),
        'data_source': 'fallback_parametric'
    }


def run_flood_analysis(args, weather_data):
    """Run flash flood risk analysis.

    Prefers Google Earth Engine-backed analysis when available; falls back to an offline
    approximation if GEE/credentials are missing.
    """
    try:
        from flood_engine import analyze_flash_flood, calculate_rainfall_frequency
        flash_flood_analysis = analyze_flash_flood(args.lat, args.lon, args.rain_intensity)
        rainfall_frequency = calculate_rainfall_frequency(args.rain_intensity)
        flash_flood_analysis['data_source'] = flash_flood_analysis.get('data_source', 'google_earth_engine')
    except Exception as e:
        flash_flood_analysis = _flash_flood_fallback(args.lat, args.lon, args.rain_intensity)
        flash_flood_analysis['warning'] = f"GEE flood analysis unavailable; used fallback: {e}"
        rainfall_frequency = _calculate_rainfall_frequency_fallback(args.rain_intensity)

    return {
        'project_type': 'flood',
        'location': {'lat': args.lat, 'lon': args.lon},
        'scenario_year': args.scenario_year,
        'input_conditions': {
            'rain_intensity_increase_pct': args.rain_intensity
        },
        'flash_flood_analysis': flash_flood_analysis,
        'rainfall_frequency': rainfall_frequency
    }


def run_health_analysis(args, weather_data):
    """Run climate health impact analysis."""
    # Import health engine
    try:
        from health_engine import calculate_productivity_loss, calculate_malaria_risk, calculate_health_economic_impact
    except ImportError:
        return {
            'project_type': 'health',
            'error': 'Health engine not available',
            'message': 'health_engine.py module not found'
        }
    
    temp_c = weather_data['max_temp_celsius']
    precip_mm = weather_data['total_precip_mm']
    
    # Estimate humidity from precipitation
    if precip_mm < 500:
        humidity_pct = 50.0
    elif precip_mm < 1000:
        humidity_pct = 65.0
    else:
        humidity_pct = 80.0
    
    try:
        productivity_loss = calculate_productivity_loss(temp_c, humidity_pct)
        malaria_risk = calculate_malaria_risk(temp_c, precip_mm)
        economic_impact = calculate_health_economic_impact(
            workforce_size=args.workforce_size,
            daily_wage=args.daily_wage,
            productivity_loss_pct=productivity_loss['productivity_loss_pct'],
            malaria_risk_score=malaria_risk['risk_score']
        )
        
        return {
            'project_type': 'health',
            'location': {'lat': args.lat, 'lon': args.lon},
            'scenario_year': args.scenario_year,
            'climate_conditions': {
                'temperature_c': round(temp_c, 2),
                'precipitation_mm': round(precip_mm, 2),
                'estimated_humidity_pct': humidity_pct,
                'data_source': weather_data.get('data_source', 'unknown')
            },
            'workforce_parameters': {
                'workforce_size': args.workforce_size,
                'daily_wage_usd': args.daily_wage
            },
            'productivity_analysis': productivity_loss,
            'malaria_risk': malaria_risk,
            'economic_impact': economic_impact
        }
    except Exception as e:
        return {
            'project_type': 'health',
            'error': 'Analysis failed',
            'message': str(e)
        }


def main():
    """Main execution function."""
    try:
        # Parse arguments
        args = parse_arguments()
        
        # Validate coordinates
        validate_coordinates(args.lat, args.lon)
        
        # Get weather data based on mode
        if args.use_mock_data:
            # Use mock data for testing (bypasses GEE completely)
            from mock_data import get_mock_weather
            weather_data = get_mock_weather(args.lat, args.lon)
            print(f"Info: Using mock data for testing", file=sys.stderr)
        else:
            # Try to get weather data from GEE, fallback to approximation
            try:
                from gee_connector import get_weather_data
                
                end_date = datetime.now()
                start_date = end_date - timedelta(days=365)
                
                weather_data = get_weather_data(
                    lat=args.lat,
                    lon=args.lon,
                    start_date=start_date.strftime('%Y-%m-%d'),
                    end_date=end_date.strftime('%Y-%m-%d')
                )
                weather_data['data_source'] = 'google_earth_engine'
            except Exception as gee_error:
                print(f"Warning: GEE unavailable, using fallback data: {gee_error}", file=sys.stderr)
                weather_data = get_weather_data_fallback(args.lat, args.lon)
        
        # Route to appropriate analysis based on project type
        if args.project_type == 'agriculture':
            result = run_agriculture_analysis(args, weather_data)
        elif args.project_type == 'coastal':
            result = run_coastal_analysis(args, weather_data)
        elif args.project_type == 'flood':
            result = run_flood_analysis(args, weather_data)
        elif args.project_type == 'health':
            result = run_health_analysis(args, weather_data)
        else:
            result = {
                'error': 'Invalid project type',
                'message': f'Unknown project_type: {args.project_type}'
            }
        
        # Add metadata
        result['execution_timestamp'] = datetime.now().isoformat()
        result['success'] = 'error' not in result
        
        # Output JSON to stdout
        print(json.dumps(result, indent=2))
        
        # Exit with appropriate code
        sys.exit(0 if result['success'] else 1)
        
    except Exception as e:
        # Handle any unexpected errors
        error_result = {
            'success': False,
            'error': 'Execution failed',
            'message': str(e),
            'execution_timestamp': datetime.now().isoformat()
        }
        print(json.dumps(error_result, indent=2))
        sys.exit(1)


if __name__ == '__main__':
    main()
