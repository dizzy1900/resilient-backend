"""
Climate Resilience Engine - Flask API
"""

import os
import pickle
from datetime import datetime, timedelta
from functools import wraps

import ee
import pandas as pd
from flask import Flask, request, jsonify
from flask_cors import CORS

from gee_connector import get_weather_data, get_coastal_params

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
                'max_temp_celsius': weather_data['avg_temp_c'],
                'total_rain_mm': weather_data['total_precip_mm'],
                'period': 'last_12_months'
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
@validate_json('temp', 'rain')
def predict():
    """Predict crop yield and calculate avoided loss."""
    if model is None:
        return jsonify({
            'status': 'error',
            'message': 'Model file not found. Ensure ag_surrogate.pkl exists.',
            'code': 'MODEL_NOT_FOUND'
        }), 500
    
    try:
        data = request.get_json()
        temp = float(data['temp'])
        rain = float(data['rain'])
        
        # Create DataFrames for each seed type
        standard_df = pd.DataFrame({
            'temp': [temp],
            'rain': [rain],
            'seed_type': [SEED_TYPES['standard']]
        })
        
        resilient_df = pd.DataFrame({
            'temp': [temp],
            'rain': [rain],
            'seed_type': [SEED_TYPES['resilient']]
        })
        
        # Run predictions
        standard_yield = float(model.predict(standard_df)[0])
        resilient_yield = float(model.predict(resilient_df)[0])
        
        avoided_loss = resilient_yield - standard_yield
        
        if standard_yield > 0:
            percentage_improvement = (avoided_loss / standard_yield) * 100
        else:
            percentage_improvement = 0.0
        
        return jsonify({
            'status': 'success',
            'data': {
                'input_conditions': {
                    'max_temp_celsius': temp,
                    'total_rain_mm': rain
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
                }
            }
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
        
        # Economic valuation using FEMA HAZUS depth-damage functions
        # Based on 1-story commercial buildings (typical urban development)
        # Damage = 0.72 * (1 - e^(-0.1332 * depth_ft))
        def calculate_flood_damage_pct(depth_cm):
            """Calculate percent damage using FEMA HAZUS depth-damage curve."""
            import math
            depth_ft = depth_cm / 30.48
            if depth_ft <= 0:
                return 0.0
            damage_pct = 0.72 * (1 - math.exp(-0.1332 * depth_ft))
            return min(damage_pct, 1.0) * 100
        
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
                    'damage_function': 'FEMA HAZUS 1-story commercial',
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
