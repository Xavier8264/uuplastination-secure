"""Basic tests to ensure modules import without Raspberry Pi hardware.

Skips picamera2-dependent logic gracefully if unavailable.
"""
from importlib import import_module


def test_fastapi_import():
    import fastapi  # noqa: F401


def test_camera_router_import():
    mod = import_module("app.routers.camera")
    assert hasattr(mod, "router")


def test_stepper_router_import():
    mod = import_module("app.routers.stepper")
    assert hasattr(mod, "router")


def test_webrtc_router_import():
    mod = import_module("app.routers.webrtc")
    assert hasattr(mod, "router")


def test_publisher_module_import():
    # Publisher should import even if picamera2/OpenCV missing
    mod = import_module("app.services.publisher")
    assert hasattr(mod, "main")
