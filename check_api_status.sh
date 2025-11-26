#!/bin/bash
# Quick API status check script

echo "========================================="
echo "UU Plastination API Status Check"
echo "========================================="
echo ""

echo "1. Service Status:"
if systemctl is-active uuplastination-api >/dev/null; then
    echo "   ✓ Service is ACTIVE"
else
    echo "   ✗ Service is NOT running"
    systemctl status uuplastination-api --no-pager | head -10 | sed 's/^/   /'
fi
echo ""

echo "2. Process Check:"
if ps aux | grep -q "[u]vicorn app.main:app"; then
    echo "   ✓ Uvicorn process running"
    ps aux | grep "[u]vicorn app.main:app" | awk '{print "   PID: " $2 " | CPU: " $3 "% | MEM: " $4 "%"}'
else
    echo "   ✗ No uvicorn process found"
fi
echo ""

echo "3. Port 8000 Check:"
echo "3. Port 8899 Check:"
if ss -tuln | grep -q ":8899 "; then
    echo "   ✓ Port 8899 is listening"
else
    echo "   ✗ Port 8899 is NOT listening"
fi
echo ""

echo "4. API Endpoint Tests:"
API_PORT=8899
API_URL="http://127.0.0.1:$API_PORT"
echo "   Testing /api/valve/open..."
OPEN_RESP=$(curl -s --max-time 3 -X POST "$API_URL/api/valve/open" -w "%{http_code}" -o /tmp/open_resp.txt)
OPEN_BODY=$(cat /tmp/open_resp.txt)
if [ "$OPEN_RESP" = "200" ] && [ "$OPEN_BODY" = '"OK"' ]; then
    echo "   ✓ Valve OPEN: $OPEN_BODY"
else
    echo "   ✗ Valve OPEN failed: HTTP $OPEN_RESP, Body: $OPEN_BODY"
fi

echo "   Testing /api/valve/close..."
CLOSE_RESP=$(curl -s --max-time 3 -X POST "$API_URL/api/valve/close" -w "%{http_code}" -o /tmp/close_resp.txt)
CLOSE_BODY=$(cat /tmp/close_resp.txt)
if [ "$CLOSE_RESP" = "200" ] && [ "$CLOSE_BODY" = '"OK"' ]; then
    echo "   ✓ Valve CLOSE: $CLOSE_BODY"
else
    echo "   ✗ Valve CLOSE failed: HTTP $CLOSE_RESP, Body: $CLOSE_BODY"
fi
echo ""

echo "5. Serial Port:"
if [ -e /dev/ttyACM0 ]; then
    echo "   ✓ /dev/ttyACM0 exists"
    ls -l /dev/ttyACM0 | awk '{print "   Permissions: " $1 " | Owner: " $3 ":" $4}'
    if groups | grep -q dialout; then
        echo "   ✓ Current user in dialout group"
    else
        echo "   ✗ Current user NOT in dialout group"
    fi
else
    echo "   ✗ /dev/ttyACM0 NOT found"
fi
echo ""

echo "6. Recent Logs:"
echo "   Last 5 log entries:"
if command -v journalctl >/dev/null; then
    if [ "$EUID" -eq 0 ]; then
        journalctl -u uuplastination-api -n 5 --no-pager | grep -v "^--" | sed 's/^/   /'
    else
        journalctl -u uuplastination-api -n 5 --no-pager | grep -v "^--" | sed 's/^/   /' 2>/dev/null || echo "   (Insufficient permissions for logs)"
    fi
else
    echo "   journalctl not found"
fi
echo ""

echo "========================================="
echo "Status check complete"
echo "========================================="
