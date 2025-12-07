FROM python:3.12-slim

ENV PYTHONPATH=/app

# 1. Install system dependencies
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Upgrade pip
RUN python -m pip install --no-cache-dir --upgrade pip

# 2. Copy requirements
COPY services/ui_service/requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt

# 3. Copy source
COPY shared/ ./shared/
COPY services/ui_service/ ./ui_service/

# 4. Gradio usually runs on 7860, not 8000
EXPOSE 7860
ENV PYTHONUNBUFFERED=1

# 5. Point to the file inside the folder (assuming your main file is app.py)
CMD ["python", "ui_service/service.py"]