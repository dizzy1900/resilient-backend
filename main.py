"""
Climate Resilience Engine - Flask API
"""

import os
import pickle
import threading
from datetime import datetime, timedelta
from functools import wraps

import ee
import pandas as pd
from flask import Flask, request, jsonify
from flask_cors import CORS

from gee_connector import get_weather_data, get_coastal_params, get_monthly_data, analyze_spatial_viability
from batch_processor import run_batch_job
from physics_engine import simulate_maize_yield, calculate_yield
from coastal_engine import analyze_flood_risk, analyze_urban_impact
from flood_engine import analyze_flash_flood, calculate_rainfall_frequency, analyze_infrastructure_risk
from financial_engine import calculate_roi_metrics, calculate_npv, calculate_payback_period

app = Flask(__name__)
# Enable CORS for all origins (Lovable uses multiple domains)
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "expose_headers": ["Content-Type"],
        "supports_credentials": False
    }
})

# Model configuration
MODEL_PATH = 'ag_surrogate.pkl'
COASTAL_MODEL_PATH = 'coastal_surrogate.pkl'
FLOOD_MODEL_PATH = 'flood_surrogate.pkl'
model = None
coastal_model = None
flood_model = None

# Load models at startup (start.sh ensures the files exist)
try:
    with open(MODEL_PATH, 'rb') as f:
        model = pickle.load(f)
    print(f"Model loaded successfully from {MODEL_PATH}")
except FileNotFoundError:
    print(f"Warning: Model file '{MODEL_PATH}' not found. Run start.sh or download manually.")
except Exception as e:
    print(f"Warning: Failed to load model: {e}")

try:
    with open(COASTAL_MODEL_PATH, 'rb') as f:
        coastal_model = pickle.load(f)
    print(f"Coastal model loaded successfully from {COASTAL_MODEL_PATH}")
except FileNotFoundError:
    print(f"Warning: Coastal model file '{COASTAL_MODEL_PATH}' not found.")
except Exception as e:
    print(f"Warning: Failed to load coastal model: {e}")

try:
    with open(FLOOD_MODEL_PATH, 'rb') as f:
        flood_model = pickle.load(f)
    print(f"Flood model loaded successfully from {FLOOD_MODEL_PATH}")
except FileNotFoundError:
    print(f"Warning: Flood model file '{FLOOD_MODEL_PATH}' not found.")
except Exception as e:
    print(f"Warning: Failed to load flood model: {e}")

SEED_TYPES = {
    'standard': 0,
    'resilient': 1
}

FALLBACK_WEATHER = {
    'max_temp_celsius': 28.5,
    'total_rain_mm': 520.0,
    'period': 'last_12_months'
}


def validate_json(*required_fields):
    """Decorator to validate required JSON fields."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not request.is_json:
                return jsonify({
                    'status': 'error',
                    'message': 'Request must be JSON',
                    'code': 'INVALID_CONTENT_TYPE'
                }), 400
            
            data = request.get_json()
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                return jsonify({
                    'status': 'error',
                    'message': f'Missing required fields: {", ".join(missing_fields)}',
                    'code': 'MISSING_FIELDS'
                }), 400
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


@app.route('/')
def index():
    return jsonify({'status': 'active'})


@app.route('/get-hazard', methods=['POST'])
@validate_json('lat', 'lon')
def get_hazard():
    """Get climate hazard data for a location using GEE."""
    try:
        data = request.get_json()
        lat = float(data['lat'])
        lon = float(data['lon'])
        
        if not (-90 <= lat <= 90):
            return jsonify({
                'status': 'error',
                'message': 'Latitude must be between -90 and 90',
                'code': 'INVALID_LATITUDE'
            }), 400
        
        if not (-180 <= lon <= 180):
            return jsonify({
                'status': 'error',
                'message': 'Longitude must be between -180 and 180',
                'code': 'INVALID_LONGITUDE'
            }), 400
        
        # Calculate date range for last 12 months
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        
        try:
            weather_data = get_weather_data(
                lat=lat,
                lon=lon,
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d')
            )
            
            hazard_metrics = {
                'max_temp_celsius': weather_data['max_temp_celsius'],
                'total_rain_mm': weather_data['total_precip_mm'],
                'period': 'growing_season_peak'
            }
        except Exception as gee_error:
            import sys
            print(f"GEE error, using fallback: {gee_error}", file=sys.stderr, flush=True)
            hazard_metrics = FALLBACK_WEATHER.copy()
        
        return jsonify({
            'status': 'success',
            'data': {
                'location': {
                    'lat': lat,
                    'lon': lon
                },
                'hazard_metrics': hazard_metrics
            }
        }), 200
        
    except ValueError:
        return jsonify({
            'status': 'error',
            'message': 'Invalid numeric values for lat/lon',
            'code': 'INVALID_NUMERIC_VALUE'
        }), 400


@app.route('/predict', methods=['POST'])
def predict():
    """Predict crop yield and calculate avoided loss.
    
    Supports two modes:
    - Mode A (Auto-Lookup): Provide lat/lon to fetch weather data from GEE
    - Mode B (Manual): Provide temp/rain directly
    """
    if not request.is_json:
        return jsonify({
            'status': 'error',
            'message': 'Request must be JSON',
            'code': 'INVALID_CONTENT_TYPE'
        }), 400
    
    try:
        data = request.get_json()
        
        # Get crop type (default to 'maize' for backwards compatibility)
        crop_type = data.get('crop_type', 'maize').lower()
        
        # Validate crop type
        if crop_type not in ['maize', 'cocoa']:
            return jsonify({
                'status': 'error',
                'message': f"Unsupported crop_type: {crop_type}. Supported crops: 'maize', 'cocoa'",
                'code': 'INVALID_CROP_TYPE'
            }), 400
        
        # Mode A: Auto-Lookup using lat/lon (Priority)
        if 'lat' in data and 'lon' in data:
            lat = float(data['lat'])
            lon = float(data['lon'])
            
            # Validate coordinates
            if not (-90 <= lat <= 90):
                return jsonify({
                    'status': 'error',
                    'message': 'Latitude must be between -90 and 90',
                    'code': 'INVALID_LATITUDE'
                }), 400
            
            if not (-180 <= lon <= 180):
                return jsonify({
                    'status': 'error',
                    'message': 'Longitude must be between -180 and 180',
                    'code': 'INVALID_LONGITUDE'
                }), 400
            
            # Fetch weather data from Google Earth Engine
            try:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=365)
                
                weather_data = get_weather_data(
                    lat=lat,
                    lon=lon,
                    start_date=start_date.strftime('%Y-%m-%d'),
                    end_date=end_date.strftime('%Y-%m-%d')
                )
                
                base_temp = weather_data['max_temp_celsius']
                base_rain = weather_data['total_precip_mm']
                data_source = 'gee_auto_lookup'
                
                # Fetch monthly data for charts
                try:
                    monthly_data = get_monthly_data(lat, lon)
                except Exception as monthly_error:
                    import sys
                    print(f"Monthly data error: {monthly_error}", file=sys.stderr, flush=True)
                    monthly_data = None
                
                # Store lat/lon for spatial analysis later
                has_location = True
                location_lat = lat
                location_lon = lon
                
            except Exception as gee_error:
                import sys
                print(f"GEE error, using fallback: {gee_error}", file=sys.stderr, flush=True)
                
                # Use fallback weather data
                base_temp = FALLBACK_WEATHER['max_temp_celsius']
                base_rain = FALLBACK_WEATHER['total_rain_mm']
                data_source = 'fallback'
                monthly_data = None
                has_location = False
        
        # Mode B: Manual fallback using temp/rain
        elif 'temp' in data and 'rain' in data:
            base_temp = float(data['temp'])
            base_rain = float(data['rain'])
            data_source = 'manual'
            monthly_data = None
            has_location = False
        
        else:
            return jsonify({
                'status': 'error',
                'message': 'Missing required fields: provide either (lat, lon) or (temp, rain)',
                'code': 'MISSING_FIELDS'
            }), 400
        
        # Climate perturbation parameters (optional)
        # Delta Method: temp uses additive, rain uses percentage scaling
        temp_increase = float(data.get('temp_increase', 0.0))
        rain_change = float(data.get('rain_change', 0.0))
        
        # Calculate final simulated values for debug output
        # These are the exact values passed to the physics engine
        final_simulated_temp = base_temp + temp_increase
        rain_modifier = 1.0 + (rain_change / 100.0)
        final_simulated_rain = max(0.0, base_rain * rain_modifier)
        
        # Run predictions using physics engine with climate perturbation
        standard_yield = calculate_yield(
            temp=base_temp,
            rain=base_rain,
            seed_type=SEED_TYPES['standard'],
            crop_type=crop_type,
            temp_delta=temp_increase,
            rain_pct_change=rain_change
        )
        
        resilient_yield = calculate_yield(
            temp=base_temp,
            rain=base_rain,
            seed_type=SEED_TYPES['resilient'],
            crop_type=crop_type,
            temp_delta=temp_increase,
            rain_pct_change=rain_change
        )
        
        avoided_loss = resilient_yield - standard_yield
        
        if standard_yield > 0:
            percentage_improvement = (avoided_loss / standard_yield) * 100
        else:
            percentage_improvement = 0.0
        
        # Financial ROI Analysis (optional)
        # Get project parameters with research-based defaults
        project_params = data.get('project_params', {})
        capex = float(project_params.get('capex', 2000))
        opex = float(project_params.get('opex', 425))
        yield_benefit_pct = float(project_params.get('yield_benefit_pct', 30.0))
        price_per_ton = float(project_params.get('price_per_ton', 4800))
        analysis_years = 10
        discount_rate = 0.10  # 10% discount rate
        
        # Calculate Agricultural ROI
        # Baseline (Business as Usual): Standard seed, no project
        predicted_yield_tons = standard_yield
        
        # Generate 10-year cash flows
        incremental_cash_flows = []
        cumulative_cash_flow_array = []
        cumulative = 0.0
        
        for year in range(analysis_years + 1):  # 0 to 10 (11 years)
            # Baseline revenue (doing nothing - standard seed)
            revenue_bau = predicted_yield_tons * price_per_ton
            net_bau = revenue_bau  # No extra cost for BAU
            
            # Project revenue (resilient seed with yield benefit)
            yield_project = resilient_yield * (1 + (yield_benefit_pct / 100))
            revenue_project = yield_project * price_per_ton
            
            # Project costs
            if year == 0:
                # Year 0: CAPEX initial investment
                cost_project = capex
            else:
                # Year 1+: OPEX annual maintenance
                cost_project = opex
            
            # Net project cash flow
            net_project = revenue_project - cost_project
            
            # Incremental cash flow (delta)
            incremental = net_project - net_bau
            
            # Year 0 is pure CAPEX (negative), no revenue yet
            if year == 0:
                incremental = -capex
            
            incremental_cash_flows.append(round(incremental, 2))
            
            # Cumulative cash flow
            cumulative += incremental
            cumulative_cash_flow_array.append(round(cumulative, 2))
        
        # Calculate NPV using financial engine
        npv = calculate_npv(incremental_cash_flows, discount_rate)
        
        # Calculate payback period
        payback_years = calculate_payback_period(incremental_cash_flows)
        
        roi_analysis = {
            'npv': round(npv, 2),
            'payback_years': round(payback_years, 2) if payback_years is not None else None,
            'cumulative_cash_flow': cumulative_cash_flow_array,
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
        
        # Run spatial analysis if location data is available
        # This analyzes cropland viability in a 50km buffer around the location
        spatial_analysis = None
        if has_location and temp_increase != 0.0:
            try:
                import sys
                print(f"[SPATIAL] Running spatial analysis for lat={location_lat}, lon={location_lon}, temp_increase={temp_increase}", file=sys.stderr, flush=True)
                spatial_analysis = analyze_spatial_viability(location_lat, location_lon, temp_increase)
                print(f"[SPATIAL] Complete: {spatial_analysis}", file=sys.stderr, flush=True)
            except Exception as spatial_error:
                import sys
                print(f"Spatial analysis error: {spatial_error}", file=sys.stderr, flush=True)
                spatial_analysis = None
        
        # Build chart_data if monthly data is available
        chart_data = None
        if monthly_data is not None:
            months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            rainfall_baseline = monthly_data['rainfall_monthly_mm']
            soil_moisture_baseline = monthly_data['soil_moisture_monthly']
            
            # Apply rainfall projection logic with summer drought penalty
            rainfall_projected = []
            for i, baseline_value in enumerate(rainfall_baseline):
                month_index = i  # 0 = Jan, 5 = Jun, 6 = Jul, 7 = Aug
                
                # Base projection: apply rain_change percentage
                projected_value = baseline_value * (1 + rain_change / 100)
                
                # Advanced: If drought (negative rain_change), apply double penalty to summer months
                if rain_change < 0:
                    # Summer months: June (5), July (6), August (7)
                    if month_index in [5, 6, 7]:
                        # Apply double penalty: compound the negative change
                        additional_penalty = abs(rain_change) / 100
                        projected_value = projected_value * (1 - additional_penalty)
                
                rainfall_projected.append(round(projected_value, 2))
            
            chart_data = {
                'months': months,
                'rainfall_baseline': [round(v, 2) for v in rainfall_baseline],
                'rainfall_projected': rainfall_projected,
                'soil_moisture_baseline': [round(v, 4) for v in soil_moisture_baseline]
            }
        
        response_data = {
            'input_conditions': {
                'max_temp_celsius': base_temp,
                'total_rain_mm': base_rain,
                'data_source': data_source,
                'crop_type': crop_type
            },
            'predictions': {
                'standard_seed': {
                    'type_code': SEED_TYPES['standard'],
                    'predicted_yield': round(standard_yield, 2)
                },
                'resilient_seed': {
                    'type_code': SEED_TYPES['resilient'],
                    'predicted_yield': round(resilient_yield, 2)
                }
            },
            'analysis': {
                'avoided_loss': round(avoided_loss, 2),
                'percentage_improvement': round(percentage_improvement, 2),
                'recommendation': 'resilient' if avoided_loss > 0 else 'standard'
            },
            'simulation_debug': {
                'raw_temp': round(base_temp, 2),
                'perturbation_added': round(temp_increase, 2),
                'final_simulated_temp': round(final_simulated_temp, 2),
                'raw_rain': round(base_rain, 2),
                'rain_modifier': round(rain_change, 2),
                'final_simulated_rain': round(final_simulated_rain, 2)
            }
        }
        
        # Add chart_data if available
        if chart_data is not None:
            response_data['chart_data'] = chart_data
        
        # Add spatial_analysis if available
        if spatial_analysis is not None:
            response_data['spatial_analysis'] = spatial_analysis
        
        # Add roi_analysis (always included)
        if roi_analysis is not None:
            response_data['roi_analysis'] = roi_analysis
        
        return jsonify({
            'status': 'success',
            'data': response_data
        }), 200
        
    except ValueError:
        return jsonify({
            'status': 'error',
            'message': 'Invalid numeric values for temp/rain',
            'code': 'INVALID_NUMERIC_VALUE'
        }), 400
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Prediction failed: {str(e)}',
            'code': 'PREDICTION_ERROR'
        }), 500


@app.route('/predict-coastal', methods=['POST'])
@validate_json('lat', 'lon', 'mangrove_width')
def predict_coastal():
    """Predict coastal runup elevation with and without mangrove protection."""
    if coastal_model is None:
        return jsonify({
            'status': 'error',
            'message': 'Coastal model file not found. Ensure coastal_surrogate.pkl exists.',
            'code': 'MODEL_NOT_FOUND'
        }), 500

    try:
        data = request.get_json()
        lat = float(data['lat'])
        lon = float(data['lon'])
        mangrove_width = float(data['mangrove_width'])
        
        # Log the request for debugging (remove in production)
        import sys
        print(f"[COASTAL REQUEST] lat={lat}, lon={lon}, mangrove_width={mangrove_width}", file=sys.stderr, flush=True)
        
        # Handle minimum effective width - model shows negligible effect below 10m
        if mangrove_width > 0 and mangrove_width < 10:
            print(f"[WARNING] Mangrove width {mangrove_width}m is below minimum effective width. Using 10m minimum.", file=sys.stderr, flush=True)
            mangrove_width = 10  # Set to minimum effective width

        if not (-90 <= lat <= 90):
            return jsonify({
                'status': 'error',
                'message': 'Latitude must be between -90 and 90',
                'code': 'INVALID_LATITUDE'
            }), 400

        if not (-180 <= lon <= 180):
            return jsonify({
                'status': 'error',
                'message': 'Longitude must be between -180 and 180',
                'code': 'INVALID_LONGITUDE'
            }), 400

        # Step A: Fetch coastal parameters from Google Earth Engine
        coastal_data = get_coastal_params(lat, lon)
        slope = coastal_data['slope_pct']
        wave_height = coastal_data['max_wave_height']

        # Step B: Run predictions for both scenarios
        # Scenario A (Gray): No mangrove protection (mangrove_width = 0)
        scenario_a_df = pd.DataFrame({
            'wave_height': [wave_height],
            'slope': [slope],
            'mangrove_width_m': [0.0]
        })

        # Scenario B (Green): With mangrove protection (user's mangrove_width)
        scenario_b_df = pd.DataFrame({
            'wave_height': [wave_height],
            'slope': [slope],
            'mangrove_width_m': [mangrove_width]
        })

        runup_a = float(coastal_model.predict(scenario_a_df)[0])
        runup_b = float(coastal_model.predict(scenario_b_df)[0])
        
        # Calculate avoided runup (in meters)
        avoided_runup = runup_a - runup_b
        
        # Convert avoided runup to economic value
        # Using standard coastal property damage estimates:
        # - Typical coastal property value: $500,000 per meter of frontage
        # - Average lot depth: 30 meters
        # - Flood damage: $1,000 per square meter per meter of flooding
        # - Formula: avoided_damage = avoided_runup * property_frontage * damage_per_sqm
        
        # Conservative estimate: $10,000 per meter of avoided runup per property
        # This accounts for structural damage, contents, cleanup, and business interruption
        DAMAGE_COST_PER_METER = 10000  # USD per meter of runup per affected property
        
        # Assume analysis covers 100 properties (typical coastal community project scale)
        NUM_PROPERTIES = 100
        
        avoided_damage_usd = avoided_runup * DAMAGE_COST_PER_METER * NUM_PROPERTIES
        
        # Calculate percentage improvement
        percentage_improvement = (avoided_runup / runup_a * 100) if runup_a > 0 else 0

        return jsonify({
            'status': 'success',
            'data': {
                'input_conditions': {
                    'lat': lat,
                    'lon': lon,
                    'mangrove_width_m': mangrove_width
                },
                'coastal_params': {
                    'detected_slope_pct': round(slope, 2),
                    'storm_wave_height': round(wave_height, 2)
                },
                'predictions': {
                    'baseline_runup': round(runup_a, 4),
                    'protected_runup': round(runup_b, 4)
                },
                'analysis': {
                    'avoided_loss': round(avoided_damage_usd, 2),
                    'avoided_runup_m': round(avoided_runup, 4),
                    'percentage_improvement': round(percentage_improvement, 2),
                    'recommendation': 'with_mangroves' if avoided_runup > 0 else 'baseline'
                },
                'economic_assumptions': {
                    'damage_cost_per_meter': DAMAGE_COST_PER_METER,
                    'num_properties': NUM_PROPERTIES,
                    'total_value_basis': 'USD per meter of flood reduction × properties affected'
                },
                # Add flat fields for frontend compatibility
                'slope': round(slope / 100, 4),  # Convert percentage to decimal (e.g., 14.12% -> 0.1412)
                'storm_wave': round(wave_height, 2),
                'avoided_loss': round(avoided_damage_usd, 2)
            }
        }), 200

    except ValueError:
        return jsonify({
            'status': 'error',
            'message': 'Invalid numeric values for lat/lon/mangrove_width',
            'code': 'INVALID_NUMERIC_VALUE'
        }), 400
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Prediction failed: {str(e)}',
            'code': 'PREDICTION_ERROR'
        }), 500


@app.route('/predict-coastal-flood', methods=['POST'])
@validate_json('lat', 'lon', 'slr_projection')
def predict_coastal_flood():
    """Predict coastal flood risk based on sea level rise and storm surge."""
    try:
        data = request.get_json()
        lat = float(data['lat'])
        lon = float(data['lon'])
        slr_projection = float(data['slr_projection'])
        include_surge = data.get('include_surge', False)
        
        # Log the request for debugging
        import sys
        print(f"[COASTAL FLOOD REQUEST] lat={lat}, lon={lon}, slr_projection={slr_projection}, include_surge={include_surge}", file=sys.stderr, flush=True)
        
        # Validate coordinates
        if not (-90 <= lat <= 90):
            return jsonify({
                'status': 'error',
                'message': 'Latitude must be between -90 and 90',
                'code': 'INVALID_LATITUDE'
            }), 400
        
        if not (-180 <= lon <= 180):
            return jsonify({
                'status': 'error',
                'message': 'Longitude must be between -180 and 180',
                'code': 'INVALID_LONGITUDE'
            }), 400
        
        if slr_projection < 0:
            return jsonify({
                'status': 'error',
                'message': 'Sea level rise projection must be non-negative',
                'code': 'INVALID_SLR_PROJECTION'
            }), 400
        
        # Set surge based on include_surge flag
        surge_m = 2.5 if include_surge else 0.0
        
        # Calculate total water level
        total_water_level = slr_projection + surge_m
        
        # Call coastal engine to analyze flood risk
        flood_risk = analyze_flood_risk(lat, lon, slr_projection, surge_m)
        
        # Call coastal engine to analyze urban impact (spatial analysis)
        # This may take 2-3 seconds due to GEE processing
        spatial_analysis = None
        try:
            import sys
            print(f"[SPATIAL] Running urban impact analysis for lat={lat}, lon={lon}, water_level={total_water_level}m", file=sys.stderr, flush=True)
            spatial_analysis = analyze_urban_impact(lat, lon, total_water_level)
            print(f"[SPATIAL] Complete: {spatial_analysis}", file=sys.stderr, flush=True)
        except Exception as spatial_error:
            import sys
            print(f"Spatial analysis error: {spatial_error}", file=sys.stderr, flush=True)
            spatial_analysis = None
        
        # Build response data
        response_data = {
            'input_conditions': {
                'lat': lat,
                'lon': lon,
                'slr_projection_m': slr_projection,
                'include_surge': include_surge,
                'surge_m': surge_m,
                'total_water_level_m': total_water_level
            },
            'flood_risk': flood_risk
        }
        
        # Add spatial_analysis if available
        if spatial_analysis is not None:
            response_data['spatial_analysis'] = spatial_analysis
        
        # Infrastructure ROI Analysis (optional)
        infrastructure_roi = None
        if 'infrastructure_params' in data and 'intervention_params' in data:
            try:
                from infrastructure_engine import calculate_infrastructure_roi
                
                infra_params = data['infrastructure_params']
                intervention_params = data['intervention_params']
                
                # Get parameters with validation
                asset_value = float(infra_params.get('asset_value', 0))
                daily_revenue = float(infra_params.get('daily_revenue', 0))
                
                capex = float(intervention_params.get('capex', 0))
                opex = float(intervention_params.get('opex', 0))
                intervention_type = intervention_params.get('type', 'sea_wall')
                
                # Use flood depth from flood_risk analysis
                flood_depth = flood_risk.get('flood_depth_m', 0.0)
                
                # Only calculate if we have valid inputs and flooding exists
                if asset_value > 0 and flood_depth > 0:
                    import sys
                    print(f"[INFRASTRUCTURE ROI] Calculating for flood_depth={flood_depth}m, asset_value=${asset_value}, intervention={intervention_type}", file=sys.stderr, flush=True)
                    
                    infrastructure_roi = calculate_infrastructure_roi(
                        flood_depth_m=flood_depth,
                        asset_value=asset_value,
                        daily_revenue=daily_revenue,
                        project_capex=capex,
                        project_opex=opex,
                        intervention_type=intervention_type,
                        analysis_years=20,
                        discount_rate=0.10,
                        wall_height_m=intervention_params.get('wall_height_m', 2.0),
                        drainage_reduction_m=intervention_params.get('drainage_reduction_m', 0.3)
                    )
                    
                    print(f"[INFRASTRUCTURE ROI] Complete: NPV=${infrastructure_roi['financial_analysis']['npv']:,.0f}, BCR={infrastructure_roi['financial_analysis']['bcr']:.2f}", file=sys.stderr, flush=True)
                    
            except Exception as roi_error:
                import sys
                print(f"Infrastructure ROI error: {roi_error}", file=sys.stderr, flush=True)
                infrastructure_roi = None
        
        # Add infrastructure_roi if available
        if infrastructure_roi is not None:
            response_data['infrastructure_roi'] = infrastructure_roi
        
        return jsonify({
            'status': 'success',
            'data': response_data
        }), 200
    
    except ValueError:
        return jsonify({
            'status': 'error',
            'message': 'Invalid numeric values for lat/lon/slr_projection',
            'code': 'INVALID_NUMERIC_VALUE'
        }), 400
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Flood risk analysis failed: {str(e)}',
            'code': 'FLOOD_RISK_ERROR'
        }), 500


@app.route('/predict-flash-flood', methods=['POST'])
@validate_json('lat', 'lon', 'rain_intensity_pct')
def predict_flash_flood():
    """Predict flash flood risk using Topographic Wetness Index (TWI) model."""
    try:
        data = request.get_json()
        lat = float(data['lat'])
        lon = float(data['lon'])
        rain_intensity_pct = float(data['rain_intensity_pct'])
        
        # Log the request for debugging
        import sys
        print(f"[FLASH FLOOD REQUEST] lat={lat}, lon={lon}, rain_intensity_pct={rain_intensity_pct}", file=sys.stderr, flush=True)
        
        # Validate coordinates
        if not (-90 <= lat <= 90):
            return jsonify({
                'status': 'error',
                'message': 'Latitude must be between -90 and 90',
                'code': 'INVALID_LATITUDE'
            }), 400
        
        if not (-180 <= lon <= 180):
            return jsonify({
                'status': 'error',
                'message': 'Longitude must be between -180 and 180',
                'code': 'INVALID_LONGITUDE'
            }), 400
        
        if rain_intensity_pct < 0:
            return jsonify({
                'status': 'error',
                'message': 'Rain intensity increase must be non-negative',
                'code': 'INVALID_RAIN_INTENSITY'
            }), 400
        
        # Call flash flood engine to analyze TWI-based flood risk
        flash_flood_analysis = analyze_flash_flood(lat, lon, rain_intensity_pct)
        
        # Call rainfall frequency analytics
        rainfall_frequency = calculate_rainfall_frequency(rain_intensity_pct)
        
        # Call infrastructure risk analysis (spatial analysis)
        # This may take 2-3 seconds due to GEE processing
        spatial_analysis = None
        try:
            import sys
            print(f"[SPATIAL] Running infrastructure risk analysis for lat={lat}, lon={lon}, rain_intensity={rain_intensity_pct}%", file=sys.stderr, flush=True)
            spatial_analysis = analyze_infrastructure_risk(lat, lon, rain_intensity_pct)
            print(f"[SPATIAL] Complete: {spatial_analysis}", file=sys.stderr, flush=True)
        except Exception as spatial_error:
            import sys
            print(f"Infrastructure risk analysis error: {spatial_error}", file=sys.stderr, flush=True)
            spatial_analysis = None
        
        # Build response data
        response_data = {
            'input_conditions': {
                'lat': lat,
                'lon': lon,
                'rain_intensity_increase_pct': rain_intensity_pct
            },
            'flash_flood_analysis': flash_flood_analysis,
            'analytics': rainfall_frequency
        }
        
        # Add spatial_analysis if available
        if spatial_analysis is not None:
            response_data['spatial_analysis'] = spatial_analysis
        
        # Infrastructure ROI Analysis (optional)
        infrastructure_roi = None
        if 'infrastructure_params' in data and 'intervention_params' in data:
            try:
                from infrastructure_engine import calculate_infrastructure_roi
                
                infra_params = data['infrastructure_params']
                intervention_params = data['intervention_params']
                
                # Get parameters with validation
                asset_value = float(infra_params.get('asset_value', 0))
                daily_revenue = float(infra_params.get('daily_revenue', 0))
                
                capex = float(intervention_params.get('capex', 0))
                opex = float(intervention_params.get('opex', 0))
                intervention_type = intervention_params.get('type', 'drainage')  # Default drainage for flash floods
                
                # Estimate flood depth from flash flood analysis
                # Use a simple heuristic: baseline flood area correlates with depth
                # For flash floods, assume average depth of 0.5m for significant flooding
                baseline_area = flash_flood_analysis.get('baseline_flood_area_km2', 0.0)
                estimated_flood_depth = 0.5 if baseline_area > 0 else 0.0
                
                # Only calculate if we have valid inputs and flooding exists
                if asset_value > 0 and estimated_flood_depth > 0:
                    import sys
                    print(f"[INFRASTRUCTURE ROI] Calculating for estimated_depth={estimated_flood_depth}m, asset_value=${asset_value}, intervention={intervention_type}", file=sys.stderr, flush=True)
                    
                    infrastructure_roi = calculate_infrastructure_roi(
                        flood_depth_m=estimated_flood_depth,
                        asset_value=asset_value,
                        daily_revenue=daily_revenue,
                        project_capex=capex,
                        project_opex=opex,
                        intervention_type=intervention_type,
                        analysis_years=20,
                        discount_rate=0.10,
                        wall_height_m=intervention_params.get('wall_height_m', 2.0),
                        drainage_reduction_m=intervention_params.get('drainage_reduction_m', 0.3)
                    )
                    
                    print(f"[INFRASTRUCTURE ROI] Complete: NPV=${infrastructure_roi['financial_analysis']['npv']:,.0f}, BCR={infrastructure_roi['financial_analysis']['bcr']:.2f}", file=sys.stderr, flush=True)
                    
            except Exception as roi_error:
                import sys
                print(f"Infrastructure ROI error: {roi_error}", file=sys.stderr, flush=True)
                infrastructure_roi = None
        
        # Add infrastructure_roi if available
        if infrastructure_roi is not None:
            response_data['infrastructure_roi'] = infrastructure_roi
        
        return jsonify({
            'status': 'success',
            'data': response_data
        }), 200
    
    except ValueError:
        return jsonify({
            'status': 'error',
            'message': 'Invalid numeric values for lat/lon/rain_intensity_pct',
            'code': 'INVALID_NUMERIC_VALUE'
        }), 400
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Flash flood analysis failed: {str(e)}',
            'code': 'FLASH_FLOOD_ERROR'
        }), 500


@app.route('/predict-flood', methods=['POST'])
@validate_json('rain_intensity', 'current_imperviousness', 'intervention_type')
def predict_flood():
    """Predict urban flood depth with and without green infrastructure intervention."""
    if flood_model is None:
        return jsonify({
            'status': 'error',
            'message': 'Flood model file not found. Ensure flood_surrogate.pkl exists.',
            'code': 'MODEL_NOT_FOUND'
        }), 500

    try:
        data = request.get_json()
        rain_intensity = float(data['rain_intensity'])
        current_imperviousness = float(data['current_imperviousness'])
        intervention_type = str(data['intervention_type']).lower()
        
        # Optional parameters with defaults
        slope_pct = float(data.get('slope_pct', 2.0))
        building_value = float(data.get('building_value', 750000))  # Use frontend value or default
        num_buildings = int(data.get('num_buildings', 1))  # Default to 1 building
        
        # Log the request for debugging
        import sys
        print(f"[FLOOD REQUEST] rain={rain_intensity}, impervious={current_imperviousness}, intervention={intervention_type}, slope={slope_pct}, building_value=${building_value}, num_buildings={num_buildings}", file=sys.stderr, flush=True)
        
        # Validate inputs
        if not (10 <= rain_intensity <= 150):
            return jsonify({
                'status': 'error',
                'message': 'Rain intensity must be between 10 and 150 mm/hr',
                'code': 'INVALID_RAIN_INTENSITY'
            }), 400
        
        if not (0.0 <= current_imperviousness <= 1.0):
            return jsonify({
                'status': 'error',
                'message': 'Current imperviousness must be between 0.0 and 1.0',
                'code': 'INVALID_IMPERVIOUSNESS'
            }), 400
        
        if not (0.1 <= slope_pct <= 10.0):
            return jsonify({
                'status': 'error',
                'message': 'Slope must be between 0.1 and 10.0 percent',
                'code': 'INVALID_SLOPE'
            }), 400
        
        # Define imperviousness reduction factors based on research
        # Sources:
        # - Green Roof: EPA Green Infrastructure Case Studies (2010)
        #   Reduces effective imperviousness by 30-40% of roof area
        # - Permeable Pavement: ASCE Low Impact Development Manual (2015)
        #   Reduces effective imperviousness by 40-50% of paved area
        INTERVENTION_FACTORS = {
            'green_roof': 0.30,        # 30% reduction
            'permeable_pavement': 0.40, # 40% reduction
            'bioswales': 0.25,         # 25% reduction
            'rain_gardens': 0.20,      # 20% reduction
            'none': 0.0                # No intervention
        }
        
        if intervention_type not in INTERVENTION_FACTORS:
            return jsonify({
                'status': 'error',
                'message': f'Invalid intervention type. Must be one of: {", ".join(INTERVENTION_FACTORS.keys())}',
                'code': 'INVALID_INTERVENTION_TYPE'
            }), 400
        
        # Scenario A (Baseline): Current imperviousness
        baseline_df = pd.DataFrame({
            'rain_intensity_mm_hr': [rain_intensity],
            'impervious_pct': [current_imperviousness],
            'slope_pct': [slope_pct]
        })
        
        # Scenario B (Intervention): Reduced imperviousness
        reduction_factor = INTERVENTION_FACTORS[intervention_type]
        intervention_imperviousness = max(0.0, current_imperviousness - reduction_factor)
        
        intervention_df = pd.DataFrame({
            'rain_intensity_mm_hr': [rain_intensity],
            'impervious_pct': [intervention_imperviousness],
            'slope_pct': [slope_pct]
        })
        
        # Run predictions
        depth_baseline = float(flood_model.predict(baseline_df)[0])
        depth_intervention = float(flood_model.predict(intervention_df)[0])
        
        # Calculate avoided depth
        avoided_depth_cm = depth_baseline - depth_intervention
        
        # Calculate percentage improvement
        percentage_improvement = (avoided_depth_cm / depth_baseline * 100) if depth_baseline > 0 else 0
        
        # Economic valuation using urban flood depth-damage functions
        # Based on urban infrastructure damage research (Thieken et al., 2008; Huizinga et al., 2017)
        # For urban flooding, damage begins at very shallow depths
        def calculate_flood_damage_pct(depth_cm):
            """
            Calculate percent damage using urban flood depth-damage curve.
            
            Urban flooding causes damage even at shallow depths:
            - 0-5 cm: Minimal damage (0-2%)
            - 5-15 cm: Minor damage to contents and finishes (2-8%)
            - 15-30 cm: Moderate damage to walls, electrical, HVAC (8-20%)
            - 30-60 cm: Major damage to structure and systems (20-40%)
            - >60 cm: Severe damage requiring major renovation (40-70%)
            
            Formula: Piecewise exponential curve fitted to urban flood data
            """
            import math
            
            if depth_cm <= 0:
                return 0.0
            
            # Urban flood damage curve (more sensitive to shallow depths)
            # Based on European Flood Damage Database (Huizinga et al., 2017)
            # Adjusted for U.S. construction standards
            if depth_cm < 5:
                # Very shallow: linear from 0% to 2%
                damage_pct = (depth_cm / 5.0) * 2.0
            elif depth_cm < 15:
                # Shallow: exponential growth from 2% to 8%
                normalized_depth = (depth_cm - 5) / 10.0
                damage_pct = 2.0 + (6.0 * normalized_depth)
            elif depth_cm < 30:
                # Moderate: exponential growth from 8% to 20%
                normalized_depth = (depth_cm - 15) / 15.0
                damage_pct = 8.0 + (12.0 * normalized_depth)
            elif depth_cm < 60:
                # Major: exponential growth from 20% to 40%
                normalized_depth = (depth_cm - 30) / 30.0
                damage_pct = 20.0 + (20.0 * normalized_depth)
            else:
                # Severe: exponential growth from 40% to 70%
                normalized_depth = min((depth_cm - 60) / 60.0, 1.0)
                damage_pct = 40.0 + (30.0 * normalized_depth)
            
            return min(damage_pct, 70.0)  # Cap at 70% for urban floods
        
        baseline_damage_pct = calculate_flood_damage_pct(depth_baseline)
        intervention_damage_pct = calculate_flood_damage_pct(depth_intervention)
        avoided_damage_pct = baseline_damage_pct - intervention_damage_pct
        
        # Economic value calculation
        # Use building_value and num_buildings from request, or defaults
        # This allows frontend to control the economic calculation
        avoided_damage_usd = (avoided_damage_pct / 100) * num_buildings * building_value
        
        return jsonify({
            'status': 'success',
            'data': {
                'input_conditions': {
                    'rain_intensity_mm_hr': rain_intensity,
                    'current_imperviousness': current_imperviousness,
                    'intervention_type': intervention_type,
                    'slope_pct': slope_pct,
                    'building_value': building_value,
                    'num_buildings': num_buildings
                },
                'imperviousness_change': {
                    'baseline': round(current_imperviousness, 3),
                    'intervention': round(intervention_imperviousness, 3),
                    'reduction_factor': reduction_factor,
                    'absolute_reduction': round(current_imperviousness - intervention_imperviousness, 3)
                },
                'predictions': {
                    'baseline_depth_cm': round(depth_baseline, 2),
                    'intervention_depth_cm': round(depth_intervention, 2)
                },
                'analysis': {
                    'avoided_depth_cm': round(avoided_depth_cm, 2),
                    'percentage_improvement': round(percentage_improvement, 2),
                    'baseline_damage_pct': round(baseline_damage_pct, 2),
                    'intervention_damage_pct': round(intervention_damage_pct, 2),
                    'avoided_damage_pct': round(avoided_damage_pct, 2),
                    'avoided_loss': round(avoided_damage_usd, 2),
                    'recommendation': intervention_type if avoided_depth_cm > 0 else 'none'
                },
                'economic_assumptions': {
                    'num_buildings': num_buildings,
                    'avg_building_value': building_value,
                    'total_value_at_risk': num_buildings * building_value,
                    'damage_function': 'Urban Flood Damage (Huizinga et al., 2017)',
                    'total_value_basis': 'Avoided structural damage across affected buildings'
                },
                # Add flat fields for frontend compatibility
                'depth_baseline': round(depth_baseline, 2),
                'depth_intervention': round(depth_intervention, 2),
                'avoided_loss': round(avoided_damage_usd, 2)
            }
        }), 200

    except ValueError as ve:
        return jsonify({
            'status': 'error',
            'message': f'Invalid numeric values: {str(ve)}',
            'code': 'INVALID_NUMERIC_VALUE'
        }), 400
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Prediction failed: {str(e)}',
            'code': 'PREDICTION_ERROR'
        }), 500


@app.route('/start-batch', methods=['POST'])
@validate_json('job_id')
def start_batch():
    """Start a background batch processing job for portfolio assets."""
    try:
        data = request.get_json()
        job_id = str(data['job_id'])
        
        # Start batch processing in a background thread
        # This prevents the API from timing out during long-running jobs
        thread = threading.Thread(
            target=run_batch_job,
            args=(job_id,),
            daemon=True
        )
        thread.start()
        
        import sys
        print(f"[API] Started batch job {job_id} in background thread", file=sys.stderr, flush=True)
        
        return jsonify({
            'status': 'started',
            'job_id': job_id,
            'message': 'Batch processing started in background. Check batch_jobs table for status.'
        }), 202  # 202 Accepted - request accepted for processing
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to start batch job: {str(e)}',
            'code': 'BATCH_START_ERROR'
        }), 500


@app.route('/calculate-financials', methods=['POST'])
def calculate_financials():
    """
    Calculate financial metrics (NPV, BCR, Payback Period) from cash flows.
    
    This is a utility endpoint for testing financial calculations in the UI.
    """
    if not request.is_json:
        return jsonify({
            'status': 'error',
            'message': 'Request must be JSON',
            'code': 'INVALID_CONTENT_TYPE'
        }), 400
    
    try:
        data = request.get_json()
        
        # Validate required fields
        if 'cash_flows' not in data or 'discount_rate' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Missing required fields: cash_flows and discount_rate',
                'code': 'MISSING_FIELDS'
            }), 400
        
        cash_flows = data['cash_flows']
        discount_rate = float(data['discount_rate'])
        
        # Validate cash_flows is a list
        if not isinstance(cash_flows, list) or len(cash_flows) < 2:
            return jsonify({
                'status': 'error',
                'message': 'cash_flows must be a list with at least 2 values',
                'code': 'INVALID_CASH_FLOWS'
            }), 400
        
        # Convert all cash flows to float
        cash_flows = [float(cf) for cf in cash_flows]
        
        # Validate discount rate
        if not (0 <= discount_rate <= 1.0):
            return jsonify({
                'status': 'error',
                'message': 'discount_rate must be between 0.0 and 1.0 (e.g., 0.10 for 10%)',
                'code': 'INVALID_DISCOUNT_RATE'
            }), 400
        
        # Calculate financial metrics
        metrics = calculate_roi_metrics(cash_flows, discount_rate)
        
        return jsonify({
            'status': 'success',
            'data': {
                'input': {
                    'cash_flows': cash_flows,
                    'discount_rate': discount_rate,
                    'discount_rate_pct': round(discount_rate * 100, 2)
                },
                'metrics': metrics,
                'interpretation': {
                    'npv_positive': metrics['npv'] > 0,
                    'bcr_favorable': metrics['bcr'] > 1.0,
                    'recommendation': 'INVEST' if metrics['npv'] > 0 and metrics['bcr'] > 1.0 else 'DO NOT INVEST'
                }
            }
        }), 200
    
    except ValueError as ve:
        return jsonify({
            'status': 'error',
            'message': f'Invalid numeric values: {str(ve)}',
            'code': 'INVALID_NUMERIC_VALUE'
        }), 400
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Financial calculation failed: {str(e)}',
            'code': 'CALCULATION_ERROR'
        }), 500


@app.route('/predict-portfolio', methods=['POST'])
def predict_portfolio():
    """
    Analyze portfolio diversification across multiple locations.
    
    Simulates 10 years of climate variation for each location and
    calculates aggregate tonnage and portfolio volatility.
    """
    if not request.is_json:
        return jsonify({
            'status': 'error',
            'message': 'Request must be JSON',
            'code': 'INVALID_CONTENT_TYPE'
        }), 400
    
    try:
        import random
        import sys
        from physics_engine import calculate_volatility
        
        data = request.get_json()
        
        # Validate required fields
        if 'locations' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Missing required field: locations',
                'code': 'MISSING_FIELDS'
            }), 400
        
        locations = data['locations']
        crop_type = data.get('crop_type', 'maize').lower()
        
        # Validate crop type
        if crop_type not in ['maize', 'cocoa']:
            return jsonify({
                'status': 'error',
                'message': f"Unsupported crop_type: {crop_type}. Supported crops: 'maize', 'cocoa'",
                'code': 'INVALID_CROP_TYPE'
            }), 400
        
        # Validate locations is a list
        if not isinstance(locations, list) or len(locations) == 0:
            return jsonify({
                'status': 'error',
                'message': 'locations must be a non-empty list',
                'code': 'INVALID_LOCATIONS'
            }), 400
        
        print(f"[PORTFOLIO] Processing {len(locations)} locations for crop_type={crop_type}", file=sys.stderr, flush=True)
        
        # Portfolio metrics
        all_location_cvs = []
        total_tonnage = 0.0
        location_results = []
        
        # Process each location
        for idx, loc in enumerate(locations):
            if 'lat' not in loc or 'lon' not in loc:
                return jsonify({
                    'status': 'error',
                    'message': f'Location {idx} missing lat or lon',
                    'code': 'INVALID_LOCATION_COORDS'
                }), 400
            
            lat = float(loc['lat'])
            lon = float(loc['lon'])
            
            # Validate coordinates
            if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                return jsonify({
                    'status': 'error',
                    'message': f'Location {idx} has invalid coordinates',
                    'code': 'INVALID_COORDINATES'
                }), 400
            
            print(f"[PORTFOLIO] Location {idx+1}/{len(locations)}: lat={lat}, lon={lon}", file=sys.stderr, flush=True)
            
            # Fetch weather data from GEE
            try:
                from datetime import datetime, timedelta
                
                end_date = datetime.now()
                start_date = end_date - timedelta(days=365)
                
                weather_data = get_weather_data(
                    lat=lat,
                    lon=lon,
                    start_date=start_date.strftime('%Y-%m-%d'),
                    end_date=end_date.strftime('%Y-%m-%d')
                )
                
                base_temp = weather_data['max_temp_celsius']
                base_rain = weather_data['total_precip_mm']
                
            except Exception as weather_error:
                print(f"Weather data error for location {idx}: {weather_error}", file=sys.stderr, flush=True)
                return jsonify({
                    'status': 'error',
                    'message': f'Failed to fetch weather data for location {idx}: {str(weather_error)}',
                    'code': 'WEATHER_DATA_ERROR'
                }), 500
            
            # Simulate 10 years of climate variation with resilient seed
            # Each year has random climate perturbations to simulate natural variability
            years = 10
            annual_yields = []
            
            for year in range(years):
                # Simulate climate variability:
                # Temperature: ±2°C random variation
                # Rainfall: ±15% random variation
                temp_variation = random.uniform(-2.0, 2.0)
                rain_variation = random.uniform(-15.0, 15.0)
                
                # Calculate yield for this year using resilient seed
                year_yield = calculate_yield(
                    temp=base_temp,
                    rain=base_rain,
                    seed_type=SEED_TYPES['resilient'],
                    crop_type=crop_type,
                    temp_delta=temp_variation,
                    rain_pct_change=rain_variation
                )
                
                annual_yields.append(year_yield)
            
            # Calculate statistics for this location
            import statistics
            mean_yield = statistics.mean(annual_yields)
            location_cv = calculate_volatility(annual_yields)
            
            # Assume 1 hectare per location for tonnage calculation
            # Tonnage = (mean_yield / 100) * max_potential_tons_per_hectare
            # For simplicity, assume max potential = 10 tons/ha
            max_potential_tons = 10.0
            location_tonnage = (mean_yield / 100.0) * max_potential_tons
            
            total_tonnage += location_tonnage
            all_location_cvs.append(location_cv)
            
            location_results.append({
                'location_index': idx,
                'lat': lat,
                'lon': lon,
                'mean_yield_pct': round(mean_yield, 2),
                'volatility_cv_pct': location_cv,
                'tonnage': round(location_tonnage, 2)
            })
            
            print(f"[PORTFOLIO] Location {idx+1} complete: mean_yield={mean_yield:.2f}%, CV={location_cv:.2f}%, tonnage={location_tonnage:.2f}t", file=sys.stderr, flush=True)
        
        # Calculate portfolio-level volatility (average of all CVs)
        portfolio_volatility = statistics.mean(all_location_cvs) if all_location_cvs else 0.0
        
        # Determine risk rating based on portfolio volatility
        if portfolio_volatility < 10.0:
            risk_rating = "Low"
        elif portfolio_volatility < 20.0:
            risk_rating = "Medium"
        elif portfolio_volatility < 30.0:
            risk_rating = "High"
        else:
            risk_rating = "Very High"
        
        print(f"[PORTFOLIO] Complete: total_tonnage={total_tonnage:.2f}t, portfolio_volatility={portfolio_volatility:.2f}%, risk={risk_rating}", file=sys.stderr, flush=True)
        
        return jsonify({
            'status': 'success',
            'data': {
                'portfolio_summary': {
                    'total_tonnage': round(total_tonnage, 2),
                    'portfolio_volatility_pct': round(portfolio_volatility, 2),
                    'risk_rating': risk_rating,
                    'num_locations': len(locations),
                    'crop_type': crop_type
                },
                'locations': location_results,
                'risk_interpretation': {
                    'low': '0-10% CV: Very stable production',
                    'medium': '10-20% CV: Moderate variation',
                    'high': '20-30% CV: Significant variation',
                    'very_high': '30%+ CV: Highly volatile'
                }
            }
        }), 200
    
    except ValueError as ve:
        return jsonify({
            'status': 'error',
            'message': f'Invalid numeric values: {str(ve)}',
            'code': 'INVALID_NUMERIC_VALUE'
        }), 400
    except Exception as e:
        import sys
        print(f"Portfolio error: {e}", file=sys.stderr, flush=True)
        return jsonify({
            'status': 'error',
            'message': f'Portfolio analysis failed: {str(e)}',
            'code': 'PORTFOLIO_ERROR'
        }), 500


@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'service': 'Climate Resilience Engine',
        'version': '1.0.0'
    }), 200


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'status': 'error',
        'message': 'Endpoint not found',
        'code': 'NOT_FOUND'
    }), 404


@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        'status': 'error',
        'message': 'Method not allowed',
        'code': 'METHOD_NOT_ALLOWED'
    }), 405


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True)
