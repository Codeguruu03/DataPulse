# Multi-stage Python 3.11 Image for DataPulse
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Install DataPulse package in editable mode
RUN pip install -e .

EXPOSE 8000

# Default entrypoint starts API and Dashboard
CMD ["uvicorn", "datapulse.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
