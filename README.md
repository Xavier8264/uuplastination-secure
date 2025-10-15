# uuplastination-secure

## Pi Stats Feature

This secure portal now exposes a read-only system telemetry API and a small footer widget that auto-refreshes every 5 seconds to show Raspberry Pi health.

- Endpoint: `/api/stats` (FastAPI on 127.0.0.1:8000, proxied only within the secure site)
- Returns JSON: CPU temp/usage, memory totals/used/percent, uptime seconds, network IPv4 addresses (non-loopback) and internet reachability, systemd service states (camera, stepper, nginx, tailscaled, webhook-deploy), simple port checks (RTSP 8554 and local HTTP 8000), OS info (PRETTY_NAME, kernel, arch), and a timestamp.
- Frontend: The secure page footer fetches `/api/stats` and renders concise badges and info. If unavailable, it shows a graceful “Failed to load stats”.

### Requirements on the Pi

- Python 3
- Packages: `fastapi`, `uvicorn[standard]`, `psutil` (see `requirements.txt`)
- For true CPU temperature: install `libraspberrypi-bin` (provides `vcgencmd`)

### Systemd service (template)

This repo includes a template unit at `systemd/uuplastination-stats.service`. The real unit should be placed at `/etc/systemd/system/uuplastination-stats.service` and adjusted if your working directory differs.

Suggested enable/start (run as root):

Enable and start in one line:

`systemctl enable --now uuplastination-stats.service`

Notes:
- It runs `uvicorn app.main:app` on `127.0.0.1:8000` and restarts on failure.
- Environment variables can override service names and ports.

### Nginx proxy (secure site only)

Include `nginx/secure_api_location.conf` within the secure server block. It proxies `/api/` to `http://127.0.0.1:8000/api/`. Do not add this to the public server block.

### Configurable names/ports

Environment variables recognized by the API:
- `SERVICE_CAMERA` (default `camera-stream.service`)
- `SERVICE_STEPPER` (default `valve-control.service`)
- `PORT_RTSP` (default `8554`)
- `PORT_API` (default `8000`)

### Security

- The API is only reachable via the secure site’s Nginx server block. Do not expose port 8000 publicly.
- The endpoint avoids leaking sensitive environment data and handles probe failures by returning nulls/placeholders instead of errors.
