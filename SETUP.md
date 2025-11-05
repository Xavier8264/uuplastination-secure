# UU Plastination Control System - Secure Dashboard

A modern, Apple-inspired web interface for controlling plastination equipment with live camera feed and valve control via Raspberry Pi.

## Features

- **Live Camera Feed**: MJPEG streaming from Raspberry Pi Camera (CSI port)
- **Valve Control**: Control stepper motor via GPIO pins with configurable open/close increments
- **System Monitoring**: Real-time CPU temp, memory usage, and system health
- **Bubble Rate Monitoring**: Track and visualize bubble rates over time
- **Responsive Design**: Beautiful Apple-inspired UI that works on desktop and mobile

## Hardware Requirements

- Raspberry Pi (tested on Pi 4/5)
- Raspberry Pi Camera Module (connected to CSI port)
- Stepper motor + driver (A4988, DRV8825, or similar)
- GPIO connections for valve control

## Quick Setup

### 1. Install System Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and pip (usually pre-installed)
sudo apt install python3 python3-pip python3-venv -y

# Install camera support
sudo apt install python3-picamera2 -y

# Install GPIO library (usually pre-installed on Raspberry Pi OS)
# If needed:
# sudo apt install python3-rpi.gpio -y
```

### 2. Enable Camera

```bash
# For Raspberry Pi OS Bullseye or later
sudo raspi-config
# Navigate to: Interface Options > Camera > Enable
# Reboot when prompted
```

### 3. Clone and Setup Application

```bash
cd ~
git clone https://github.com/Xavier8264/uuplastination-secure.git
cd uuplastination-secure

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

### 4. Configure GPIO Pins

Copy the example environment file and edit it:

```bash
cp .env.example .env
nano .env
```

Set your GPIO pins according to your wiring. Default configuration:
- `VALVE_PIN_STEP=23` (BCM GPIO 23, Physical Pin 16)
- `VALVE_PIN_DIR=24` (BCM GPIO 24, Physical Pin 18)
- `VALVE_PIN_ENABLE=18` (BCM GPIO 18, Physical Pin 12)

### 5. Run the Application

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Run with uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The dashboard will be available at: `http://your-pi-ip:8000`

## GPIO Pin Configuration

The system uses **BCM GPIO numbering** (not physical pin numbers). You can configure any available GPIO pins via environment variables.

### Example Wiring for A4988/DRV8825 Driver

| Raspberry Pi | Physical Pin | → | Stepper Driver |
|--------------|--------------|---|----------------|
| GPIO 23      | Pin 16       | → | STEP           |
| GPIO 24      | Pin 18       | → | DIR            |
| GPIO 18      | Pin 12       | → | ENABLE         |
| GND          | Any GND      | → | GND            |

### Choosing Different GPIO Pins

Edit `.env` file:

```bash
# Example: Using different pins
VALVE_PIN_STEP=17  # BCM 17 (Physical Pin 11)
VALVE_PIN_DIR=27   # BCM 27 (Physical Pin 13)
VALVE_PIN_ENABLE=22 # BCM 22 (Physical Pin 15)
```

**Available GPIO Pins (BCM)**: 2, 3, 4, 17, 27, 22, 10, 9, 11, 5, 6, 13, 19, 26, 23, 24, 25, 8, 7, 12, 16, 20, 21

**Avoid using**: GPIO 14, 15 (UART), GPIO 0, 1 (reserved)

## Camera Configuration

The system supports Raspberry Pi Camera modules connected to the CSI port.

### Using Different Camera Port

If you have multiple cameras:

```bash
# In .env file
CAMERA_NUM=0  # Use first camera (CAM0)
# or
CAMERA_NUM=1  # Use second camera (CAM1)
```

### Adjusting Resolution and Framerate

```bash
# In .env file
CAMERA_WIDTH=1920
CAMERA_HEIGHT=1080
CAMERA_FPS=30
```

For better performance on older Pi models, try:
```bash
CAMERA_WIDTH=1280
CAMERA_HEIGHT=720
CAMERA_FPS=15
```

## API Endpoints

### Camera
- `GET /camera/stream.mjpg` - MJPEG video stream
- `GET /camera/snapshot` - Single JPEG snapshot
- `GET /camera/status` - Camera status
- `POST /camera/start` - Start camera
- `POST /camera/stop` - Stop camera

### Valve Control
- `POST /api/valve/open` - Open valve by 5%
- `POST /api/valve/close` - Close valve by 5%
- `GET /api/valve/position` - Get current position

### Stepper Motor (Advanced)
- `GET /api/stepper/status` - Get stepper status
- `POST /api/stepper/enable` - Enable motor
- `POST /api/stepper/disable` - Disable motor
- `POST /api/stepper/step?steps=200&rpm=60` - Move specific steps
- `POST /api/stepper/abort` - Emergency stop

### System Monitoring
- `GET /api/system/metrics` - System metrics (CPU, memory, uptime)
- `GET /api/stats` - Detailed system statistics

## Running as a Service

Create a systemd service to run on boot:

```bash
sudo nano /etc/systemd/system/plastination-dashboard.service
```

Add:

```ini
[Unit]
Description=UU Plastination Dashboard
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/uuplastination-secure
Environment="PATH=/home/pi/uuplastination-secure/venv/bin"
EnvironmentFile=/home/pi/uuplastination-secure/.env
ExecStart=/home/pi/uuplastination-secure/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable plastination-dashboard.service
sudo systemctl start plastination-dashboard.service

# Check status
sudo systemctl status plastination-dashboard.service
```

## Troubleshooting

### Camera Issues

```bash
# Test camera
libcamera-hello

# Check if camera is detected
vcgencmd get_camera

# View camera logs
journalctl -u plastination-dashboard -f | grep camera
```

### GPIO Permission Issues

```bash
# Add user to gpio group
sudo usermod -a -G gpio $USER

# Logout and login again for changes to take effect
```

### Check Application Logs

```bash
# If running as service
sudo journalctl -u plastination-dashboard -f

# If running manually
# Logs will appear in terminal
```

### Port Already in Use

```bash
# Find process using port 8000
sudo lsof -i :8000

# Kill process if needed
sudo kill -9 <PID>

# Or use different port
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

## Security Notes

- This system is designed for internal lab use
- For production deployment, add authentication (JWT, OAuth2, etc.)
- Use NGINX as reverse proxy with HTTPS
- Restrict access via firewall rules
- Keep system and dependencies updated

## Development

```bash
# Install dev dependencies
pip install pytest black flake8

# Run tests
pytest

# Format code
black app/

# Lint
flake8 app/
```

## License

MIT License - See LICENSE file for details

## Contributing

Pull requests are welcome! For major changes, please open an issue first.

## Support

For issues or questions, please open an issue on GitHub.
