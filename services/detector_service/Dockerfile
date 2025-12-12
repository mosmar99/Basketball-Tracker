FROM pytorch/pytorch:2.9.1-cuda13.0-cudnn9-runtime

WORKDIR /app

# system deps
RUN apt-get update && apt-get install -y \
    ffmpeg libsm6 libxext6 && \
    rm -rf /var/lib/apt/lists/*

COPY services/detector_service/requirements.txt .

RUN pip3 install --upgrade pip && \
pip3 install -r requirements.txt

# Copy source
COPY shared/ ./shared/
COPY services/detector_service/ ./detector_service/


EXPOSE 8000

CMD ["uvicorn", "detector_service.detector_service:app", "--host", "0.0.0.0", "--port", "8000"]
