from __future__ import annotations

import os
import time
from typing import Dict, Optional

from fastapi import APIRouter, HTTPException

try:
    import serial  # type: ignore
except Exception:  # pragma: no cover
    serial = None  # type: ignore

router = APIRouter(prefix="/api/valve", tags=["valve"])

DEVICE_PATH = os.getenv("VALVE_SERIAL_DEVICE", "/dev/ttyACM0")
BAUD_RATE = int(os.getenv("VALVE_SERIAL_BAUD", "115200"))
WRITE_TIMEOUT = float(os.getenv("VALVE_WRITE_TIMEOUT", "0.5"))
OPEN_CHAR = os.getenv("VALVE_OPEN_CHAR", "r")  # character to open (e.g. rotate right)
CLOSE_CHAR = os.getenv("VALVE_CLOSE_CHAR", "l")  # character to close (e.g. rotate left)

# Maintain virtual position percentage for UI feedback only
_valve_position = int(os.getenv("VALVE_START_PERCENT", "50"))
STEP_PERCENT = int(os.getenv("VALVE_STEP_PERCENT", "5"))

_ser: Optional['serial.Serial'] = None  # lazy initialized

def _ensure_serial() -> 'serial.Serial':
    if serial is None:
        raise HTTPException(status_code=500, detail="pyserial not installed")
    global _ser
    if _ser and _ser.is_open:
        return _ser
    try:
        _ser = serial.Serial(DEVICE_PATH, BAUD_RATE, timeout=1, write_timeout=WRITE_TIMEOUT)
        time.sleep(0.05)  # small settle delay
        return _ser
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"serial unavailable: {e}")

def _send_char(ch: str) -> None:
    ser = _ensure_serial()
    try:
        ser.write(ch.encode('utf-8'))
        ser.flush()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"serial write failed: {e}")

@router.get("/health")
def valve_health() -> Dict[str, object]:
    try:
        ser = _ensure_serial()
        return {"device": DEVICE_PATH, "open": ser.is_open, "baud": BAUD_RATE}
    except HTTPException as e:  # propagate structured error
        raise e
    except Exception as e:  # pragma: no cover
        raise HTTPException(status_code=503, detail=str(e))

@router.get("/position")
def valve_position() -> Dict[str, int]:
    return {"position": _valve_position}

@router.post("/open")
def valve_open() -> Dict[str, object]:
    global _valve_position
    _valve_position = min(100, _valve_position + STEP_PERCENT)
    _send_char(OPEN_CHAR)
    return {"result": "open-sent", "char": OPEN_CHAR, "position": _valve_position}

@router.post("/close")
def valve_close() -> Dict[str, object]:
    global _valve_position
    _valve_position = max(0, _valve_position - STEP_PERCENT)
    _send_char(CLOSE_CHAR)
    return {"result": "close-sent", "char": CLOSE_CHAR, "position": _valve_position}

@router.post("/raw")
def valve_raw(char: str) -> Dict[str, object]:
    if len(char) != 1:
        raise HTTPException(status_code=400, detail="char must be a single character")
    _send_char(char)
    return {"result": "raw-sent", "char": char}

