# UU Plastination — Secure Control System

Modern, Apple-inspired web dashboard for controlling plastination equipment with live camera feed, dual valve control systems, and comprehensive system monitoring on Raspberry Pi.

## ✨ Features

- 📹 **Live Camera Feed** - MJPEG streaming from Raspberry Pi Camera (CSI port) with WebRTC/LiveKit support for low-latency viewing
- 🎛️ **Dual Valve Control Systems**
  - **Stepper Motor Control** - Precise GPIO-driven control (A4988/DRV8825 compatible drivers)
  - **Serial Valve Control** - Arduino-based valve control via USB serial (`/dev/ttyACM0`)
- 📊 **System Monitoring** - Real-time Pi telemetry including CPU temp/usage, memory, uptime, network status, and systemd service health
- 🚀 **WebRTC Streaming** - LiveKit integration with RTMP publisher and automatic MJPEG fallback
- 🎨 **Beautiful UI** - Apple-inspired responsive design

## 📋 Table of Contents

- [Hardware Requirements](#-hardware-requirements)
- [Quick Start](#-quick-start)
- [API Endpoints](#-api-endpoints)
- [Configuration](#-configuration)
- [Production Deployment](#-production-deployment)
- [WebRTC Setup](#-webrtc--livekit-setup)
- [Troubleshooting](#-troubleshooting)
- [Documentation](#-documentation)

## 🔌 Hardware Requirements

### Essential
- Raspberry Pi 4 or 5 with Raspberry Pi OS (Bullseye or newer)
- Raspberry Pi Camera Module (connected to CSI port)
- Power supply appropriate for your Pi model

### For Stepper Motor Control
- Stepper motor (NEMA 17 or similar)
- Stepper driver (A4988, DRV8825, or compatible)
- Appropriate power supply for motor (12V-24V typical)
- GPIO connections (see [GPIO_SETUP.md](GPIO_SETUP.md))

### For Serial Valve Control
- Arduino or compatible microcontroller running valve control firmware
- USB connection to Raspberry Pi (`/dev/ttyACM0`)

## 🚀 Quick Start

### Prerequisites

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install system dependencies
sudo apt install python3 python3-pip python3-venv -y
sudo apt install python3-picamera2 libraspberrypi-bin -y
```

### Installation

```bash
# Clone repository
git clone https://github.com/Xavier8264/uuplastination-secure.git
cd uuplastination-secure

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
nano .env  # Edit to match your hardware setup
```

### Running Locally

```bash
# Activate virtual environment
source venv/bin/activate

# Run the application
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Access the dashboard at: `http://your-pi-ip:8000`

## 🔧 API Endpoints

All API endpoints are served by FastAPI on `127.0.0.1:8000` and should be proxied through Nginx for security.

### System Monitoring

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/stats` | GET | Comprehensive system telemetry (CPU, memory, uptime, network, services) |

**Response includes:**
- CPU temperature and usage percentage
- Memory total, used, and percentage
- System uptime in seconds
- Network IPv4 addresses and internet reachability
- Systemd service states (configurable via env vars)
- Port availability checks (RTSP 8554, API 8000)
- OS information and timestamp

### Camera

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/camera/stream.mjpg` | GET | Live MJPEG stream |
| `/camera/snapshot` | GET | Single frame capture |
| `/camera/status` | GET | Camera status and publisher health |

### Stepper Motor Control

**Base path:** `/api/stepper`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/healthz` | GET | Simple health check (200 OK) |
| `/status` | GET | Motor state: enabled, moving, position, worker status, errors |
| `/enable` | POST | Enable motor (assert ENABLE pin) |
| `/disable` | POST | Disable motor (de-assert ENABLE pin) - errors if moving |
| `/abort` | POST | Emergency stop - cancel current move |
| `/step` | POST | Execute precise move (params: `steps`, `rpm`, `direction`) |
| `/open` | POST | Convenience forward move (default 200 steps) |
| `/close` | POST | Convenience reverse move (default -200 steps) |

**Query Parameters for `/step`:**
- `steps` (required): Number of steps; negative values reverse direction
- `rpm` (optional): Speed in rotations per minute (default: 60)
- `direction` (optional): `fwd` or `rev` to override step sign

**Notes:**
- Non-blocking operation via background worker thread
- Returns HTTP 409 if already moving (use `/abort` to stop)
- Timing based on Python sleeps (adequate for manual control, not real-time)

### Serial Valve Control

**Base path:** `/api/valve`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/open` | POST | Send 'r' character to Arduino valve controller |
| `/close` | POST | Send 'l' character to Arduino valve controller |

**Notes:**
- Communicates via `/dev/ttyACM0` at 115200 baud (configurable)
- One-way communication (write-only)
- Uses exclusive serial port access
- Returns HTTP 503 if port is busy

### WebRTC/LiveKit

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/webrtc/health` | GET | WebRTC configuration summary and reachability |
| `/webrtc/diagnostics` | GET | Detailed diagnostics including token issuance test |

## ⚙️ Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

#### Camera Settings
```bash
CAMERA_NUM=0           # Camera port (0 for CAM0, 1 for CAM1)
CAMERA_WIDTH=1920      # Resolution width
CAMERA_HEIGHT=1080     # Resolution height
CAMERA_FPS=30          # Frame rate
```

#### Stepper Motor GPIO (BCM Numbering)
```bash
STEPPER_PIN_STEP=23       # GPIO pin for STEP signal (default: 23)
STEPPER_PIN_DIR=24        # GPIO pin for DIR signal (default: 24)
STEPPER_PIN_ENABLE=18     # GPIO pin for ENABLE signal (default: 18, -1 to disable)
STEPPER_INVERT_ENABLE=1   # Enable pin polarity (1=active-low, 0=active-high)
STEPPER_STEPS_PER_REV=200 # Steps per revolution (200 for 1.8° motors)
STEPPER_DEFAULT_RPM=60    # Default rotation speed
STEPPER_OPEN_STEPS=200    # Steps for "open" button
STEPPER_CLOSE_STEPS=-200  # Steps for "close" button
```

See [GPIO_SETUP.md](GPIO_SETUP.md) for complete pinout reference and wiring guide.

#### Serial Valve Settings
```bash
VALVE_SERIAL_BAUD=115200  # Baud rate for /dev/ttyACM0
```

#### LiveKit/WebRTC
```bash
LIVEKIT_HOST=https://livekit.yourdomain.com
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret
LIVEKIT_ICE_SERVERS=turns:turn.yourdomain.com:5349?transport=tcp
WEBRTC_DISABLE=0          # Set to 1 to force MJPEG fallback
```

#### System Monitoring
```bash
SERVICE_CAMERA=camera-stream.service   # Systemd service name to monitor
SERVICE_STEPPER=valve-control.service  # Systemd service name to monitor
PORT_RTSP=8554                         # RTSP port to check
PORT_API=8000                          # API port to check
```

## 🏭 Production Deployment

### 1. Systemd Service

The application should run as a systemd service for automatic startup and restart on failure.

```bash
# Copy template to systemd directory
sudo cp systemd/uuplastination-stats.service /etc/systemd/system/

# Edit to match your deployment path
sudo nano /etc/systemd/system/uuplastination-stats.service

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable --now uuplastination-stats.service

# Check status
sudo systemctl status uuplastination-stats.service
```

**Service Configuration Notes:**
- Default working directory: `/var/www/secure/uuplastination-secure`
- Binds to `127.0.0.1:8000` (localhost only)
- Auto-restarts on failure with 3-second delay
- Environment variables can be set in the service file or via `EnvironmentFile`

### 2. Nginx Reverse Proxy

The API should **never** be exposed directly. Use Nginx as a reverse proxy with SSL/TLS.

```bash
# Include API proxy configuration in your secure server block
sudo nano /etc/nginx/sites-available/secure
```

Add this inside your SSL server block:
```nginx
# Include API routes (only in secure vhost)
include /path/to/nginx/secure_api_location.conf;
```

The `secure_api_location.conf` file proxies `/api/*` to `http://127.0.0.1:8000/api/*`.

**Optional Rate Limiting for Actuators:**
```nginx
# Define rate limit zone (in http context)
limit_req_zone $binary_remote_addr zone=actuator:10m rate=10r/m;

# Apply to stepper/valve routes (in server context)
location /api/stepper/ {
    limit_req zone=actuator burst=5 nodelay;
    proxy_pass http://127.0.0.1:8000/api/stepper/;
}

location /api/valve/ {
    limit_req zone=actuator burst=5 nodelay;
    proxy_pass http://127.0.0.1:8000/api/valve/;
}
```

### 3. Security Hardening

- ✅ Bind API to `127.0.0.1` only (not `0.0.0.0`)
- ✅ Use Nginx reverse proxy with SSL/TLS
- ✅ Add authentication (Cloudflare Access, HTTP Basic Auth, etc.)
- ✅ Rate limit actuator endpoints (`/api/stepper/*`, `/api/valve/*`)
- ✅ Restrict `.env` file permissions: `chmod 600 .env`
- ✅ Keep system and dependencies updated
- ✅ Only expose actuator routes on the authenticated/secure vhost

## 🎥 WebRTC & LiveKit Setup

For low-latency live streaming, the system supports WebRTC via LiveKit with automatic MJPEG fallback.

### 1. Create LiveKit Ingress

```bash
# Generate RTMP ingress and save stream key
python3 webrtc/init_ingress.py --room plastination --name pi-cam --out webrtc/ingress_key.txt

# View generated credentials
cat webrtc/ingress_key.txt
```

### 2. Start Camera Publisher

**Manual Test:**
```bash
bash webrtc/pi_rtmp_publisher.sh
```

**Systemd Service (Recommended):**
```bash
# Install publisher service
sudo cp systemd/pi-camera-publisher.service.example /etc/systemd/system/pi-camera-publisher.service

# Edit environment variables if needed
sudo nano /etc/systemd/system/pi-camera-publisher.service

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable --now pi-camera-publisher.service

# Check logs
sudo journalctl -u pi-camera-publisher.service -f
```

**Publisher logs:** `/var/log/pi-camera/publisher.log`

### 3. WebRTC Troubleshooting

| Symptom | Solution |
|---------|----------|
| MJPEG only, no WebRTC | Check browser console for errors. Verify `LIVEKIT_HOST` is HTTPS and reachable. Ensure TURN ports are exposed. |
| Publisher restarts constantly | Check camera ribbon cable. Run `libcamera-hello` to test. Review `/var/log/pi-camera/publisher.log`. |
| Token errors | Verify `LIVEKIT_API_KEY` and `LIVEKIT_API_SECRET` in `.env` match LiveKit server. |
| High latency | Ensure using H264 hardware encoding (libcamera-vid) not software MJPEG→x264. |
| TURN connection failures | Use TURNS (port 5349) over TCP if UDP blocked. Verify TLS certificate and realm match domain. |
| ICE gathering stalls | Check `/webrtc/health` endpoint. Ensure `LIVEKIT_ICE_SERVERS` is set with valid STUN/TURN servers. |
| 403 joining room | Rotate API credentials. Verify keys match between `.env` and LiveKit server config. |

**Validation Script:**
```bash
# Run automated WebRTC checks
python3 scripts/webrtc_validate.py
```

## 🐛 Troubleshooting

### Camera Not Working

```bash
# Test camera hardware
libcamera-hello

# Check camera detection
vcgencmd get_camera

# Enable camera if disabled
sudo raspi-config
# Navigate to: Interface Options > Camera > Enable
```

### Stepper Motor Not Moving

1. **Check power supply** - Ensure stepper driver has adequate power (12V-24V typical)
2. **Verify GPIO pins** - Confirm `.env` settings match your wiring
3. **Test enable pin**:
   ```bash
   curl -X POST http://localhost:8000/api/stepper/enable
   curl http://localhost:8000/api/stepper/status
   ```
4. **Check driver microstepping** - Ensure driver DIP switches match your steps-per-revolution setting
5. **Review logs**:
   ```bash
   sudo journalctl -u uuplastination-stats.service -f
   ```

### Serial Valve Not Responding

1. **Check device path**:
   ```bash
   ls -l /dev/ttyACM*
   # Ensure /dev/ttyACM0 exists and is readable
   ```
2. **Verify permissions**:
   ```bash
   # Add user to dialout group
   sudo usermod -a -G dialout $USER
   # Log out and back in
   ```
3. **Test serial connection**:
   ```bash
   # Install screen if not present
   sudo apt install screen
   
   # Connect to serial port
   screen /dev/ttyACM0 115200
   # Type 'r' or 'l' and observe Arduino behavior
   ```
4. **Check baud rate** - Ensure Arduino firmware uses 115200 baud (or update `VALVE_SERIAL_BAUD`)

### Service Logs

```bash
# View service status
sudo systemctl status uuplastination-stats.service

# Follow live logs
sudo journalctl -u uuplastination-stats.service -f

# View last 100 lines
sudo journalctl -u uuplastination-stats.service -n 100
```

### GPIO Permission Issues

If GPIO operations fail with permission errors:

```bash
# Add user to gpio group
sudo usermod -a -G gpio $USER

# Create udev rule for GPIO access
echo 'SUBSYSTEM=="gpio", GROUP="gpio", MODE="0660"' | sudo tee /etc/udev/rules.d/99-gpio.rules

# Reload udev rules
sudo udevadm control --reload-rules
sudo udevadm trigger

# Log out and back in
```

## 📚 Documentation

- **[SETUP.md](SETUP.md)** - Detailed setup and installation guide
- **[GPIO_SETUP.md](GPIO_SETUP.md)** - Complete GPIO pinout reference and wiring diagrams
- **[.env.example](.env.example)** - Full environment variable documentation
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Production deployment and security guidelines
- **[WEBRTC.md](WEBRTC.md)** - WebRTC/LiveKit integration guide
- **[VALVE_API.md](VALVE_API.md)** - Valve control API documentation

## 🤝 Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

## 📄 License

MIT License - See LICENSE file for details

## 📞 Support

For issues or questions, open an issue on [GitHub](https://github.com/Xavier8264/uuplastination-secure/issues).

---

**Built with ❤️ for the UU Plastination Lab**
