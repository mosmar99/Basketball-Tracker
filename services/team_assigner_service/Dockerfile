FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    ffmpeg libsm6 libxext6 \
    && rm -rf /var/lib/apt/lists/*

COPY services/team_assigner_service/requirements.txt .

RUN pip3 install --upgrade pip && \
pip3 install -r requirements.txt

COPY shared/ ./shared/
COPY services/team_assigner_service/ ./team_assigner_service/

EXPOSE 8000

CMD ["uvicorn", "team_assigner_service.team_assigner_service:app", "--host", "0.0.0.0", "--port", "8000"]