FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    ffmpeg libsm6 libxext6 && \
    rm -rf /var/lib/apt/lists/*

COPY services/orchestrator_service/orchestrator_service.py /app/
COPY services/orchestrator_service/api_utils.py /app/
COPY services/orchestrator_service/requirements.txt /app/

COPY tracking /app/tracking
COPY utils /app/utils
COPY canvas /app/canvas
COPY shared /app/shared
COPY ball_acq /app/ball_acq
COPY team_assigner /app/team_assigner

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8002
CMD ["python", "orchestrator_service.py"]
