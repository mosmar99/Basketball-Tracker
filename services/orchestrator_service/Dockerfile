FROM python:3.12-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg libsm6 libxext6 \
 && rm -rf /var/lib/apt/lists/*

# Copy orchestrator service as a proper Python package
COPY services/orchestrator_service /app/orchestrator_service

# Ensure Python treats it as a package
RUN touch /app/orchestrator_service/__init__.py

# Copy shared modules
COPY tracking /app/tracking
COPY utils /app/utils
COPY canvas /app/canvas
COPY shared /app/shared
COPY ball_acq /app/ball_acq
COPY team_assigner /app/team_assigner

# Install requirements
COPY services/orchestrator_service/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

EXPOSE 8000

# Start API
CMD ["uvicorn", "orchestrator_service.orchestrator_service:app", "--host", "0.0.0.0", "--port", "8000"]
