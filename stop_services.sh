#!/bin/bash
# UU Plastination - Stop all services

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Stopping UU Plastination Services ==="
echo ""

# Stop API
echo "Stopping FastAPI application..."
pkill -f "uvicorn app.main:app" || echo "API was not running"

# Stop Docker containers
echo "Stopping LiveKit and Ingress containers..."
cd webrtc
docker compose down
cd ..

echo ""
echo "All services stopped."
