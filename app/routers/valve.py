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

_ser: Optional['serial.Serial'] = None  # cached handle

def _ensure_serial() -> 'serial.Serial':
    if serial is None:
        raise HTTPException(status_code=500, detail="pyserial not installed")
    global _ser
    if _ser and _ser.is_open:
        return _ser
    try:
        # timeout=0 -> non-blocking reads (we don't read); write_timeout enforced
        _ser = serial.Serial(
            DEVICE_PATH,
            BAUD_RATE,
            timeout=0,
            write_timeout=WRITE_TIMEOUT,
        )
        time.sleep(0.02)  # tiny settle; some boards need a moment after opening
        return _ser
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"serial unavailable: {e}")

def _send_char(ch: str) -> None:
    ser = _ensure_serial()
    try:
        ser.write(ch.encode("utf-8"))
        # no flush needed; pyserial writes directly; flush() optional
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"serial write failed: {e}")

@router.get("/health")
def valve_health() -> Dict[str, object]:
    """Report usability of the serial device without implying responses."""
    try:
        ser = _ensure_serial()
        return {
            "device": DEVICE_PATH,
            "open": bool(ser.is_open),
            "baud": BAUD_RATE,
            "one_way": True,
        }
    except HTTPException as e:
        raise e
    except Exception as e:  # pragma: no cover
        raise HTTPException(status_code=503, detail=str(e))

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

