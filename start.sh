#!/usr/bin/env bash
set -euo pipefail

mkdir -p models
if [ ! -f models/ag_surrogate.pkl ]; then
  curl -L -o models/ag_surrogate.pkl \
    "https://github.com/dizzy1900/adaptmetric-backend/releases/download/v1.0.0/ag.surrogate.pkl"
fi

exec uvicorn app:app --host 0.0.0.0 --port "${PORT:-8000}"
