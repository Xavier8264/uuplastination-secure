"""
Simple valve control via Arduino serial communication.
Open button → sends 'r'
Close button → sends 'l'

Replace your existing app/routers/valve.py with this file.
"""

from fastapi import APIRouter, HTTPException
import serial
import threading
import time
from typing import Optional

router = APIRouter()

# Serial configuration
SERIAL_PORT = "/dev/ttyACM0"
BAUD_RATE = 115200

# Global serial connection (kept open as long as possible)
serial_conn: Optional[serial.Serial] = None

# --- Thread Safety for Serial Connection -------------------------------------
serial_lock = threading.Lock()

# --- Improved Connection Initialization ---------------------------------------
def init_serial() -> None:
    """Try to (re)initialize the serial connection with retries."""
    global serial_conn
    retries = 5
    for attempt in range(retries):
        if serial_conn and serial_conn.is_open:
            return
        try:
            ser = serial.Serial(
                port=SERIAL_PORT,
                baudrate=BAUD_RATE,
                timeout=1.0,
            )
            time.sleep(2)  # Allow Arduino to reset
            serial_conn = ser
            print(f"\u2713 Serial connected to {SERIAL_PORT} @ {BAUD_RATE}")
            return
        except Exception as e:
            print(f"\u2717 Serial connection attempt {attempt + 1} failed: {e}")
            time.sleep(2 ** attempt)  # Exponential backoff
    serial_conn = None
    raise RuntimeError(f"Failed to connect to serial port {SERIAL_PORT} after {retries} attempts")


def get_serial() -> serial.Serial:
    """
    Get a live serial connection or raise HTTP 503.

    This will attempt to (re)initialize the port if it's not open.
    """
    init_serial()
    if not serial_conn or not serial_conn.is_open:
        raise HTTPException(
            status_code=503,
            detail=f"Serial port {SERIAL_PORT} not connected",
        )
    return serial_conn


@router.post("/api/valve/open")
async def open_valve():
    """Send 'r' to Arduino (open valve)."""
    with serial_lock:
        ser = get_serial()
        try:
            ser.write(b"r")
            ser.flush()
            return {"status": "ok", "command": "r", "action": "open"}
        except Exception as e:
            # Force close so the next call can try to reconnect
            try:
                ser.close()
            except Exception:
                pass
            raise HTTPException(status_code=500, detail=f"Serial error: {str(e)}")


@router.post("/api/valve/close")
async def close_valve():
    """Send 'l' to Arduino (close valve)."""
    with serial_lock:
        ser = get_serial()
        try:
            ser.write(b"l")
            ser.flush()
            return {"status": "ok", "command": "l", "action": "close"}
        except Exception as e:
            # Force close so the next call can try to reconnect
            try:
                ser.close()
            except Exception:
                pass
            raise HTTPException(status_code=500, detail=f"Serial error: {str(e)}")


def cleanup() -> None:
    """Close serial connection on shutdown."""
    global serial_conn
    if serial_conn and serial_conn.is_open:
        try:
            print("Closing serial connection...")
            serial_conn.close()
        except Exception:
            pass
        finally:
            serial_conn = None
