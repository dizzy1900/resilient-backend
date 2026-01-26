#!/usr/bin/env sh
set -eu

python download_model.py

exec gunicorn main:app --bind 0.0.0.0:${PORT:-8000}
