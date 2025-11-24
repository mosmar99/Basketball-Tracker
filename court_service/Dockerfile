# Base Image
FROM python:3.12

# Set Environment Variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV TZ=Etc/UTC

# Tell Python where to find modules. /app will be our project root inside the container.
ENV PYTHONPATH=/app

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Make python3 the default python
RUN ln -s /usr/bin/python3 /usr/bin/python

# Set up Working Directory
WORKDIR /app

# Install Python Dependencies including Torch packages with cu128
RUN python -m pip install --no-cache-dir --upgrade pip
RUN python -m pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu130

# Copy ONLY the requirements.txt file first to leverage Docker layer caching
COPY court_service/requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt

# Install Superpoint and LightGlue from Repository
RUN python -m pip install --no-cache-dir 'git+https://github.com/cvg/LightGlue.git#egg=lightglue[superpoint]'

# Models are downloaded on first init, run init to provide container with models
RUN python -c "\
from lightglue import LightGlue, SuperPoint; \
SuperPoint(max_num_keypoints=2048).eval(); \
LightGlue(features='superpoint').eval(); \
print('Model downloads complete.')"

# Copy the shared library and the specific service code into the container
COPY shared/ ./shared/
COPY court_service/ ./court_service/

EXPOSE 8000

CMD ["uvicorn", "court_service.service:app", "--host", "0.0.0.0", "--port", "8000"]