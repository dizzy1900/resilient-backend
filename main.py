import os
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


def authenticate_gee():
    """Placeholder for Google Earth Engine authentication."""
    pass


@app.route('/')
def index():
    return jsonify({'status': 'active'})


if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
