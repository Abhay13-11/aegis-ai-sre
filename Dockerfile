# AEGIS Unified AI-SRE Platform Container
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application files (backend, testbed, compiled web dashboard)
COPY . .

ENV PYTHONUNBUFFERED=1

# Start AEGIS unified platform
CMD ["python", "scripts/run_platform.py"]
