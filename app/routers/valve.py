from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
import time
import threading
import os
from typing import List, Dict

import serial
from serial.serialutil import SerialException

SERIAL_PORT = "/dev/ttyACM0"
BAUD_RATE = 115200

router = APIRouter(prefix="/api/valve", tags=["valve"])

serial_lock = threading.Lock()
ser = None


def get_serial():
    """Lazily open and return the serial port. Raise SerialException if it fails."""
    global ser
    try:
        if ser is not None and getattr(ser, 'is_open', False):
            return ser
    except Exception:
        # fall through and try to reopen
        pass

    try:
        s = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    except SerialException:
        # propagate to caller
        raise

    # Give Arduino time to reset after serial open
    time.sleep(2)
    ser = s
    return ser


class MoveRequest(BaseModel):
    units: int

# --- Security & Rate Limiting -------------------------------------------
_VALVE_TOKEN = os.getenv("VALVE_API_TOKEN")  # configure in environment; if unset, auth disabled
_recent_requests: List[float] = []
_RATE_WINDOW_SEC = 5.0
_RATE_MAX_EVENTS = 15
_valve_position = 45  # virtual percentage position

def _security_check(request: Request):
    if _VALVE_TOKEN:
        hdr = request.headers.get("X-Auth-Token")
        if hdr != _VALVE_TOKEN:
            raise HTTPException(status_code=401, detail="unauthorized")
        # Same-origin guard (basic CSRF mitigation)
        origin = request.headers.get("Origin") or ""
        referer = request.headers.get("Referer") or ""
        if origin:
            host = f"{request.url.scheme}://{request.url.netloc}"
            if origin != host:
                raise HTTPException(status_code=403, detail="bad origin")
        if referer:
            host = f"{request.url.scheme}://{request.url.netloc}"
            if not referer.startswith(host):
                raise HTTPException(status_code=403, detail="bad referer")

def _rate_limit():
    now = time.time()
    while _recent_requests and now - _recent_requests[0] > _RATE_WINDOW_SEC:
        _recent_requests.pop(0)
    _recent_requests.append(now)
    if len(_recent_requests) > _RATE_MAX_EVENTS:
        raise HTTPException(status_code=429, detail="rate limited")

# --- Low-level serial helper --------------------------------------------
_char_lock = threading.Lock()

def _send_char(ch: str):
    if ch not in ("r", "l"):
        raise HTTPException(status_code=400, detail="invalid command")
    try:
        with _char_lock:
            s = get_serial()
            s.write(ch.encode("ascii"))
            s.flush()
    except SerialException as e:
        raise HTTPException(status_code=503, detail=f"Serial port error on {SERIAL_PORT}: {e}")
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Serial communication error: {e}")


@router.post("/move")
def move_valve(req: MoveRequest, request: Request = Depends()):
    _security_check(request)
    _rate_limit()
    # units must be non-zero
    if req.units == 0:
        raise HTTPException(status_code=400, detail="units must be non-zero")

    cmd = f"MOVE {req.units}\n"

    try:
        with serial_lock:
            s = get_serial()
            # clear any pending input
            s.reset_input_buffer()
            s.write(cmd.encode("ascii"))
            s.flush()
            raw = s.readline()
            line = raw.decode(errors="ignore").strip() if raw else ""
    except SerialException as e:
        raise HTTPException(status_code=503, detail=f"Serial port error on {SERIAL_PORT}: {e}")
    except Exception as e:
        # Any other serial/IO error
        raise HTTPException(status_code=503, detail=f"Serial communication error: {e}")

    return {
        "status": "ok",
        "sent_command": cmd.strip(),
        "arduino_reply": line,
        "position": _valve_position,
    }


@router.post("/open")
def valve_open(request: Request) -> Dict[str, object]:
    """Clockwise step via Arduino: send 'r' and increment virtual position."""
    _security_check(request)
    _rate_limit()
    global _valve_position
    _send_char("r")
    _valve_position = min(100, _valve_position + 5)
    return {"result": "opened", "position": _valve_position}


@router.post("/close")
def valve_close(request: Request) -> Dict[str, object]:
    """Counter‑clockwise step via Arduino: send 'l' and decrement virtual position."""
    _security_check(request)
    _rate_limit()
    global _valve_position
    _send_char("l")
    _valve_position = max(0, _valve_position - 5)
    return {"result": "closed", "position": _valve_position}


@router.get("/position")
def valve_position() -> Dict[str, object]:
    return {"position": _valve_position}
