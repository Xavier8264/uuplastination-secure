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

# UU Plastination — Secure Portal

This secure site hosts private tools and APIs for the AI camera/plastination project.

## What’s here

- `index.html` — Secure UI with telemetry and actuator controls
- `app/` — FastAPI app served behind Nginx
	- `routers/stats.py` — Pi telemetry endpoint (`GET /api/stats`)
	- `routers/stepper.py` — Stepper control endpoints under `/api/stepper`
- `nginx/secure_api_location.conf` — Nginx `location /api/` proxy include
- `systemd/uuplastination-stats.service` — Example unit for uvicorn app
- `requirements.txt` — Python deps

## Stepper control API

All routes are available only via the secure origin and proxied by Nginx to the local FastAPI app. Default bind: `127.0.0.1:8000`.

Base path: `/api/stepper`

- `GET /healthz` — simple 200 OK
- `GET /status` — returns `{ enabled, moving, position_steps, worker_alive, last_error, steps_per_rev, default_rpm }`
- `POST /enable` — asserts ENABLE pin (or treated as always-enabled if no pin)
- `POST /disable` — de-asserts ENABLE; errors with 409 if moving
- `POST /abort` — cancels current move if running
- `POST /step?steps=±N&rpm=R&direction=fwd|rev` — non-blocking move; returns `moving`
- `POST /open` — convenience forward move of `STEPPER_OPEN_STEPS` (default 200)
- `POST /close` — convenience reverse move of `STEPPER_CLOSE_STEPS` (default -200)

Notes:
- Uses basic STEP/DIR/ENABLE control (A4988/DRV8825-style). Timing is best-effort via Python sleeps; adequate for manual control.
- Concurrency-safe: rejects a new move with HTTP 409 if already moving; use `/abort` to stop.

## GPIO configuration

The controller reads environment variables (BCM numbering):

- `STEPPER_PIN_STEP` (default 23)
- `STEPPER_PIN_DIR` (default 24)
- `STEPPER_PIN_ENABLE` (default 18; set to `-1` or unset to omit enable control)
- `STEPPER_STEPS_PER_REV` (default 200)
- `STEPPER_DEFAULT_RPM` (default 60)
- `STEPPER_INVERT_ENABLE` (default 1; many drivers use active-low ENABLE)
- `STEPPER_OPEN_STEPS` (default 200)
- `STEPPER_CLOSE_STEPS` (default -200)

## Deploy

1) Install dependencies on the Pi (within an isolated venv):

- `fastapi`
- `uvicorn[standard]`
- `psutil`
- (Optional) `RPi.GPIO` — available by default on Raspberry Pi OS; for 64-bit Bullseye/Bookworm use the packaged module.

2) Systemd unit: copy `systemd/uuplastination-stats.service` to `/etc/systemd/system/` and edit Environment lines to match pinout. Ensure the WorkingDirectory points to the deployed path (e.g., `/var/www/uuplastination-secure`).

```ini
[Service]
Environment=STEPPER_PIN_STEP=23
Environment=STEPPER_PIN_DIR=24
Environment=STEPPER_PIN_ENABLE=18
Environment=STEPPER_STEPS_PER_REV=200
Environment=STEPPER_DEFAULT_RPM=60
Environment=STEPPER_INVERT_ENABLE=1
```

Then:

```bash
sudo systemctl daemon-reload
sudo systemctl enable uuplastination-stats --now
sudo systemctl status uuplastination-stats
```

3) Nginx: include `nginx/secure_api_location.conf` inside the secure server block hosting `/secure`. This proxies `/secure/api/` → `http://127.0.0.1:8000/api/`.

Add rate limiting for actuator routes if desired:

```nginx
location /api/stepper/ {
		limit_req zone=actuator burst=5 nodelay;
		proxy_pass http://127.0.0.1:8000/api/stepper/;
}
```

4) Cloudflare: keep TLS termination at Cloudflare; only expose the secure origin. Gate with Cloudflare Access or HTTP Basic auth.

## Frontend controls

`index.html` includes a "Stepper Motor Control" card with buttons that call the API through the same origin. Status polls every 3 seconds.

## Security notes

- API binds to 127.0.0.1 only. Do not expose it directly.
- Place actuator routes only under the secure vhost. Gate with Cloudflare Access or Basic auth.
- Consider CSRF exposure minimal because only POST methods perform actions and the site is behind access controls; still, same-site cookies only.
- Add Nginx rate limits on `/api/stepper/*`.

## Troubleshooting

- Check service: `systemctl status uuplastination-stats` and `journalctl -u uuplastination-stats -e`
- Health: `curl -s http://127.0.0.1:8000/api/stepper/healthz`
- If GPIO import fails on dev: routes still work but don’t toggle pins; errors appear in `/api/stepper/status` under `last_error`.
