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
echo "Waiting for Grafana to be ready..."

# Wait for Grafana API to become responsive
until curl -s http://localhost:3000/api/health >/dev/null; do
    echo "Grafana not ready yet, retrying..."
    sleep 2
done

echo "Grafana is up! Uploading dashboard..."

curl -s -X POST http://localhost:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -u admin:admin \
  -d @monitoring/dashboard.json

echo ""
echo "Dashboard uploaded!"

echo "Waiting 30 seconds before running tests..."
sleep 30

echo "Running tests..."
python tests/main.py
