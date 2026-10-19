# --- Stage 1: Build Frontend Dashboard ---
FROM node:20-alpine AS frontend-builder
WORKDIR /app/web
COPY web/package*.json ./
RUN npm ci
COPY web/ ./
RUN npm run build

# --- Stage 2: Python Backend & Runtime ---
FROM python:3.12-slim AS runner
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code, testbed, tests, scripts
COPY engine/ ./engine/
COPY services/ ./services/
COPY tests/ ./tests/
COPY scripts/ ./scripts/
COPY docs/ ./docs/
COPY README.md ./

# Copy built frontend assets from stage 1
COPY --from=frontend-builder /app/web/dist ./web/dist

ENV PYTHONUNBUFFERED=1

# Start AEGIS unified platform
CMD ["python", "scripts/run_platform.py"]
