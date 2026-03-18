# ---- Build stage: install Python deps in a venv ----
FROM python:3.12-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libgdal-dev \
        libgeos-dev \
        libproj-dev \
        libffi-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --upgrade pip \
    && /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# ---- Runtime stage: slim image with only what we need ----
FROM python:3.12-slim

# System libraries required at runtime by geospatial stack and WeasyPrint
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgdal35 \
        libgeos3.12.2 \
        libproj25 \
        libcairo2 \
        libpango-1.0-0 \
        libpangocairo-1.0-0 \
        libgdk-pixbuf-2.0-0 \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Copy the pre-built virtualenv from the builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app

COPY . .

EXPOSE 8000

# Run uvicorn with 4 workers for production concurrency
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
