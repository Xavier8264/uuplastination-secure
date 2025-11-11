#!/bin/bash
# UU Plastination - Check system status

echo "======================================"
echo "UU Plastination System Status Check"
echo "======================================"
echo ""

# Check Docker containers
echo "=== Docker Containers ==="
docker ps --filter name=livekit --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "Docker not available"
echo ""

# Check API process
echo "=== FastAPI Application ==="
if pgrep -f "uvicorn app.main:app" > /dev/null; then
    echo "✅ Running (PID: $(pgrep -f 'uvicorn app.main:app'))"
    echo "   Listening on: http://127.0.0.1:8000"
else
    echo "❌ Not running"
fi
echo ""

# Check LiveKit
echo "=== LiveKit Server ==="
if curl -s http://127.0.0.1:7880 > /dev/null 2>&1; then
    echo "✅ Responding on port 7880"
else
    echo "❌ Not responding on port 7880"
fi
echo ""

# Check WebRTC diagnostics
echo "=== WebRTC Diagnostics ==="
if command -v python3 > /dev/null && command -v curl > /dev/null; then
    DIAG=$(curl -s http://127.0.0.1:8000/webrtc/diagnostics 2>/dev/null)
    if [ $? -eq 0 ]; then
        echo "$DIAG" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(f\"  Host: {d.get('livekit_host_env', 'Not set')}\")
    print(f\"  API Credentials: {'✅ Configured' if d.get('api_credentials_configured') else '❌ Missing'}\")
    print(f\"  ICE Servers: {d.get('ice_servers_count', 0)} configured\")
    print(f\"  Token Generation: {d.get('token_issuance', 'unknown')}\")
    if d.get('recommendations'):
        print(f\"  ⚠️  Recommendations:\")
        for r in d['recommendations']:
            print(f\"      - {r}\")
except:
    print('  Unable to parse diagnostics')
" 2>/dev/null || echo "  Unable to parse response"
    else
        echo "  ❌ API not responding"
    fi
else
    echo "  Skipped (python3 or curl not available)"
fi
echo ""

# Check Camera
echo "=== Camera Status ==="
if curl -s http://127.0.0.1:8000/camera/status > /dev/null 2>&1; then
    curl -s http://127.0.0.1:8000/camera/status | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(f\"  Available: {'✅' if d.get('available') else '❌'}\")
    print(f\"  Running: {'✅' if d.get('running') else '❌'}\")
    print(f\"  Resolution: {d.get('resolution', 'unknown')}\")
    print(f\"  Framerate: {d.get('framerate', 'unknown')} fps\")
    if d.get('publisher'):
        print(f\"  Publisher: {d['publisher'].get('status', 'unknown')}\")
except:
    print('  Unable to parse status')
" 2>/dev/null || echo "  Unable to parse response"
else
    echo "  ❌ Camera API not responding"
fi
echo ""

# Check video devices
echo "=== Video Devices ==="
if ls /dev/video* > /dev/null 2>&1; then
    echo "  Available devices:"
    ls -1 /dev/video* 2>/dev/null | head -5
    DEVICE_COUNT=$(ls -1 /dev/video* 2>/dev/null | wc -l)
    if [ $DEVICE_COUNT -gt 5 ]; then
        echo "  ... and $((DEVICE_COUNT - 5)) more"
    fi
else
    echo "  ❌ No video devices found"
fi
echo ""

# Port checks
echo "=== Network Ports ==="
echo "  Port 7880 (LiveKit): $(netstat -ln 2>/dev/null | grep -q ':7880 ' && echo '✅ Listening' || echo '❌ Not listening')"
echo "  Port 8000 (API):     $(netstat -ln 2>/dev/null | grep -q ':8000 ' && echo '✅ Listening' || echo '❌ Not listening')"
echo ""

# Quick recommendations
echo "=== Quick Actions ==="
echo "  View API logs:      tail -f /tmp/uuplastination-api.log"
echo "  View LiveKit logs:  docker logs -f livekit"
echo "  Start services:     ./start_services.sh"
echo "  Stop services:      ./stop_services.sh"
echo "  Dashboard:          http://127.0.0.1:8000/"
echo ""
echo "======================================"
