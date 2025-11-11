from __future__ import annotations

import io
import os
import threading
import time
from typing import Optional

from fastapi import APIRouter, Response
from fastapi.responses import StreamingResponse
from pathlib import Path
import json


router = APIRouter(prefix="/camera", tags=["camera"])


# --- Camera abstraction for Raspberry Pi Camera ---
try:
    from picamera2 import Picamera2  # type: ignore
    from picamera2.encoders import JpegEncoder, MJPEGEncoder  # type: ignore
    from picamera2.outputs import FileOutput  # type: ignore
    PICAMERA_AVAILABLE = True
except ImportError:
    PICAMERA_AVAILABLE = False
    Picamera2 = None  # type: ignore


class StreamingOutput(io.BufferedIOBase):
    """Thread-safe output class for MJPEG streaming."""
    
    def __init__(self):
        self.frame = None
        self.condition = threading.Condition()

    def write(self, buf):
        with self.condition:
            self.frame = buf
            self.condition.notify_all()


class CameraController:
    """Manages Raspberry Pi Camera with configurable port and resolution."""

    def __init__(
        self,
        camera_num: int = 0,
        resolution: tuple = (1920, 1080),
        framerate: int = 30,
        use_mjpeg: bool = True,
    ):
        self.camera_num = camera_num
        self.resolution = resolution
        self.framerate = framerate
        self.use_mjpeg = use_mjpeg
        self.picam2: Optional[Picamera2] = None
        self.output: Optional[StreamingOutput] = None
        self.is_running = False
        self._lock = threading.Lock()
        
        if not PICAMERA_AVAILABLE:
            print("WARNING: picamera2 not available. Camera streaming will not work.")
            return
        
        try:
            self._initialize_camera()
        except Exception as e:
            print(f"ERROR: Failed to initialize camera: {e}")

    def _initialize_camera(self):
        """Initialize the Raspberry Pi camera."""
        if not PICAMERA_AVAILABLE:
            return
            
        try:
            self.picam2 = Picamera2(self.camera_num)
            
            # Configure camera for video streaming
            video_config = self.picam2.create_video_configuration(
                main={"size": self.resolution, "format": "RGB888"},
                controls={"FrameRate": self.framerate}
            )
            self.picam2.configure(video_config)
            
            # Setup streaming output
            self.output = StreamingOutput()
            
            print(f"Camera {self.camera_num} initialized: {self.resolution[0]}x{self.resolution[1]} @ {self.framerate}fps")
        except Exception as e:
            print(f"Failed to initialize camera: {e}")
            raise

    def start(self):
        """Start the camera streaming."""
        with self._lock:
            if self.is_running or not self.picam2:
                return
                
            try:
                if self.use_mjpeg:
                    encoder = MJPEGEncoder()
                else:
                    encoder = JpegEncoder()
                    
                self.picam2.start_recording(encoder, FileOutput(self.output))
                self.is_running = True
                print(f"Camera streaming started on port {self.camera_num}")
            except Exception as e:
                print(f"Failed to start camera: {e}")
                raise

    def stop(self):
        """Stop the camera streaming."""
        with self._lock:
            if not self.is_running or not self.picam2:
                return
                
            try:
                self.picam2.stop_recording()
                self.is_running = False
                print("Camera streaming stopped")
            except Exception as e:
                print(f"Failed to stop camera: {e}")

    def get_frame(self) -> Optional[bytes]:
        """Get the latest frame from the camera."""
        if not self.output:
            return None
            
        with self.output.condition:
            self.output.condition.wait()
            return self.output.frame

    def status(self) -> dict:
        """Get camera status."""
        return {
            "running": self.is_running,
            "camera_num": self.camera_num,
            "resolution": f"{self.resolution[0]}x{self.resolution[1]}",
            "framerate": self.framerate,
            "available": PICAMERA_AVAILABLE and self.picam2 is not None,
        }


# --- Configuration from environment ---
CAMERA_NUM = int(os.getenv("CAMERA_NUM", "0"))
CAMERA_WIDTH = int(os.getenv("CAMERA_WIDTH", "1920"))
CAMERA_HEIGHT = int(os.getenv("CAMERA_HEIGHT", "1080"))
CAMERA_FPS = int(os.getenv("CAMERA_FPS", "30"))

# Initialize camera controller
_camera = CameraController(
    camera_num=CAMERA_NUM,
    resolution=(CAMERA_WIDTH, CAMERA_HEIGHT),
    framerate=CAMERA_FPS,
    use_mjpeg=True,
)


# --- Routes ---
@router.get("/status")
def get_camera_status():
    """Get camera status."""
    status = _camera.status()
    # Augment with publisher health if available
    health_path = Path(os.getenv("PUBLISHER_HEALTH_FILE", "/tmp/publisher_health.json"))
    if health_path.exists():
        try:
            status["publisher"] = json.loads(health_path.read_text())
        except Exception:
            status["publisher"] = {"status": "unreadable"}
    else:
        status["publisher"] = {"status": "missing"}
    return status


@router.post("/start")
def start_camera():
    """Start camera streaming."""
    try:
        _camera.start()
        return {"status": "started"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/stop")
def stop_camera():
    """Stop camera streaming."""
    try:
        _camera.stop()
        return {"status": "stopped"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def generate_frames():
    """Generator function for streaming frames."""
    # Ensure camera is started
    if not _camera.is_running:
        try:
            _camera.start()
        except Exception as e:
            print(f"Failed to start camera in stream: {e}")
            # Send a simple error frame
            yield b'--FRAME\r\n'
            yield b'Content-Type: text/plain\r\n\r\n'
            yield b'Camera unavailable\r\n'
            return
    
    try:
        while True:
            frame = _camera.get_frame()
            if frame:
                yield b'--FRAME\r\n'
                yield b'Content-Type: image/jpeg\r\n\r\n'
                yield frame
                yield b'\r\n'
    except GeneratorExit:
        print("Client disconnected from stream")


@router.get("/stream.mjpg")
def video_feed():
    """MJPEG video streaming endpoint."""
    if not PICAMERA_AVAILABLE:
        return Response(
            content="Camera not available - picamera2 not installed",
            media_type="text/plain",
            status_code=503
        )
    # Ensure running (auto-start safeguard)
    if not _camera.is_running:
        try:
            _camera.start()
        except Exception as e:
            return Response(content=f"Failed to start camera: {e}", media_type="text/plain", status_code=500)
    return StreamingResponse(
        generate_frames(),
        media_type='multipart/x-mixed-replace; boundary=FRAME'
    )


@router.get("/snapshot")
def get_snapshot():
    """Get a single JPEG snapshot from the camera."""
    if not _camera.is_running:
        try:
            _camera.start()
            time.sleep(0.5)  # Give camera time to warm up
        except Exception as e:
            return Response(
                content=f"Camera unavailable: {e}",
                media_type="text/plain",
                status_code=503
            )
    
    frame = _camera.get_frame()
    if frame:
        return Response(content=frame, media_type="image/jpeg")
    else:
        return Response(
            content="No frame available",
            media_type="text/plain",
            status_code=503
        )
