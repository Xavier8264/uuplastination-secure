from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import serial
import time
import threading

# Adjust this to match your Arduino device:
#   ls /dev/ttyACM*  or  ls /dev/ttyUSB*
SERIAL_PORT = "/dev/ttyACM0"
BAUD_RATE = 115200

app = FastAPI()

serial_lock = threading.Lock()
ser = None


def init_serial():
    global ser
    if ser is None:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        # give Arduino time to reset after opening
        time.sleep(2)


class MoveRequest(BaseModel):
    units: int  # positive or negative integer


@app.on_event("startup")
def on_startup():
    init_serial()


@app.post("/api/valve/move")
def move_valve(req: MoveRequest):
    if req.units == 0:
        raise HTTPException(status_code=400, detail="units must be non-zero")

    cmd = f"MOVE {req.units}\n"

    with serial_lock:
        ser.reset_input_buffer()
        ser.write(cmd.encode("ascii"))
        ser.flush()
        # optional readback from Arduino
        reply = ser.readline().decode(errors="ignore").strip()

    return {
        "status": "ok",
        "sent_command": cmd.strip(),
        "arduino_reply": reply,
    }
