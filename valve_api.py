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
serial_lock = threading.Lock()


def init_serial() -> None:
    """Try to (re)initialize the serial connection."""
    global serial_conn

    # If it's already open, don't reopen
    if serial_conn and serial_conn.is_open:
        return

    try:
        ser = serial.Serial(
            port=SERIAL_PORT,
            baudrate=BAUD_RATE,
            timeout=1.0,
        )
        # Arduino resets when the port opens, give it time
        time.sleep(2)
        ser.reset_input_buffer()
        ser.reset_output_buffer()

        serial_conn = ser
        print(f"✓ Serial connected to {SERIAL_PORT} @ {BAUD_RATE}")
    except Exception as e:
        print(f"✗ Serial connection failed: {e}")
        serial_conn = None


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


@router.get("/api/valve/status")
async def valve_status():
    """
    Check whether the Arduino serial connection is available.

    Does NOT throw, just reports connected / not connected.
    """
    with serial_lock:
        try:
            # Try to get a live port; will attempt reconnect
            ser = get_serial()
            return {
                "connected": True,
                "port": SERIAL_PORT,
                "baud_rate": BAUD_RATE,
                "is_open": ser.is_open,
            }
        except HTTPException as e:
            # Swallow into a friendly JSON status
            return {
                "connected": False,
                "port": SERIAL_PORT,
                "baud_rate": BAUD_RATE,
                "error": e.detail,
            }


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
