#!/usr/bin/env sh
set -e

MODEL_URL="${MODEL_URL:-https://github.com/dizzy1900/adaptmetric-backend/releases/download/v1.0.0/ag_surrogate.pkl}"
MODEL_PATH="ag_surrogate.pkl"

if [ ! -f "$MODEL_PATH" ]; then
  echo "Downloading model from $MODEL_URL..."
  curl -L --retry 3 --retry-delay 5 --max-time 120 -o "$MODEL_PATH" "$MODEL_URL"
  echo "Model downloaded successfully."
fi

exec gunicorn main:app --bind 0.0.0.0:${PORT:-8000} --workers 2 --threads 4 --timeout 120
