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

# Optional OpenCV fallback for non-Pi or when picamera2 is unavailable
try:  # pragma: no cover
    import cv2  # type: ignore
    CV2_AVAILABLE = True
except Exception:  # pragma: no cover
    CV2_AVAILABLE = False


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
        self.cap = None  # OpenCV VideoCapture
        self._cv_thread: Optional[threading.Thread] = None
        self.is_running = False
        self._lock = threading.Lock()
        
        try:
            self._initialize_camera()
        except Exception as e:
            print(f"ERROR: Failed to initialize camera: {e}")

    def _initialize_camera(self):
        """Initialize the Raspberry Pi camera."""
        # Initialize picamera2 if available; else prepare OpenCV
        self.output = StreamingOutput()
        if PICAMERA_AVAILABLE:
            try:
                self.picam2 = Picamera2(self.camera_num)
                # Use simpler config that works with rpicam
                video_config = self.picam2.create_video_configuration(
                    main={"size": self.resolution}
                )
                self.picam2.configure(video_config)
                print(f"PiCamera {self.camera_num} ready: {self.resolution[0]}x{self.resolution[1]} @ {self.framerate}fps")
            except Exception as e:
                self.picam2 = None
                print(f"picamera2 init failed: {e}")
                import traceback
                traceback.print_exc()
                if not CV2_AVAILABLE:
                    raise
        if self.picam2 is None and CV2_AVAILABLE:
            # OpenCV device; allow override via env CAMERA_DEVICE or use numeric index
            dev = os.getenv("CAMERA_DEVICE", "/dev/video0")
            try:
                self.cap = cv2.VideoCapture(dev)
                if not self.cap.isOpened():
                    raise RuntimeError(f"Failed to open camera device {dev}")
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
                self.cap.set(cv2.CAP_PROP_FPS, self.framerate)
                print(f"OpenCV camera ready on {dev}: {self.resolution[0]}x{self.resolution[1]} @ {self.framerate}fps")
            except Exception:
                self.cap = None
                raise

    def start(self):
        """Start the camera streaming."""
        with self._lock:
            if self.is_running:
                return
            try:
                if self.picam2 is not None:
                    encoder = MJPEGEncoder() if self.use_mjpeg else JpegEncoder()
                    self.picam2.start_recording(encoder, FileOutput(self.output))
                    self.is_running = True
                    print(f"Camera streaming started (picamera2) on {self.camera_num}")
                elif self.cap is not None and CV2_AVAILABLE:
                    # Start a background thread to capture frames and encode to JPEG
                    self.is_running = True
                    def _cv_loop():
                        try:
                            interval = 1.0 / max(1, self.framerate)
                            while self.is_running:
                                ok, frame = self.cap.read()
                                if not ok:
                                    time.sleep(0.05)
                                    continue
                                # Ensure BGR->JPEG encode
                                ok2, buf = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
                                if ok2:
                                    with self.output.condition:
                                        self.output.frame = buf.tobytes()
                                        self.output.condition.notify_all()
                                time.sleep(interval)
                        except Exception as e:
                            print(f"OpenCV capture error: {e}")
                    self._cv_thread = threading.Thread(target=_cv_loop, daemon=True)
                    self._cv_thread.start()
                    print("Camera streaming started (OpenCV)")
                else:
                    raise RuntimeError("No camera backend available (picamera2 or OpenCV)")
            except Exception as e:
                print(f"Failed to start camera: {e}")
                raise

    def stop(self):
        """Stop the camera streaming."""
        with self._lock:
            if not self.is_running:
                return
                
            try:
                if self.picam2 is not None:
                    self.picam2.stop_recording()
                self.is_running = False
                if self.cap is not None:
                    try:
                        self.cap.release()
                    except Exception:
                        pass
                if self._cv_thread and self._cv_thread.is_alive():
                    self._cv_thread.join(timeout=0.5)
                self.is_running = False
                print("Camera streaming stopped")
            except Exception as e:
                print(f"Failed to stop camera: {e}")

    def get_frame(self) -> Optional[bytes]:
        """Get the latest frame from the camera."""
        if not self.output:
            return None
            
        with self.output.condition:
            # Wait with timeout to avoid infinite blocking
            self.output.condition.wait(timeout=5.0)
            return self.output.frame

    def status(self) -> dict:
        """Get camera status."""
        backend = "none"
        if self.picam2 is not None:
            backend = "picamera2"
        elif self.cap is not None:
            backend = "opencv"
        
        return {
            "running": self.is_running,
            "camera_num": self.camera_num,
            "resolution": f"{self.resolution[0]}x{self.resolution[1]}",
            "framerate": self.framerate,
            "available": (self.picam2 is not None) or (self.cap is not None),
            "backend": backend,
            "picamera2_available": PICAMERA_AVAILABLE,
            "opencv_available": CV2_AVAILABLE,
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
            print("Auto-starting camera for stream request...")
            _camera.start()
            # Give camera a moment to stabilize
            import time
            time.sleep(0.3)
        except Exception as e:
            print(f"Failed to start camera in stream: {e}")
            # Send a simple error frame as an image
            yield b'--FRAME\r\n'
            yield b'Content-Type: text/plain\r\n\r\n'
            yield f'Camera unavailable: {str(e)}\r\n'.encode()
            return
    
    try:
        frame_count = 0
        while True:
            frame = _camera.get_frame()
            if frame:
                frame_count += 1
                yield b'--FRAME\r\n'
                # Including Content-Length improves compatibility with some proxies/clients
                header = f"Content-Type: image/jpeg\r\nContent-Length: {len(frame)}\r\n\r\n".encode()
                yield header
                yield frame
                yield b'\r\n'
                
                # Log periodic confirmation
                if frame_count % 300 == 0:  # Every ~10 seconds at 30fps
                    print(f"Camera stream active: {frame_count} frames delivered")
            else:
                # No frame available, brief pause
                import time
                time.sleep(0.01)
    except GeneratorExit:
        print("Client disconnected from camera stream")
    except Exception as e:
        print(f"Error in camera stream: {e}")


@router.get("/stream.mjpg")
def video_feed():
    """MJPEG video streaming endpoint."""
    if not (PICAMERA_AVAILABLE or CV2_AVAILABLE):
        return Response(
            content="Camera not available - no backend present (picamera2 or OpenCV)\n"
                    "Install picamera2: pip install picamera2\n"
                    "Or install OpenCV: pip install opencv-python",
            media_type="text/plain",
            status_code=503
        )
    
    # Check if camera was initialized
    if _camera.picam2 is None and _camera.cap is None:
        return Response(
            content="Camera hardware not detected. Check:\n"
                    "- Camera is properly connected\n"
                    "- Camera is enabled in raspi-config\n"
                    "- Device permissions (user in video group)\n"
                    f"- Device file exists: ls -la /dev/video*",
            media_type="text/plain",
            status_code=503
        )
    
    # Stream will auto-start camera if needed
    return StreamingResponse(
        generate_frames(),
        media_type='multipart/x-mixed-replace; boundary=FRAME',
        headers={
            # Prevent any client/proxy caching of the stream
            "Cache-Control": "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
            # Hint for nginx to avoid buffering this upstream
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/snapshot")
def get_snapshot():
    """Get a single JPEG snapshot from the camera."""
    if not _camera.is_running:
        try:
            print("Auto-starting camera for snapshot request...")
            _camera.start()
            time.sleep(0.5)  # Give camera time to warm up
        except Exception as e:
            return Response(
                content=f"Camera unavailable: {e}\n"
                        f"Available backends: picamera2={PICAMERA_AVAILABLE}, opencv={CV2_AVAILABLE}",
                media_type="text/plain",
                status_code=503,
                headers={
                    "Cache-Control": "no-store, no-cache, must-revalidate, proxy-revalidate",
                    "Pragma": "no-cache",
                },
            )
    
    # Try to get a frame with timeout
    max_attempts = 5
    for attempt in range(max_attempts):
        frame = _camera.get_frame()
        if frame:
            return Response(
                content=frame,
                media_type="image/jpeg",
                headers={
                    "Cache-Control": "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0",
                    "Pragma": "no-cache",
                    "Expires": "0",
                    "X-Accel-Buffering": "no",
                },
            )
        time.sleep(0.1)
    
    return Response(
        content="No frame available from camera after multiple attempts",
        media_type="text/plain",
        status_code=503,
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, proxy-revalidate",
            "Pragma": "no-cache",
        },
    )
