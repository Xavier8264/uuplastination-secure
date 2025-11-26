#!/bin/bash
# Quick API status check script

echo "========================================="
echo "UU Plastination API Status Check"
echo "========================================="
echo ""

echo "1. Service Status:"
systemctl is-active uuplastination-api && echo "   ✓ Service is ACTIVE" || echo "   ✗ Service is NOT running"
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
if ss -tuln | grep -q ":8000 "; then
    echo "   ✓ Port 8000 is listening"
else
    echo "   ✗ Port 8000 is NOT listening"
fi
echo ""

echo "4. API Endpoint Tests:"
echo "   Testing /api/valve/open..."
OPEN_RESP=$(curl -s -X POST http://127.0.0.1:8000/api/valve/open 2>&1)
if [ "$OPEN_RESP" = '"OK"' ]; then
    echo "   ✓ Valve OPEN: $OPEN_RESP"
else
    echo "   ✗ Valve OPEN failed: $OPEN_RESP"
fi

echo "   Testing /api/valve/close..."
CLOSE_RESP=$(curl -s -X POST http://127.0.0.1:8000/api/valve/close 2>&1)
if [ "$CLOSE_RESP" = '"OK"' ]; then
    echo "   ✓ Valve CLOSE: $CLOSE_RESP"
else
    echo "   ✗ Valve CLOSE failed: $CLOSE_RESP"
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
sudo journalctl -u uuplastination-api -n 5 --no-pager | grep -v "^--" | sed 's/^/   /'
echo ""

echo "========================================="
echo "Status check complete"
echo "========================================="
