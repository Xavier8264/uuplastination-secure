"""Simple valve control API - sends 'r' and 'l' through serial port.

This API sends single characters to /dev/ttyACM0 based on button presses:
- 'r' for open valve
- 'l' for close valve

One-way communication only - no reading from the serial port.
"""

import os

from fastapi import APIRouter, HTTPException

try:
    import serial
except ImportError:
    serial = None

router = APIRouter(prefix="/api/valve", tags=["valve"])

# Configuration
DEVICE_PATH = "/dev/ttyACM0"
BAUD_RATE = int(os.getenv("VALVE_SERIAL_BAUD", "115200"))
WRITE_TIMEOUT = 0.5

def _send_char(ch: str) -> None:
    """Send a single character through the serial port with exclusive access."""
    if serial is None:
        raise HTTPException(status_code=500, detail="pyserial not installed")
    
    ser = None
    try:
        # Open with exclusive flag to ensure only one connection
        ser = serial.Serial(
            DEVICE_PATH,
            BAUD_RATE,
            timeout=0,
            write_timeout=WRITE_TIMEOUT,
            exclusive=True  # Ensure exclusive access
        )
        ser.write(ch.encode("utf-8"))
        ser.flush()
    except serial.SerialException as e:
        error_msg = str(e).lower()
        if "busy" in error_msg or "permission denied" in error_msg or "resource busy" in error_msg:
            raise HTTPException(status_code=503, detail=f"Serial port busy: {e}")
        raise HTTPException(status_code=500, detail=f"Serial error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")
    finally:
        if ser and ser.is_open:
            try:
                ser.close()
            except Exception:
                pass

@router.post("/open")
def valve_open() -> str:
    """Send 'r' character to open the valve."""
    _send_char("r")
    return "OK"

@router.post("/close")
def valve_close() -> str:
    """Send 'l' character to close the valve."""
    _send_char("l")
    return "OK"
