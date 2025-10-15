from __future__ import annotations

import os
import threading
import time
from typing import Dict, Optional

from fastapi import APIRouter, HTTPException, Query


router = APIRouter(prefix="/api/stepper", tags=["stepper"])


# --- GPIO abstraction -------------------------------------------------------
try:
    import RPi.GPIO as GPIO  # type: ignore
except Exception:  # pragma: no cover - not on dev machine
    GPIO = None  # type: ignore


class _GPIOLike:
    BCM = 0
    OUT = 0
    HIGH = 1
    LOW = 0

    def setmode(self, *_args, **_kwargs):
        pass

    def setwarnings(self, *_args, **_kwargs):
        pass

    def setup(self, *_args, **_kwargs):
        pass

    def output(self, *_args, **_kwargs):
        pass

    def cleanup(self, *_args, **_kwargs):
        pass


GPIO_IF = GPIO if GPIO is not None else _GPIOLike()  # type: ignore


# --- Controller -------------------------------------------------------------
class StepperController:
    """Very small A4988/DRV8825 style controller using STEP/DIR/ENABLE.

    Not real-time precise, but adequate for manual control via web UI.
    """

    def __init__(
        self,
        pin_step: int,
        pin_dir: int,
        pin_enable: Optional[int] = None,
        steps_per_rev: int = 200,
        default_rpm: float = 60.0,
        invert_enable: bool = True,
        duty_cycle: float = 0.5,
    ) -> None:
        self.pin_step = pin_step
        self.pin_dir = pin_dir
        self.pin_enable = pin_enable
        self.steps_per_rev = steps_per_rev
        self.default_rpm = default_rpm
        self.invert_enable = invert_enable
        self.duty_cycle = min(max(duty_cycle, 0.05), 0.95)

        self._lock = threading.Lock()
        self._worker: Optional[threading.Thread] = None
        self._abort = threading.Event()
        self.enabled = False
        self.moving = False
        self.position = 0  # arbitrary units (steps)
        self.last_error: Optional[str] = None

        # GPIO init
        try:
            GPIO_IF.setwarnings(False)
            if hasattr(GPIO_IF, "BCM"):
                GPIO_IF.setmode(GPIO_IF.BCM)  # type: ignore[attr-defined]
            GPIO_IF.setup(self.pin_step, GPIO_IF.OUT)
            GPIO_IF.setup(self.pin_dir, GPIO_IF.OUT)
            if self.pin_enable is not None:
                GPIO_IF.setup(self.pin_enable, GPIO_IF.OUT)
                # disable by default
                self._write_enable(False)
        except Exception as e:  # pragma: no cover
            self.last_error = f"GPIO init failed: {e}"

    # --- Hardware helpers -------------------------------------------------
    def _write_enable(self, on: bool) -> None:
        if self.pin_enable is None:
            self.enabled = True  # treat as always enabled
            return
        # many drivers are ENABLE low-active
        val = GPIO_IF.LOW if (on and self.invert_enable) else GPIO_IF.HIGH if on else (
            GPIO_IF.HIGH if self.invert_enable else GPIO_IF.LOW
        )
        try:
            GPIO_IF.output(self.pin_enable, val)
            self.enabled = on
        except Exception as e:  # pragma: no cover
            self.last_error = f"enable failed: {e}"

    def _set_dir(self, forward: bool) -> None:
        try:
            GPIO_IF.output(self.pin_dir, GPIO_IF.HIGH if forward else GPIO_IF.LOW)
        except Exception as e:  # pragma: no cover
            self.last_error = f"dir failed: {e}"

    def _pulse(self, step_delay: float) -> None:
        hi = step_delay * self.duty_cycle
        lo = step_delay - hi
        try:
            GPIO_IF.output(self.pin_step, GPIO_IF.HIGH)
            time.sleep(max(hi, 0.00005))
            GPIO_IF.output(self.pin_step, GPIO_IF.LOW)
            time.sleep(max(lo, 0.00005))
        except Exception as e:  # pragma: no cover
            self.last_error = f"pulse failed: {e}"

    # --- Public API --------------------------------------------------------
    def status(self) -> Dict[str, Optional[object]]:
        with self._lock:
            return {
                "enabled": self.enabled,
                "moving": self.moving,
                "position_steps": self.position,
                "worker_alive": bool(self._worker and self._worker.is_alive()),
                "last_error": self.last_error,
                "steps_per_rev": self.steps_per_rev,
                "default_rpm": self.default_rpm,
            }

    def enable(self) -> None:
        with self._lock:
            self._write_enable(True)

    def disable(self) -> None:
        with self._lock:
            if self.moving:
                raise RuntimeError("cannot disable while moving; abort first")
            self._write_enable(False)

    def abort(self) -> None:
        self._abort.set()
        t = None
        with self._lock:
            t = self._worker
        if t and t.is_alive():
            t.join(timeout=1.5)
        self._abort.clear()
        with self._lock:
            self.moving = False

    def step(self, steps: int, rpm: Optional[float] = None, forward: Optional[bool] = None) -> None:
        if steps == 0:
            return
        if not self.enabled and self.pin_enable is not None:
            raise RuntimeError("stepper not enabled")

        rpm_eff = max(1.0, float(rpm or self.default_rpm))
        sps = (rpm_eff * self.steps_per_rev) / 60.0  # steps per second
        step_delay = 1.0 / sps
        direction = forward if forward is not None else (steps > 0)

        def run():
            try:
                with self._lock:
                    self.moving = True
                    self.last_error = None
                self._set_dir(direction)
                total = abs(int(steps))
                sign = 1 if direction else -1
                for _ in range(total):
                    if self._abort.is_set():
                        break
                    self._pulse(step_delay)
                    with self._lock:
                        self.position += sign
            except Exception as e:  # pragma: no cover
                with self._lock:
                    self.last_error = str(e)
            finally:
                with self._lock:
                    self.moving = False

        with self._lock:
            if self.moving:
                raise RuntimeError("already moving")
            self._worker = threading.Thread(target=run, daemon=True)
            self._worker.start()


# --- Singleton controller (env-configurable) -------------------------------
PIN_STEP = int(os.getenv("STEPPER_PIN_STEP", os.getenv("PIN_STEP", "23")))
PIN_DIR = int(os.getenv("STEPPER_PIN_DIR", os.getenv("PIN_DIR", "24")))
PIN_ENABLE = os.getenv("STEPPER_PIN_ENABLE", os.getenv("PIN_ENABLE", "18"))
PIN_ENABLE_INT: Optional[int] = int(PIN_ENABLE) if PIN_ENABLE not in (None, "", "-1") else None
STEPS_PER_REV = int(os.getenv("STEPPER_STEPS_PER_REV", "200"))
DEFAULT_RPM = float(os.getenv("STEPPER_DEFAULT_RPM", "60"))
INVERT_ENABLE = os.getenv("STEPPER_INVERT_ENABLE", "1") not in ("0", "false", "False")

_controller = StepperController(
    pin_step=PIN_STEP,
    pin_dir=PIN_DIR,
    pin_enable=PIN_ENABLE_INT,
    steps_per_rev=STEPS_PER_REV,
    default_rpm=DEFAULT_RPM,
    invert_enable=INVERT_ENABLE,
)


# --- Routes ----------------------------------------------------------------
@router.get("/healthz")
def healthz() -> Dict[str, str]:
    return {"status": "ok"}


@router.get("/status")
def status() -> Dict[str, Optional[object]]:
    return _controller.status()


@router.post("/enable")
def api_enable() -> Dict[str, str]:
    _controller.enable()
    return {"result": "enabled"}


@router.post("/disable")
def api_disable() -> Dict[str, str]:
    try:
        _controller.disable()
    except RuntimeError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return {"result": "disabled"}


@router.post("/abort")
def api_abort() -> Dict[str, str]:
    _controller.abort()
    return {"result": "aborted"}


@router.post("/step")
def api_step(
    steps: int = Query(..., description="Number of steps; negative = reverse"),
    rpm: Optional[float] = Query(None, description="Speed in RPM"),
    direction: Optional[str] = Query(None, pattern="^(fwd|rev)$", description="Override direction"),
) -> Dict[str, object]:
    forward = None
    if direction == "fwd":
        forward = True
    elif direction == "rev":
        forward = False
    try:
        _controller.step(steps=steps, rpm=rpm, forward=forward)
    except RuntimeError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return {"result": "moving", "requested_steps": steps, "rpm": rpm or _controller.default_rpm}


# Convenience aliases for UI buttons
OPEN_STEPS = int(os.getenv("STEPPER_OPEN_STEPS", "200"))
CLOSE_STEPS = int(os.getenv("STEPPER_CLOSE_STEPS", "-200"))


@router.post("/open")
def api_open(rpm: Optional[float] = Query(None)) -> Dict[str, object]:
    try:
        _controller.step(steps=abs(OPEN_STEPS), rpm=rpm, forward=True)
    except RuntimeError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return {"result": "moving-open", "steps": abs(OPEN_STEPS)}


@router.post("/close")
def api_close(rpm: Optional[float] = Query(None)) -> Dict[str, object]:
    try:
        _controller.step(steps=abs(CLOSE_STEPS), rpm=rpm, forward=False)
    except RuntimeError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return {"result": "moving-close", "steps": abs(CLOSE_STEPS)}
