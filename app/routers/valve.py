from __future__ import annotations

"""Valve control (one-way serial).

This router implements a WRITE-ONLY protocol to a microcontroller that listens
on a serial device (default: /dev/ttyACM0). The Raspberry Pi sends single
characters 'r' and 'l' (configurable) to indicate valve motion commands. No
response is expected; there is intentionally NO read/parsing logic here.

If future two-way communication is added, a read loop or async background task
could be introduced without changing the outward-facing API.
"""

import os
import time
from typing import Dict, Optional

from fastapi import APIRouter, HTTPException

try:  # pragma: no cover - import may fail off-device
    import serial  # type: ignore
except Exception:  # pragma: no cover
    serial = None  # type: ignore

router = APIRouter(prefix="/api/valve", tags=["valve"])

# --- Configuration ---------------------------------------------------------
DEVICE_PATH = os.getenv("VALVE_SERIAL_DEVICE", "/dev/ttyACM0")  # ensure spelling: ACM not AMC
BAUD_RATE = int(os.getenv("VALVE_SERIAL_BAUD", "115200"))
WRITE_TIMEOUT = float(os.getenv("VALVE_WRITE_TIMEOUT", "0.25"))  # lower for snappier failures
OPEN_CHAR = os.getenv("VALVE_OPEN_CHAR", "r")
CLOSE_CHAR = os.getenv("VALVE_CLOSE_CHAR", "l")

_valve_position = int(os.getenv("VALVE_START_PERCENT", "50"))  # purely virtual feedback
STEP_PERCENT = int(os.getenv("VALVE_STEP_PERCENT", "5"))
REPORT_POSITION = os.getenv("VALVE_REPORT_POSITION", "1") not in ("0", "false", "False")

def _send_char(ch: str) -> None:
    """Write a single character to the serial port. Opens, writes, closes immediately.
    This ensures we don't hold the port open and avoids 'device busy' errors.
    """
    if serial is None:
        raise HTTPException(status_code=500, detail="pyserial not installed")
    
    ser = None
    try:
        # Open with exclusive access, write immediately, close
        # timeout=0 means non-blocking (we never read)
        ser = serial.Serial(
            DEVICE_PATH,
            BAUD_RATE,
            timeout=0,
            write_timeout=WRITE_TIMEOUT,
            exclusive=True,  # Prevent other processes from opening simultaneously
        )
        time.sleep(0.01)  # Brief settle time
        ser.write(ch.encode("utf-8"))
        ser.flush()  # Ensure data is transmitted before closing
    except serial.SerialException as e:
        if "busy" in str(e).lower():
            raise HTTPException(
                status_code=503, 
                detail=f"Serial port {DEVICE_PATH} is busy. Close other applications using this port."
            )
        raise HTTPException(status_code=503, detail=f"Serial error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write to serial: {e}")
    finally:
        if ser and ser.is_open:
            try:
                ser.close()
            except Exception:
                pass  # Best effort cleanup

@router.get("/health")
def valve_health() -> Dict[str, object]:
    """Report usability of the serial device without implying responses."""
    if serial is None:
        raise HTTPException(status_code=500, detail="pyserial not installed")
    
    ser = None
    try:
        # Quick test: open and close to verify port is accessible
        ser = serial.Serial(
            DEVICE_PATH,
            BAUD_RATE,
            timeout=0,
            write_timeout=WRITE_TIMEOUT,
            exclusive=True,
        )
        result = {
            "device": DEVICE_PATH,
            "accessible": True,
            "baud": BAUD_RATE,
            "one_way": True,
        }
        ser.close()
        return result
    except serial.SerialException as e:
        if "busy" in str(e).lower():
            raise HTTPException(
                status_code=503, 
                detail=f"Port {DEVICE_PATH} is busy. Check: lsof {DEVICE_PATH}"
            )
        raise HTTPException(status_code=503, detail=f"Serial error: {e}")
    except Exception as e:  # pragma: no cover
        raise HTTPException(status_code=503, detail=str(e))
    finally:
        if ser and ser.is_open:
            try:
                ser.close()
            except Exception:
                pass

@router.get("/position")
def valve_position() -> Dict[str, Optional[int]]:
    if not REPORT_POSITION:
        return {"position": None}
    return {"position": _valve_position}

@router.post("/open")
def valve_open() -> Dict[str, object]:
    global _valve_position
    if REPORT_POSITION:
        _valve_position = min(100, _valve_position + STEP_PERCENT)
    _send_char(OPEN_CHAR)
    return {
        "result": "open-sent",
        "char": OPEN_CHAR,
        "position": _valve_position if REPORT_POSITION else None,
    }

@router.post("/close")
def valve_close() -> Dict[str, object]:
    global _valve_position
    if REPORT_POSITION:
        _valve_position = max(0, _valve_position - STEP_PERCENT)
    _send_char(CLOSE_CHAR)
    return {
        "result": "close-sent",
        "char": CLOSE_CHAR,
        "position": _valve_position if REPORT_POSITION else None,
    }

@router.post("/raw")
def valve_raw(char: str) -> Dict[str, object]:
    if len(char) != 1:
        raise HTTPException(status_code=400, detail="char must be a single character")
    _send_char(char)
    return {"result": "raw-sent", "char": char}

