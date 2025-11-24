FROM python:3.12

WORKDIR /app

RUN apt-get update && apt-get install -y \
    ffmpeg libsm6 libxext6 \
    && rm -rf /var/lib/apt/lists/*

COPY services/team_assigner_service/requirements.txt /app/

# Install PyTorch with CUDA 13.0 runtime first
RUN pip3 install --upgrade pip && \
    pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cu130 && \
    pip3 install -r requirements.txt

COPY utils /app/utils
COPY shared /app/shared
COPY team_assigner /app/team_assigner
COPY canvas /app/canvas
COPY services/team_assigner_service/team_assigner_service.py /app/

EXPOSE 8001
CMD ["python", "team_assigner_service.py"]
