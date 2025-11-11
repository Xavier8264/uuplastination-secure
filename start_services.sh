#!/bin/bash
# UU Plastination - Start all services
# This script starts the WebRTC infrastructure and API server

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== UU Plastination Service Startup ==="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "ERROR: .env file not found. Copy .env.example to .env and configure it."
    exit 1
fi

# Start LiveKit and Ingress containers
echo "Starting LiveKit and Ingress containers..."
cd webrtc
docker compose up -d
cd ..

# Wait for LiveKit to be ready
echo "Waiting for LiveKit to start..."
for i in {1..10}; do
    if curl -s http://127.0.0.1:7880 > /dev/null 2>&1; then
        echo "LiveKit is ready!"
        break
    fi
    if [ $i -eq 10 ]; then
        echo "WARNING: LiveKit may not be running properly"
    fi
    sleep 1
done

# Start FastAPI application
echo "Starting FastAPI application..."
source venv/bin/activate
nohup python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000 > /tmp/uuplastination-api.log 2>&1 &
API_PID=$!
echo "API started with PID $API_PID"

# Wait for API to be ready
echo "Waiting for API to start..."
for i in {1..10}; do
    if curl -s http://127.0.0.1:8000/webrtc/health > /dev/null 2>&1; then
        echo "API is ready!"
        break
    fi
    if [ $i -eq 10 ]; then
        echo "WARNING: API may not be running properly"
    fi
    sleep 1
done

echo ""
echo "=== Service Status ==="
echo "LiveKit:  http://127.0.0.1:7880"
echo "API:      http://127.0.0.1:8000"
echo "Dashboard: http://127.0.0.1:8000/"
echo ""
echo "To view API logs: tail -f /tmp/uuplastination-api.log"
echo "To view LiveKit logs: docker logs livekit"
echo "To stop services: ./stop_services.sh"
echo ""
echo "=== Diagnostics ==="
curl -s http://127.0.0.1:8000/webrtc/health | python3 -m json.tool 2>/dev/null || echo "API health check failed"
