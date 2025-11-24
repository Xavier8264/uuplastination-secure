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

# Global serial connection (kept open forever)
serial_conn: Optional[serial.Serial] = None
serial_lock = threading.Lock()


def init_serial():
    """Initialize serial connection on startup"""
    global serial_conn
    try:
        serial_conn = serial.Serial(
            port=SERIAL_PORT,
            baudrate=BAUD_RATE,
            timeout=1.0
        )
        print(f"✓ Serial connected to {SERIAL_PORT}")
        time.sleep(2)  # Wait for Arduino to reset
        serial_conn.reset_input_buffer()
        serial_conn.reset_output_buffer()
    except Exception as e:
        print(f"✗ Serial connection failed: {e}")
        serial_conn = None


# Initialize on module load
init_serial()


@router.post("/api/valve/open")
async def open_valve():
    """Send 'r' to Arduino"""
    with serial_lock:
        if not serial_conn or not serial_conn.is_open:
            raise HTTPException(status_code=503, detail="Serial port not connected")
        
        try:
            serial_conn.write(b'r')
            serial_conn.flush()
            return {"status": "ok", "command": "r", "action": "open"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Serial error: {str(e)}")


@router.post("/api/valve/close")
async def close_valve():
    """Send 'l' to Arduino"""
    with serial_lock:
        if not serial_conn or not serial_conn.is_open:
            raise HTTPException(status_code=503, detail="Serial port not connected")
        
        try:
            serial_conn.write(b'l')
            serial_conn.flush()
            return {"status": "ok", "command": "l", "action": "close"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Serial error: {str(e)}")


@router.get("/api/valve/status")
async def valve_status():
    """Check if Arduino serial connection is available"""
    try:
        with serial_lock:
            ser = get_serial()
            return {
                "connected": ser.is_open,
                "port": SERIAL_PORT,
                "baud_rate": BAUD_RATE
            }
    except HTTPException as e:
        return {
            "connected": False,
            "port": SERIAL_PORT,
            "error": e.detail
        }


# Cleanup on shutdown
def cleanup():
    """Close serial connection on shutdown"""
    global serial_conn
    if serial_conn and serial_conn.is_open:
        try:
            serial_conn.close()
        except:
            pass
