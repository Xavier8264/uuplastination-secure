"""Simple valve control API - sends 'r' and 'l' through serial port.

This API sends single characters to /dev/ttyACM0 based on button presses:
- 'r' for open valve
- 'l' for close valve

One-way communication only - no reading from the serial port.
The serial port is kept open indefinitely for better performance.
"""

import os
import atexit

from fastapi import APIRouter, BackgroundTasks

try:
    import serial
except ImportError:
    serial = None

router = APIRouter(prefix="/api/valve", tags=["valve"])

# Configuration
DEVICE_PATH = os.getenv("VALVE_SERIAL_DEVICE", "/dev/ttyACM0")
BAUD_RATE = int(os.getenv("VALVE_SERIAL_BAUD", "115200"))
WRITE_TIMEOUT = 0.5

# Global serial connection - kept open indefinitely
_serial_connection = None

def _get_serial_connection():
    """Get or create the persistent serial connection."""
    global _serial_connection
    
    if serial is None:
        print("[valve] pyserial not installed; skipping serial write", flush=True)
        return None
    
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
    except Exception as e:
        # Best-effort: log and return None so we never raise to the client.
        print(f"[valve] failed to open serial {DEVICE_PATH}: {e}", flush=True)
        _serial_connection = None
        return None

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
    """Send a single character through the persistent serial port (best effort)."""
    ser = _get_serial_connection()
    if ser is None:
        print(f"[valve] no serial connection; skipped write '{ch}'", flush=True)
        return

    try:
        ser.write(ch.encode("utf-8"))
        ser.flush()
    except Exception as e:  # Swallow errors to keep API one-way OK
        global _serial_connection
        _serial_connection = None
        print(f"[valve] write failed, clearing connection: {e}", flush=True)

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
