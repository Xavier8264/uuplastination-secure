"""
Simple valve control - just sends 'r' or 'l' to /dev/ttyACM0
"""

from fastapi import APIRouter
import serial

router = APIRouter()

SERIAL_PORT = "/dev/ttyACM0"
BAUD_RATE = 115200


@router.post("/api/valve/open")
async def open_valve():
    """Send 'r' to serial port."""
    try:
        with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1) as ser:
            ser.write(b"r")
            ser.flush()
    except Exception:
        pass  # Ignore errors, just try to send
    return "OK"


@router.post("/api/valve/close")
async def close_valve():
    """Send 'l' to serial port."""
    try:
        with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1) as ser:
            ser.write(b"l")
            ser.flush()
    except Exception:
        pass  # Ignore errors, just try to send
    return "OK"
