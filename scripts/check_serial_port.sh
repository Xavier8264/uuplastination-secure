#!/bin/bash
# Quick diagnostic script for /dev/ttyACM0

DEVICE="${1:-/dev/ttyACM0}"

echo "=== Serial Port Diagnostic: $DEVICE ==="
echo ""

if [ ! -e "$DEVICE" ]; then
    echo "❌ Device does not exist: $DEVICE"
    echo "Available serial devices:"
    ls -la /dev/tty* 2>/dev/null | grep -E "(ACM|USB)" || echo "  None found"
    exit 1
fi

echo "✅ Device exists: $DEVICE"
ls -la "$DEVICE"
echo ""

echo "Current user: $(whoami)"
echo "Groups: $(groups)"
echo ""

if groups | grep -q dialout; then
    echo "✅ User is in 'dialout' group (can access serial ports)"
else
    echo "❌ User is NOT in 'dialout' group"
    echo "   Fix: sudo usermod -aG dialout $(whoami) && newgrp dialout"
fi
echo ""

echo "Processes using $DEVICE:"
if lsof "$DEVICE" 2>/dev/null; then
    echo ""
    echo "⚠️  Port is BUSY! Close the above processes before using the valve API."
    echo "   Common culprits: Arduino IDE, PlatformIO, screen, minicom, other Python scripts"
else
    echo "✅ Port is available (not in use)"
fi
echo ""

echo "Testing write access..."
if python3 -c "import serial; s = serial.Serial('$DEVICE', 115200, timeout=0, write_timeout=0.25, exclusive=True); s.write(b'test'); s.close(); print('✅ SUCCESS: Can write to $DEVICE')" 2>&1; then
    :
else
    echo "❌ FAILED to write to $DEVICE"
fi

echo ""
echo "=== End Diagnostic ==="
