# UU Plastination — Technical Reference

Comprehensive technical documentation including API reference, implementation details, troubleshooting fixes, and WebRTC setup.

---

## Table of Contents

- [API Reference](#api-reference)
- [Valve API Details](#valve-api-details)
- [WebRTC & LiveKit Integration](#webrtc--livekit-integration)
- [Implementation History](#implementation-history)
- [Webcam Fixes Applied](#webcam-fixes-applied)
- [Issue Resolution: Valve 405 Error](#issue-resolution-valve-405-error)
- [API Analysis & Cleanup](#api-analysis--cleanup)
- [Dashboard Assets](#dashboard-assets)

---

## API Reference

All API endpoints are served by FastAPI on `127.0.0.1:8000` and should be proxied through Nginx for security.

### System Monitoring

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/stats` | GET | Comprehensive system telemetry (CPU, memory, uptime, network, services) |
| `/api/system/metrics` | GET | Simplified format for dashboard (cpuTemp, cpuUsage, memoryUsage, uptime) |

**Response includes:**
- CPU temperature and usage percentage
- Memory total, used, and percentage
- System uptime in seconds (human-readable in `/metrics`)
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
| `/camera/start` | POST | Start camera |
| `/camera/stop` | POST | Stop camera |

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
| `/health` | GET | Check if serial port is accessible |

**Notes:**
- Communicates via `/dev/ttyACM0` at 115200 baud (configurable)
- One-way communication (write-only)
- Uses exclusive serial port access
- Returns HTTP 503 if port is busy

### WebRTC/LiveKit

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/webrtc/config` | GET | LiveKit configuration summary |
| `/webrtc/token` | GET | Returns access token for WebRTC connection |
| `/webrtc/health` | GET | WebRTC configuration summary and reachability |
| `/webrtc/diagnostics` | GET | Detailed diagnostics including token issuance test |

---

## Valve API Details

### Overview
The valve API provides a clean, one-way serial communication interface that sends single characters ('r' and 'l') through `/dev/ttyACM0` based on button presses from the frontend.

### Simplified Implementation

The current valve API has been simplified to do **exactly one thing**: send single characters through `/dev/ttyACM0`.

- **POST /api/valve/open** → sends `'r'` → returns `"OK"`
- **POST /api/valve/close** → sends `'l'` → returns `"OK"`

**No reading from serial port. No complex error handling. Just send and return OK.**

### How It Works

```python
def _send_char(ch: str) -> None:
    """Send a single character through serial port."""
    ser = serial.Serial(
        "/dev/ttyACM0",
        115200,
        timeout=0,
        write_timeout=0.5,
        exclusive=True  # Only one connection at a time
    )
    ser.write(ch.encode("utf-8"))
    ser.flush()
    ser.close()
```

### Response Codes

- **200 OK**: Character sent successfully → Response body: `"OK"`
- **500 Internal Server Error**: Serial communication failed
- **503 Service Unavailable**: Serial port is busy or locked by another process

### Configuration
**Hardcoded:**
- Device: `/dev/ttyACM0`
- Baud rate: 115200 (can be overridden with `VALVE_SERIAL_BAUD` env var)
- Characters: 'r' for open, 'l' for close

### Testing

```bash
# Health check
curl http://localhost:8000/api/valve/health

# Send 'r' (open)
curl -X POST http://localhost:8000/api/valve/open

# Send 'l' (close)
curl -X POST http://localhost:8000/api/valve/close
```

### Serial Port Setup

```bash
# Check if device exists
ls -l /dev/ttyACM0

# Add user to dialout group (if permission denied)
sudo usermod -a -G dialout $USER

# Verify permissions
groups $USER
```

### Troubleshooting

#### Port Busy Error
```bash
# Check what's using the port
lsof /dev/ttyACM0

# Kill the process if needed
sudo fuser -k /dev/ttyACM0

# Or restart the API
sudo systemctl restart uuplastination-api
```

#### Permission Denied
```bash
# Add user to dialout group
sudo usermod -a -G dialout $USER

# Reboot or re-login for changes to take effect
```

---

## WebRTC & LiveKit Integration

This system uses LiveKit + Ingress + coturn stack to deliver the Raspberry Pi camera to the web UI using WebRTC.

### Components

- **LiveKit Server**: signaling + SFU (WS at 7880; use HTTPS/WSS via reverse proxy)
- **LiveKit Ingress**: accepts RTMP/WHIP, publishes into a room
- **coturn**: TURN/TURNS for NAT traversal (recommended TURNS on 5349 or 443)

Frontend at `index.html` auto-attempts a WebRTC connection with retries; if unavailable, it falls back to MJPEG and keeps retrying.

### DNS and HTTPS (Production)

You must expose signaling and TURN on public hostnames:

- `livekit.<your-domain>` → HTTPS/WSS to LiveKit (via Nginx or Cloudflare Tunnel). Prefer a dedicated subdomain over a path.
- `turn.<your-domain>` → TURNS (5349/tcp or 443/tcp) directly reachable on the Internet (Cloudflare proxy OFF)

**Important:** Cloudflare Tunnel does not proxy UDP; prefer TURNS over TCP (5349) or expose 443 directly. If you cannot expose TURN publicly, WebRTC may fail under NAT.

### Configuration

1. Copy `.env.example` to `.env` and set:
   - `LIVEKIT_HOST=https://livekit.<your-domain>`
   - `LIVEKIT_API_KEY` / `LIVEKIT_API_SECRET`
   - `LIVEKIT_ICE_SERVERS=turns:turn.<your-domain>:5349?transport=tcp`
   - `TURN_REALM=<your-domain>`
   - `TURN_STATIC_SECRET=random long hex (32+ chars)`
   - `TURN_EXTERNAL_IP=your public IP (if behind NAT)`
   - `TURN_CERT_DIR` path containing `fullchain.pem` and `privkey.pem` for `turn.<your-domain>`

2. Start the stack:
   - Ensure ports 7880/tcp (or proxied), 5349/tcp (TURNS), 3478/udp (TURN) are reachable.

3. Bring up services:
   ```bash
   docker compose -f webrtc/docker-compose.yml up -d
   ```

### Publishing from the Pi (RTMP Ingress)

We use LiveKit Ingress (RTMP) so the Pi can publish without running a full WebRTC client.

1. **Create an RTMP Ingress and get stream key:**
   ```python
   from livekit import api as lk

   client = lk.ApiClient(host=LIVEKIT_HOST, api_key=LIVEKIT_API_KEY, api_secret=LIVEKIT_API_SECRET)
   req = lk.CreateIngressRequest(input_type=lk.IngressInput.RTMP_INPUT, name="pi-cam", room_name="plastination")
   resp = client.ingress.create_ingress(req)
   print(resp.rtmp.url, resp.stream_key)
   ```

2. **Push RTMP from the Pi:**
   ```bash
   libcamera-vid -t 0 --inline -n -o - \
     | ffmpeg -re -f h264 -i - -c:v copy -f flv rtmp://<livekit-hostname>/live/<STREAM_KEY>
   ```

   Or if you don't have H.264 elementary stream:
   ```bash
   ffmpeg -f v4l2 -input_format mjpeg -i /dev/video0 -c:v libx264 -preset veryfast -tune zerolatency -f flv rtmp://<livekit-hostname>/live/<STREAM_KEY>
   ```

3. Open your dashboard page; the viewer auto-subscribes to the room and displays the first video track. It will keep retrying WebRTC if the producer isn't up yet.

### Auto-create Ingress on Boot

Use `webrtc/init_ingress.py` to create an ingress and write the stream key to a file. Combine with a systemd unit to start the publisher automatically.

### Troubleshooting WebRTC

| Symptom | Solution |
|---------|----------|
| MJPEG only, no WebRTC | Check browser console for errors. Verify `LIVEKIT_HOST` is HTTPS and reachable. Ensure TURN ports are exposed. |
| Publisher restarts constantly | Check camera ribbon cable. Run `libcamera-hello` to test. Review `/var/log/pi-camera/publisher.log`. |
| Token errors | Verify `LIVEKIT_API_KEY` and `LIVEKIT_API_SECRET` in `.env` match LiveKit server. |
| High latency | Ensure using H264 hardware encoding (libcamera-vid) not software MJPEG→x264. |
| TURN connection failures | Use TURNS (port 5349) over TCP if UDP blocked. Verify TLS certificate and realm match domain. |
| ICE gathering stalls | Check `/webrtc/health` endpoint. Ensure `LIVEKIT_ICE_SERVERS` is set with valid STUN/TURN servers. |
| 403 joining room | Rotate API credentials. Verify keys match between `.env` and LiveKit server config. |

---

## Implementation History

### What Was Built

#### Camera Publishing System
- **RTMP Publisher** (`webrtc/pi_rtmp_publisher.sh`): Bash script using `libcamera-vid | ffmpeg` to push H.264 to LiveKit ingress
  - Auto-restarts with exponential backoff on failure
  - Logs to `/var/log/pi-camera/publisher.log`
  - Reads stream key from `webrtc/ingress_key.txt` or environment

- **Systemd Service** (`systemd/pi-camera-publisher.service.example`):
  - Auto-starts on boot
  - Restarts on crash
  - Manages logs and health

- **Python Publisher** (`app/services/publisher.py`):
  - Future-facing alternative for direct WebRTC publishing
  - Includes health file monitoring
  - Graceful fallback between picamera2 and OpenCV

#### Backend Enhancements
- **Camera Router** (`app/routers/camera.py`):
  - Enhanced `/camera/status` with publisher health info
  - Auto-starts MJPEG stream on first request
  - Graceful degradation when picamera2 unavailable

- **Dependencies** (`requirements.txt`):
  - Added: `aiohttp`, `aiortc`, `av`, `opencv-python`
  - Commented out `picamera2` (Pi-specific, install via apt)

- **Health Monitoring**:
  - Publisher writes JSON health to `/tmp/publisher_health.json`
  - Status endpoint exposes publisher state to dashboard

#### Frontend Integration
- **Dashboard** (`assets/js/dashboard.js`):
  - Disabled mock mode (`MOCK_DATA=false`)
  - Uses live API endpoints

- **WebRTC Auto-Connect** (`index.html`):
  - LiveKit client with retry logic
  - Falls back to MJPEG if WebRTC unavailable
  - Keeps retrying WebRTC in background

### Architecture Diagram

```
┌─────────────┐  H.264/RTMP   ┌──────────────┐  WebRTC      ┌─────────────┐
│ Raspberry   │──────────────>│   LiveKit    │<────────────>│   Browser   │
│ Pi Camera   │   (Ingress)   │   Server     │  (Viewer)    │  Dashboard  │
└─────────────┘               └──────────────┘              └─────────────┘
      │                              │                              │
      │ libcamera-vid                │ Signaling                    │
      │ + ffmpeg                     │ + TURN                       │ MJPEG
      │                              │                              │ Fallback
      └──────────────────────────────┴──────────────────────────────┘
                        Nginx (HTTPS proxy)
```

**Flow:**
1. Pi camera captures video via `libcamera-vid` (hardware H.264)
2. `ffmpeg` wraps to FLV and pushes to LiveKit RTMP ingress
3. LiveKit ingress publishes into room "plastination"
4. Browser fetches token from `/webrtc/token`
5. LiveKit client subscribes to video track
6. Video appears in dashboard with <1s latency
7. If WebRTC fails, falls back to MJPEG at `/camera/stream.mjpg`

---

## Webcam Fixes Applied

### Issues Found and Fixed

#### 1. LiveKit Container Crash Loop ✅ FIXED
**Problem**: LiveKit and Ingress containers were in restart loop with error:
```
Could not parse keys, it needs to be exactly, "key: secret", including the space
```

**Root Cause**: The `LIVEKIT_KEYS` environment variable format was incorrect.

**Fix Applied**:
- Updated `webrtc/docker-compose.yml` to use proper YAML syntax with quoted keys:
  ```yaml
  environment:
    LIVEKIT_KEYS: "devkey: devsecret"
  ```

#### 2. Missing Environment Variables ✅ FIXED
**Problem**: FastAPI application couldn't read environment variables from `.env` file.

**Root Cause**:
1. Environment variables were read at module import time, before `.env` was loaded
2. Missing `WEBRTC_DISABLE` variable in `.env`
3. No mechanism to load `.env` file into Python environment

**Fix Applied**:
- Installed `python-dotenv` package
- Added `.env` loading at the top of `app/main.py` and `app/routers/webrtc.py`

#### 3. Insecure TURN/ICE Configuration ✅ FIXED
**Problem**: `.env` file contained placeholder values.

**Fix Applied**:
- Generated secure random secret
- Changed to public STUN server since coturn TLS certificates don't exist
- Disabled coturn service until TLS certificates are available

#### 4. FastAPI Not Running ✅ FIXED
**Problem**: API endpoints returned no response.

**Fix Applied**:
- Created virtual environment activation and startup procedure
- Created convenience scripts: `start_services.sh`, `stop_services.sh`

---

## Issue Resolution: Valve 405 Error

### Problem
The valve API was returning a **405 Method Not Allowed** error when accessed through the `/secure/api/valve/*` path.

### Root Cause
The nginx configuration had the `/secure/` location block matching BEFORE the specific `/secure/api/` proxy blocks. This caused nginx to try serving static files instead of proxying API requests to the FastAPI backend.

### What Was Happening:
1. Browser requests: `POST /secure/api/valve/open`
2. Nginx matches: `location ^~ /secure/` (static file serving)
3. Nginx tries: `try_files $uri $uri/ /index.html`
4. Result: 405 error because static files don't accept POST requests

### Solution Applied

#### 1. Fixed nginx Configuration
Updated `/etc/nginx/sites-available/uuplastination` to include specific proxy location blocks BEFORE the general `/secure/` location:

```nginx
# BEFORE - Proxy blocks for /secure/api/, /secure/camera/, /secure/webrtc/
location ^~ /secure/api/ {
    auth_basic "UU Plastination — Secure";
    auth_basic_user_file /etc/nginx/.htpasswd;
    proxy_pass http://127.0.0.1:8000/api/;
    # ... proxy headers
}

# AFTER - General static file serving for /secure/
location ^~ /secure/ {
    alias /home/plastination/uuplastination/uuplastination-secure/;
    auth_basic "UU Plastination — Secure";
    auth_basic_user_file /etc/nginx/.htpasswd;
    try_files $uri $uri/ /index.html;
}
```

#### 2. Restarted API Server
Killed and restarted the uvicorn process to load the updated valve API code.

#### 3. Reloaded nginx
Applied the configuration changes with `sudo systemctl reload nginx`.

### Testing After Fix

```bash
# Without auth (root path) - should work
curl -X POST http://localhost/api/valve/open

# With auth (secure path) - needs credentials
curl -X POST http://localhost/secure/api/valve/open -u ADMIN:password
```

---

## API Analysis & Cleanup

### Frontend API Usage (from index.html)

#### Active Endpoints Used by Frontend:

1. **Valve API** (`/api/valve/*`)
   - `POST /api/valve/open` - Sends 'r' character
   - `POST /api/valve/close` - Sends 'l' character

2. **Stats API** (`/api/system/metrics`)
   - `GET /api/system/metrics` - Returns CPU temp, usage, memory, uptime

3. **Stepper API** (`/api/stepper/status`)
   - `GET /api/stepper/status` - Returns stepper motor status

4. **Camera API** (`/camera/*`)
   - `GET /camera/status` - Returns camera status

5. **WebRTC API** (`/webrtc/*`)
   - `GET /webrtc/config` - Returns LiveKit configuration
   - `GET /webrtc/token` - Returns access token for WebRTC connection

### Files Removed

- **`app/routers/valve_old.py`** - Obsolete implementation, replaced by simplified `valve.py`
- **`assets/js/dashboard.js`** (original) - Not loaded/used by `index.html`

### Current Router Status

| Router File | Prefix | Status |
|------------|--------|--------|
| `valve.py` | `/api/valve` | ✅ Active |
| `stats.py` | `/api` | ✅ Active |
| `stepper.py` | `/api/stepper` | ✅ Active |
| `camera.py` | `/camera` | ✅ Active |
| `webrtc.py` | `/webrtc` | ✅ Active |

---

## Dashboard Assets

Modern, minimal control dashboard for the UU Plastination lab monitoring system.

### Design System

#### Colors
- **Background**: `#0B0B0F` (ultra-dark)
- **Surface**: `#111216` (card background)
- **Surface-2**: `#15171D` (elevated elements)
- **Border**: `rgba(255,255,255,0.08)` (subtle borders)
- **Accent**: `#0A84FF` (iOS blue)
- **Positive**: `#30D158` (success states)
- **Warning**: `#FFD60A` (warnings)
- **Danger**: `#FF453A` (errors, recording)

#### Typography
- **Font Stack**: SF Pro Text, SF Pro Display, -apple-system, BlinkMacSystemFont, Inter, Segoe UI
- **Sizes**: Base 16px, headings use optical sizing (H1: 28px, H2: 22px, H3: 18px)
- **Mono**: SF Mono for code/data display

#### Layout
- **12-column grid** on desktop (xl: ≥1280px)
- **6-column grid** on tablet (md: 768–1279px)
- **Full-width stack** on mobile (<768px)
- **Grid gaps**: 16px (mobile), 20px (desktop)

#### Cards
- Border radius: `24px` (--radius-2xl)
- Padding: `20px` (mobile), `24px` (desktop)
- Shadow: Subtle elevation with top highlight
- Border: 1px solid rgba(255,255,255,0.08)

### JavaScript Architecture

#### Mock Data Mode

Set `MOCK_DATA = true` at the top of `dashboard.js` to use simulated data:

```javascript
const MOCK_DATA = true; // Change to false for production
```

#### Key Classes

- **`Dashboard`**: Main orchestrator. Initializes all subsystems.
- **`ThemeManager`**: Handles light/dark mode toggle.
- **`RecordingControl`**: Manages the recording button in the header.
- **`CameraManager`**: Fullscreen toggle (button or `f` key).
- **`BubbleChart`**: Simple canvas-based line chart with area fill.
- **`DataManager`**: Polls APIs every 5 seconds.
- **`ValveController`**: Sends valve commands.

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `t` | Toggle light/dark theme |
| `f` | Fullscreen camera |
| `Ctrl+r` | Toggle recording |
| `?` | Show help |

### Accessibility

- All interactive elements have min 44×44px hit areas
- Keyboard navigation supported (Tab, Enter, Space)
- Focus rings use accent color (2px outline)
- `aria-label` and `role` attributes on key widgets
- Reduced motion support (`prefers-reduced-motion`)

### Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+

Uses modern CSS (custom properties, grid, backdrop-filter) and ES2020 JavaScript (optional chaining, nullish coalescing).

---

## Dependencies

Required Python packages (see `requirements.txt`):
```bash
pip install pyserial  # For serial valve communication
pip install python-dotenv  # For .env file loading
pip install picamera2  # For Pi camera support (Pi only)
```

---

## Security Notes

⚠️ **Development Setup uses default credentials:**
- API Key: `devkey`
- API Secret: `devsecret`

**For production:**
1. Generate new credentials
2. Update both `.env` and `webrtc/docker-compose.yml`
3. Enable HTTPS
4. Configure authentication
5. Restrict firewall rules

---

*Built with ❤️ for the UU Plastination Lab*
