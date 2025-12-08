#!/bin/bash
set -e

echo "Checking shared network..."

if ! docker network inspect shared >/dev/null 2>&1; then
    echo "Creating shared network..."
    docker network create shared
else
    echo "Shared network already exists."
fi

echo "Starting all services..."

docker compose \
  -f docker-compose.yml \
  -f monitoring/prometheus-grafana.yml \
  up -d --build

echo "All services started!"
