FROM python:3.12-slim

WORKDIR /app

# system deps
RUN apt-get update && apt-get install -y \
    ffmpeg libsm6 libxext6 && \
    rm -rf /var/lib/apt/lists/*

COPY services/detector_service/detector_service.py /app/
COPY services/detector_service/requirements.txt /app/

# shared project code
COPY tracking /app/tracking
COPY utils /app/utils
COPY canvas /app/canvas
COPY shared /app/shared
COPY ball_acq /app/ball_acq

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000
CMD ["python", "detector_service.py"]
