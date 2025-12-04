FROM pytorch/pytorch:2.9.1-cuda13.0-cudnn9-runtime

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV TZ=Etc/UTC

ENV PYTHONPATH=/app

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    libgl1 \
    libglib2.0-0 \
    libgl1-mesa-glx \
    libgtk2.0-dev \
    && rm -rf /var/lib/apt/lists/*

RUN ln -s /usr/bin/python3 /usr/bin/python

WORKDIR /app

RUN python -m pip install --no-cache-dir --upgrade pip

COPY services/court_service/requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt

RUN python -m pip install --no-cache-dir 'git+https://github.com/cvg/LightGlue.git#egg=lightglue[superpoint]'

RUN python -c "\
from lightglue import LightGlue, SuperPoint; \
SuperPoint(max_num_keypoints=2048).eval(); \
LightGlue(features='superpoint').eval(); \
print('Model downloads complete.')"

COPY shared/ ./shared/
COPY services/court_service/ ./court_service/

EXPOSE 8000

CMD ["uvicorn", "court_service.service:app", "--host", "0.0.0.0", "--port", "8000"]