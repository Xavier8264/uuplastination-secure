from __future__ import annotations

import os
from typing import Dict

from fastapi import APIRouter, HTTPException

# Reuse stepper controller and constants
from .stepper import _controller, OPEN_STEPS, CLOSE_STEPS

router = APIRouter(prefix="/api/valve", tags=["valve"])

# Percentage-based virtual valve position
_valve_position = int(os.getenv("VALVE_START_PERCENT", "45"))

STEP_PERCENT = int(os.getenv("VALVE_STEP_PERCENT", "5"))  # percent change per open/close

@router.post("/open")
def valve_open() -> Dict[str, int]:
    global _valve_position
    _valve_position = min(100, _valve_position + STEP_PERCENT)
    try:
        # map percent change to proportional step amount
        step_count = int(OPEN_STEPS * (STEP_PERCENT / 100.0))
        if step_count > 0:
            _controller.step(steps=step_count, rpm=None, forward=True)
    except RuntimeError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return {"result": "opened", "position": _valve_position}

@router.post("/close")
def valve_close() -> Dict[str, int]:
    global _valve_position
    _valve_position = max(0, _valve_position - STEP_PERCENT)
    try:
        step_count = int(abs(CLOSE_STEPS) * (STEP_PERCENT / 100.0))
        if step_count > 0:
            _controller.step(steps=step_count, rpm=None, forward=False)
    except RuntimeError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return {"result": "closed", "position": _valve_position}

@router.get("/position")
def valve_position() -> Dict[str, int]:
    return {"position": _valve_position}
