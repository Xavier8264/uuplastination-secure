from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import time
import threading

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


@router.post("/move")
def move_valve(req: MoveRequest):
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
    }
