#!/usr/bin/env sh

MODEL_URL="${MODEL_URL:-https://github.com/dizzy1900/adaptmetric-backend/releases/download/v1.1.0/ag_surrogate.pkl}"
COASTAL_MODEL_URL="${COASTAL_MODEL_URL:-https://github.com/dizzy1900/adaptmetric-backend/releases/download/v1.1.0/coastal_surrogate.pkl}"
MIN_MODEL_SIZE=10000000  # 10MB minimum expected size

echo "=== Model Download Setup ==="
echo "Agricultural Model URL: $MODEL_URL"
echo "Coastal Model URL: $COASTAL_MODEL_URL"

# Download or validate models using Python
python3 << 'PYTHON_SCRIPT'
import os
import sys
import urllib.request

def download_model(model_url, model_path, min_size):
    """Download and validate a model file."""
    print(f"\n--- Processing {model_path} ---")
    print(f"URL: {model_url}")
    
    # Check if file exists and validate
    if os.path.exists(model_path):
        file_size = os.path.getsize(model_path)
        print(f"File exists: YES (size: {file_size} bytes)")
        
        # Read first bytes to check for HTML
        with open(model_path, 'rb') as f:
            first_bytes = f.read(15).decode('utf-8', errors='ignore')
        
        # Re-download if too small or looks like HTML
        if file_size < min_size or 'HTTP' in first_bytes or '<!DOCTYPE' in first_bytes or '<html' in first_bytes:
            print(f"Found corrupted file (size={file_size}, first_bytes={repr(first_bytes)}). Removing...")
            os.remove(model_path)
        else:
            print(f"Valid file found, skipping download")
            return True
    else:
        print("File exists: NO")
    
    # Download if missing
    if not os.path.exists(model_path):
        print(f"Downloading from {model_url}...")
        try:
            urllib.request.urlretrieve(model_url, model_path)
            file_size = os.path.getsize(model_path)
            print(f"Downloaded successfully. Size: {file_size} bytes")
            
            # Verify size
            if file_size < min_size:
                print(f"ERROR: Downloaded file too small ({file_size} bytes), expected > {min_size/1_000_000}MB")
                return False
            
            # Verify content
            with open(model_path, 'rb') as f:
                first_bytes = f.read(15).decode('utf-8', errors='ignore')
            if 'HTTP' in first_bytes or '<!DOCTYPE' in first_bytes or '<html' in first_bytes:
                print(f"ERROR: Downloaded file looks like HTML, not pickle data")
                return False
                
            return True
        except Exception as e:
            print(f"ERROR: Download failed: {e}")
            return False
    
    return True

# Get environment variables
ag_model_url = os.environ.get("MODEL_URL", "https://github.com/dizzy1900/adaptmetric-backend/releases/download/v1.1.0/ag_surrogate.pkl")
coastal_model_url = os.environ.get("COASTAL_MODEL_URL", "https://github.com/dizzy1900/adaptmetric-backend/releases/download/v1.1.0/coastal_surrogate.pkl")
min_size = 10_000_000  # 10MB

print("\n=== Downloading Models ===")

# Download agricultural model
success_ag = download_model(ag_model_url, "ag_surrogate.pkl", min_size)

# Download coastal model (smaller, so use 5MB minimum)
success_coastal = download_model(coastal_model_url, "coastal_surrogate.pkl", 5_000_000)

if not success_ag or not success_coastal:
    print("\n=== ERROR: Model download failed ===")
    sys.exit(1)

print("\n=== All models downloaded successfully ===")
PYTHON_SCRIPT

if [ $? -ne 0 ]; then
    echo "ERROR: Model download/preparation failed"
    exit 1
fi

echo ""
echo "=== Starting Gunicorn ==="
exec gunicorn main:app --bind 0.0.0.0:${PORT:-8000} --workers 2 --threads 4 --timeout 120
