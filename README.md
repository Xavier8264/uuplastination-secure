# UU Plastination — Secure Control System# uuplastination-secure



Modern, Apple-inspired web dashboard for controlling plastination equipment with live camera feed, valve control, and system monitoring on Raspberry Pi.## Pi Stats Feature



## ✨ FeaturesThis secure portal now exposes a read-only system telemetry API and a small footer widget that auto-refreshes every 5 seconds to show Raspberry Pi health.



- 📹 **Live Camera Feed** - MJPEG streaming from Raspberry Pi Camera (CSI port)- Endpoint: `/api/stats` (FastAPI on 127.0.0.1:8000, proxied only within the secure site)

- 🦾 **Valve Control** - Stepper motor control via configurable GPIO pins- Returns JSON: CPU temp/usage, memory totals/used/percent, uptime seconds, network IPv4 addresses (non-loopback) and internet reachability, systemd service states (camera, stepper, nginx, tailscaled, webhook-deploy), simple port checks (RTSP 8554 and local HTTP 8000), OS info (PRETTY_NAME, kernel, arch), and a timestamp.

- 📊 **System Monitoring** - Real-time CPU, memory, and health metrics- Frontend: The secure page footer fetches `/api/stats` and renders concise badges and info. If unavailable, it shows a graceful “Failed to load stats”.

- 🫧 **Bubble Detection** - Track and visualize bubble rates (placeholder for AI integration)

- 🎨 **Beautiful UI** - Apple-inspired responsive design### Requirements on the Pi



## 🚀 Quick Start- Python 3

- Packages: `fastapi`, `uvicorn[standard]`, `psutil` (see `requirements.txt`)

**For detailed setup instructions, see [SETUP.md](SETUP.md)**- For true CPU temperature: install `libraspberrypi-bin` (provides `vcgencmd`)



**For GPIO pin configuration, see [GPIO_SETUP.md](GPIO_SETUP.md)**### Systemd service (template)



### PrerequisitesThis repo includes a template unit at `systemd/uuplastination-stats.service`. The real unit should be placed at `/etc/systemd/system/uuplastination-stats.service` and adjusted if your working directory differs.



- Raspberry Pi 4 or 5 with Raspberry Pi OSSuggested enable/start (run as root):

- Raspberry Pi Camera Module (connected to CSI port)

- Stepper motor + driver (A4988, DRV8825, or similar)Enable and start in one line:



### Basic Installation`systemctl enable --now uuplastination-stats.service`



```bashNotes:

# Clone repository- It runs `uvicorn app.main:app` on `127.0.0.1:8000` and restarts on failure.

git clone https://github.com/Xavier8264/uuplastination-secure.git- Environment variables can override service names and ports.

cd uuplastination-secure

### Nginx proxy (secure site only)

# Install dependencies

python3 -m venv venvInclude `nginx/secure_api_location.conf` within the secure server block. It proxies `/api/` to `http://127.0.0.1:8000/api/`. Do not add this to the public server block.

source venv/bin/activate

pip install -r requirements.txt### Configurable names/ports



# Configure GPIO pins# UU Plastination — Secure Portal

cp .env.example .env

nano .env  # Edit to match your wiringThis secure site hosts private tools and APIs for the AI camera/plastination project.



# Run the application## What’s here

uvicorn app.main:app --host 0.0.0.0 --port 8000

```- `index.html` — Secure UI with telemetry and actuator controls

- `app/` — FastAPI app served behind Nginx

Access at: `http://your-pi-ip:8000`	- `routers/stats.py` — Pi telemetry endpoint (`GET /api/stats`)

	- `routers/stepper.py` — Stepper control endpoints under `/api/stepper`

## 🔌 GPIO Pin Configuration- `nginx/secure_api_location.conf` — Nginx `location /api/` proxy include

- `systemd/uuplastination-stats.service` — Example unit for uvicorn app

The system uses **BCM GPIO numbering**. Default pins:- `requirements.txt` — Python deps

- **STEP**: GPIO 23 (Physical Pin 16)

- **DIR**: GPIO 24 (Physical Pin 18)  ## Stepper control API

- **ENABLE**: GPIO 18 (Physical Pin 12)

All routes are available only via the secure origin and proxied by Nginx to the local FastAPI app. Default bind: `127.0.0.1:8000`.

**You can use any available GPIO pins** - just update the `.env` file:

Base path: `/api/stepper`

```bash

VALVE_PIN_STEP=23    # Change to your STEP pin- `GET /healthz` — simple 200 OK

VALVE_PIN_DIR=24     # Change to your DIR pin- `GET /status` — returns `{ enabled, moving, position_steps, worker_alive, last_error, steps_per_rev, default_rpm }`

VALVE_PIN_ENABLE=18  # Change to your ENABLE pin- `POST /enable` — asserts ENABLE pin (or treated as always-enabled if no pin)

```- `POST /disable` — de-asserts ENABLE; errors with 409 if moving

- `POST /abort` — cancels current move if running

See [GPIO_SETUP.md](GPIO_SETUP.md) for complete pinout and wiring guide.- `POST /step?steps=±N&rpm=R&direction=fwd|rev` — non-blocking move; returns `moving`

- `POST /open` — convenience forward move of `STEPPER_OPEN_STEPS` (default 200)

## 📹 Camera Setup- `POST /close` — convenience reverse move of `STEPPER_CLOSE_STEPS` (default -200)



Supports Raspberry Pi Camera Module on CSI port. Configure in `.env`:Notes:

- Uses basic STEP/DIR/ENABLE control (A4988/DRV8825-style). Timing is best-effort via Python sleeps; adequate for manual control.

```bash- Concurrency-safe: rejects a new move with HTTP 409 if already moving; use `/abort` to stop.

CAMERA_NUM=0          # Camera port (0 for CAM0, 1 for CAM1)

CAMERA_WIDTH=1920     # Resolution width## GPIO configuration

CAMERA_HEIGHT=1080    # Resolution height

CAMERA_FPS=30         # Frame rateThe controller reads environment variables (BCM numbering):

```

- `STEPPER_PIN_STEP` (default 23)

## 🔧 API Endpoints- `STEPPER_PIN_DIR` (default 24)

- `STEPPER_PIN_ENABLE` (default 18; set to `-1` or unset to omit enable control)

### Camera- `STEPPER_STEPS_PER_REV` (default 200)

- `GET /camera/stream.mjpg` - Live MJPEG stream- `STEPPER_DEFAULT_RPM` (default 60)

- `GET /camera/snapshot` - Single frame capture- `STEPPER_INVERT_ENABLE` (default 1; many drivers use active-low ENABLE)

- `GET /camera/status` - Camera status- `STEPPER_OPEN_STEPS` (default 200)

- `STEPPER_CLOSE_STEPS` (default -200)

### Valve Control  

- `POST /api/valve/open` - Open valve by 5%## Deploy

- `POST /api/valve/close` - Close valve by 5%

- `GET /api/valve/position` - Current position1) Install dependencies on the Pi (within an isolated venv):



### Stepper Motor (Advanced)- `fastapi`

- `GET /api/stepper/status` - Motor status- `uvicorn[standard]`

- `POST /api/stepper/enable` - Enable motor- `psutil`

- `POST /api/stepper/disable` - Disable motor- (Optional) `RPi.GPIO` — available by default on Raspberry Pi OS; for 64-bit Bullseye/Bookworm use the packaged module.

- `POST /api/stepper/step?steps=200` - Move specific steps

- `POST /api/stepper/abort` - Emergency stop2) Systemd unit: copy `systemd/uuplastination-stats.service` to `/etc/systemd/system/` and edit Environment lines to match pinout. Ensure the WorkingDirectory points to the deployed path (e.g., `/var/www/uuplastination-secure`).



### System Monitoring```ini

- `GET /api/system/metrics` - System health (CPU, memory, uptime)[Service]

- `GET /api/stats` - Detailed statisticsEnvironment=STEPPER_PIN_STEP=23

Environment=STEPPER_PIN_DIR=24

## 🏭 Production DeploymentEnvironment=STEPPER_PIN_ENABLE=18

Environment=STEPPER_STEPS_PER_REV=200

### Run as Systemd ServiceEnvironment=STEPPER_DEFAULT_RPM=60

Environment=STEPPER_INVERT_ENABLE=1

```bash```

sudo nano /etc/systemd/system/plastination-dashboard.service

```Then:



See [SETUP.md](SETUP.md) for complete service configuration.```bash

sudo systemctl daemon-reload

```bashsudo systemctl enable uuplastination-stats --now

sudo systemctl enable plastination-dashboardsudo systemctl status uuplastination-stats

sudo systemctl start plastination-dashboard```

```

3) Nginx: include `nginx/secure_api_location.conf` inside the secure server block hosting `/secure`. This proxies `/secure/api/` → `http://127.0.0.1:8000/api/`.

### Nginx Reverse Proxy

Add rate limiting for actuator routes if desired:

Include `nginx/secure_api_location.conf` in your secure server block:

```nginx

```nginxlocation /api/stepper/ {

server {		limit_req zone=actuator burst=5 nodelay;

    listen 443 ssl;		proxy_pass http://127.0.0.1:8000/api/stepper/;

    server_name your-domain.com;}

    ```

    # Include API proxy

    include /path/to/nginx/secure_api_location.conf;4) Cloudflare: keep TLS termination at Cloudflare; only expose the secure origin. Gate with Cloudflare Access or HTTP Basic auth.

    

    # Rate limiting for actuator endpoints## Frontend controls

    location /api/stepper/ {

        limit_req zone=actuator burst=5 nodelay;`index.html` includes a "Stepper Motor Control" card with buttons that call the API through the same origin. Status polls every 3 seconds.

        proxy_pass http://127.0.0.1:8000/api/stepper/;

    }## Security notes

}

```- API binds to 127.0.0.1 only. Do not expose it directly.

- Place actuator routes only under the secure vhost. Gate with Cloudflare Access or Basic auth.

## 🔒 Security- Consider CSRF exposure minimal because only POST methods perform actions and the site is behind access controls; still, same-site cookies only.

- Add Nginx rate limits on `/api/stepper/*`.

- API binds to `127.0.0.1` only by default

- Use Nginx reverse proxy with SSL/TLS## Troubleshooting

- Add authentication (Cloudflare Access, HTTP Basic Auth, etc.)

- Implement rate limiting on actuator endpoints- Check service: `systemctl status uuplastination-stats` and `journalctl -u uuplastination-stats -e`

- Keep system and dependencies updated- Health: `curl -s http://127.0.0.1:8000/api/stepper/healthz`

- If GPIO import fails on dev: routes still work but don’t toggle pins; errors appear in `/api/stepper/status` under `last_error`.

## 📚 Documentation

- [SETUP.md](SETUP.md) - Complete setup guide
- [GPIO_SETUP.md](GPIO_SETUP.md) - GPIO pin configuration and wiring
- [.env.example](.env.example) - Environment configuration reference

## 🐛 Troubleshooting

### Camera not working
```bash
libcamera-hello  # Test camera
vcgencmd get_camera  # Check detection
```

### Motor not moving
1. Check power supply to driver
2. Verify GPIO pins in `.env`
3. Try: `curl -X POST http://localhost:8000/api/stepper/enable`

### Check logs
```bash
sudo journalctl -u plastination-dashboard -f
```

## 🤝 Contributing

Pull requests are welcome! For major changes, please open an issue first.

## 📄 License

MIT License - See LICENSE file for details

## 📞 Support

For issues or questions, open an issue on GitHub.

---

**Previous documentation backed up to `README.md.backup`**
