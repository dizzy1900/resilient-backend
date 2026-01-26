"""
Climate Resilience Engine - Flask API
"""

import os
import pickle
import urllib.request
from datetime import datetime, timedelta
from functools import wraps

import ee
import pandas as pd
from flask import Flask, request, jsonify
from flask_cors import CORS

from gee_connector import get_weather_data

app = Flask(__name__)
CORS(app)

# Model configuration
MODEL_PATH = 'ag_surrogate.pkl'
MODEL_URL = os.getenv(
    'MODEL_URL',
    'https://github.com/dizzy1900/adaptmetric-backend/releases/download/v1.0.0/ag_surrogate.pkl'
)
model = None


def download_model():
    """Download model from GitHub Releases if not present locally."""
    if os.path.exists(MODEL_PATH):
        return True
    print(f"Downloading model from {MODEL_URL}...")
    try:
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
        print("Model downloaded successfully.")
        return True
    except Exception as e:
        print(f"Failed to download model: {e}")
        return False


# Download and load model at startup
download_model()

try:
    with open(MODEL_PATH, 'rb') as f:
        model = pickle.load(f)
except FileNotFoundError:
    print(f"Warning: Model file '{MODEL_PATH}' not found. /predict endpoint will fail.")
except Exception as e:
    print(f"Warning: Failed to load model: {e}")

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
