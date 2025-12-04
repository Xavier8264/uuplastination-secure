"""Simple valve control API - sends 'r' and 'l' through serial port.

This API sends single characters to /dev/ttyACM0 based on button presses:
- 'r' for open valve
- 'l' for close valve

One-way communication only - no reading from the serial port.
The serial port is kept open indefinitely for better performance.
"""

import os
import atexit

from fastapi import APIRouter, BackgroundTasks, HTTPException

try:
    import serial
except ImportError:
    serial = None

router = APIRouter(prefix="/api/valve", tags=["valve"])

# Configuration
DEVICE_PATH = "/dev/ttyACM0"
BAUD_RATE = int(os.getenv("VALVE_SERIAL_BAUD", "115200"))
WRITE_TIMEOUT = 0.5

# Global serial connection - kept open indefinitely
_serial_connection = None

def _get_serial_connection():
    """Get or create the persistent serial connection."""
    global _serial_connection
    
    if serial is None:
        raise HTTPException(status_code=500, detail="pyserial not installed")
    
    # If connection exists and is open, return it
    if _serial_connection is not None and _serial_connection.is_open:
        return _serial_connection
    
    # Create new connection
    try:
        _serial_connection = serial.Serial(
            DEVICE_PATH,
            BAUD_RATE,
            timeout=0,
            write_timeout=WRITE_TIMEOUT,
            exclusive=True  # Ensure exclusive access
        )
        return _serial_connection
    except serial.SerialException as e:
        error_msg = str(e).lower()
        if "busy" in error_msg or "permission denied" in error_msg or "resource busy" in error_msg:
            raise HTTPException(status_code=503, detail=f"Serial port busy: {e}")
        raise HTTPException(status_code=500, detail=f"Serial error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")

def _close_serial_connection():
    """Close the serial connection on shutdown."""
    global _serial_connection
    if _serial_connection is not None and _serial_connection.is_open:
        try:
            _serial_connection.close()
        except Exception:
            pass

# Register cleanup on exit
atexit.register(_close_serial_connection)

def _send_char(ch: str) -> None:
    """Send a single character through the persistent serial port."""
    try:
        ser = _get_serial_connection()
        ser.write(ch.encode("utf-8"))
        ser.flush()
    except serial.SerialException as e:
        # Connection might have been lost, try to reconnect
        global _serial_connection
        _serial_connection = None
        error_msg = str(e).lower()
        if "busy" in error_msg or "permission denied" in error_msg or "resource busy" in error_msg:
            raise HTTPException(status_code=503, detail=f"Serial port busy: {e}")
        raise HTTPException(status_code=500, detail=f"Serial error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")

@router.post("/open")
def valve_open(background_tasks: BackgroundTasks) -> str:
    """Send 'r' character to open the valve without waiting for a response."""

    def _write_open():
        try:
            _send_char("r")
        except Exception as exc:  # noqa: BLE001 - log and swallow to keep one-way behavior
            # Best-effort fire-and-forget; log for diagnostics without surfacing errors to the client.
            print(f"[valve] open write failed: {exc}", flush=True)

    background_tasks.add_task(_write_open)
    return "OK"

@router.post("/close")
def valve_close(background_tasks: BackgroundTasks) -> str:
    """Send 'l' character to close the valve without waiting for a response."""

    def _write_close():
        try:
            _send_char("l")
        except Exception as exc:  # noqa: BLE001 - log and swallow to keep one-way behavior
            print(f"[valve] close write failed: {exc}", flush=True)

    background_tasks.add_task(_write_close)
    return "OK"
