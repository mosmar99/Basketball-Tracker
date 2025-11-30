FROM python:3.10

WORKDIR /app

COPY services/video_viewer_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/video_viewer_service/video_viewer_api.py .
COPY shared /app/shared

EXPOSE 8000

CMD ["uvicorn", "video_viewer_api:app", "--host", "0.0.0.0", "--port", "8000"]
