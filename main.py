import os
import json
import ee
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


def authenticate_gee():
    """
    Initialize Google Earth Engine using Service Account credentials
    stored in the GEE_SERVICE_ACCOUNT_JSON environment variable.
    
    The environment variable should contain the complete JSON string
    of the service account key file.
    
    Raises:
        ValueError: If the environment variable is not set or empty.
        json.JSONDecodeError: If the JSON string is invalid.
        ee.EEException: If Earth Engine initialization fails.
    
    Returns:
        bool: True if initialization is successful.
    """
    service_account_json = os.environ.get('GEE_SERVICE_ACCOUNT_JSON')
    
    if not service_account_json:
        raise ValueError(
            "GEE_SERVICE_ACCOUNT_JSON environment variable is not set. "
            "Please set it with your service account JSON string."
        )
    
    try:
        service_account_info = json.loads(service_account_json)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(
            f"Invalid JSON in GEE_SERVICE_ACCOUNT_JSON: {e.msg}",
            e.doc,
            e.pos
        )
    
    service_account_email = service_account_info.get('client_email')
    
    if not service_account_email:
        raise ValueError(
            "Service account JSON is missing 'client_email' field."
        )
    
    credentials = ee.ServiceAccountCredentials(
        email=service_account_email,
        key_data=service_account_json
    )
    
    ee.Initialize(credentials=credentials)
    
    return True


@app.route('/')
def index():
    return jsonify({'status': 'active'})


if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
