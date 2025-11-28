# UU Plastination — Setup & Configuration Guide

Complete guide for setting up the UU Plastination Control System on Raspberry Pi.

---

## Table of Contents

- [Quick Start](#quick-start)
- [System Requirements](#system-requirements)
- [Installation](#installation)
- [GPIO Configuration](#gpio-configuration)
- [Camera Configuration](#camera-configuration)
- [Running the Application](#running-the-application)
- [Environment Variables Reference](#environment-variables-reference)
- [Troubleshooting](#troubleshooting)

---

## Quick Start

### ✅ System Status: OPERATIONAL

All critical issues have been resolved. Your live webcam setup is now functional.

### Start Everything
```bash
./start_services.sh
```

### Check Status
```bash
./check_status.sh
```

### Access Dashboard
Open browser to: **http://127.0.0.1:8000/**

### Stop Services
```bash
./stop_services.sh
```

---

## System Requirements

### Hardware
- Raspberry Pi 4 or 5 with Raspberry Pi OS (Bullseye or newer, 64-bit recommended)
- Raspberry Pi Camera Module (connected to CSI port)
- Power supply appropriate for your Pi model

### For Stepper Motor Control
- Stepper motor (NEMA 17 or similar)
- Stepper driver (A4988, DRV8825, or compatible)
- Appropriate power supply for motor (12V-24V typical)
- GPIO connections

### For Serial Valve Control
- Arduino or compatible microcontroller running valve control firmware
- USB connection to Raspberry Pi (`/dev/ttyACM0`)

---

## Installation

### 1. Install System Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and pip (usually pre-installed)
sudo apt install python3 python3-pip python3-venv -y

# Install camera support
sudo apt install python3-picamera2 libraspberrypi-bin -y

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

### 4. Configure Environment

Copy the example environment file and edit it:

```bash
cp .env.example .env
nano .env
```

---

## GPIO Configuration

The system uses **BCM GPIO numbering** (not physical pin numbers). You can configure any available GPIO pins via environment variables.

### Raspberry Pi GPIO Pinout (BCM Numbering)

```
     3.3V  (1)  (2)  5V
    GPIO2  (3)  (4)  5V
    GPIO3  (5)  (6)  GND
    GPIO4  (7)  (8)  GPIO14 (UART TX)
      GND  (9) (10)  GPIO15 (UART RX)
   GPIO17 (11) (12)  GPIO18 (PWM)
   GPIO27 (13) (14)  GND
   GPIO22 (15) (16)  GPIO23 ← STEP (default)
     3.3V (17) (18)  GPIO24 ← DIR (default)
   GPIO10 (19) (20)  GND
    GPIO9 (21) (22)  GPIO25
   GPIO11 (23) (24)  GPIO8
      GND (25) (26)  GPIO7
    GPIO0 (27) (28)  GPIO1
    GPIO5 (29) (30)  GND
    GPIO6 (31) (32)  GPIO12
   GPIO13 (33) (34)  GND
   GPIO19 (35) (36)  GPIO16
   GPIO26 (37) (38)  GPIO20
      GND (39) (40)  GPIO21
```

### Default Wiring for A4988/DRV8825 Driver

| Raspberry Pi | Physical Pin | → | Stepper Driver |
|--------------|--------------|---|----------------|
| GPIO 23      | Pin 16       | → | STEP           |
| GPIO 24      | Pin 18       | → | DIR            |
| GPIO 18      | Pin 12       | → | ENABLE         |
| GND          | Any GND      | → | GND            |

### Recommended Pin Configurations

#### Option 1 (Default)
- **STEP**: GPIO 23 (Physical Pin 16)
- **DIR**: GPIO 24 (Physical Pin 18)
- **ENABLE**: GPIO 18 (Physical Pin 12)
- **GND**: Any GND pin

#### Option 2 (Alternative)
- **STEP**: GPIO 17 (Physical Pin 11)
- **DIR**: GPIO 27 (Physical Pin 13)
- **ENABLE**: GPIO 22 (Physical Pin 15)
- **GND**: Any GND pin

#### Option 3 (Compact Grouping)
- **STEP**: GPIO 5 (Physical Pin 29)
- **DIR**: GPIO 6 (Physical Pin 31)
- **ENABLE**: GPIO 13 (Physical Pin 33)
- **GND**: Pin 30 or 34

### Safe GPIO Pins to Use

✅ **Safe to use**: 4, 5, 6, 12, 13, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27

⚠️ **Use with caution** (special functions):
- GPIO 0, 1: Reserved for ID EEPROM
- GPIO 2, 3: I2C (if using I2C devices)
- GPIO 7, 8, 9, 10, 11: SPI (if using SPI devices)
- GPIO 14, 15: UART (if using serial console)

### Choosing Different GPIO Pins

Edit `.env` file:

```bash
# Example: Using different pins
VALVE_PIN_STEP=17  # BCM 17 (Physical Pin 11)
VALVE_PIN_DIR=27   # BCM 27 (Physical Pin 13)
VALVE_PIN_ENABLE=22 # BCM 22 (Physical Pin 15)
```

### Example .env Configurations

#### Configuration for A4988 Driver (Active-Low Enable)
```bash
VALVE_PIN_STEP=23
VALVE_PIN_DIR=24
VALVE_PIN_ENABLE=18
STEPPER_INVERT_ENABLE=1
```

#### Configuration for TMC2208 Driver (Active-High Enable)
```bash
VALVE_PIN_STEP=23
VALVE_PIN_DIR=24
VALVE_PIN_ENABLE=18
STEPPER_INVERT_ENABLE=0
```

#### Configuration Without Enable Pin
```bash
VALVE_PIN_STEP=23
VALVE_PIN_DIR=24
VALVE_PIN_ENABLE=-1
STEPPER_INVERT_ENABLE=1
```

### Testing Your GPIO Configuration

After changing pins, test with:

```bash
# Enable the motor
curl -X POST http://localhost:8000/api/stepper/enable

# Move 10 steps forward
curl -X POST "http://localhost:8000/api/stepper/step?steps=10"

# Check status
curl http://localhost:8000/api/stepper/status

# Disable the motor
curl -X POST http://localhost:8000/api/stepper/disable
```

---

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

---

## Running the Application

### Manual Startup

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Run with uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The dashboard will be available at: `http://your-pi-ip:8000`

### Running as a Service

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

---

## Environment Variables Reference

### Camera Settings
```bash
CAMERA_NUM=0           # Camera port (0 for CAM0, 1 for CAM1)
CAMERA_WIDTH=1920      # Resolution width
CAMERA_HEIGHT=1080     # Resolution height
CAMERA_FPS=30          # Frame rate
```

### Stepper Motor GPIO (BCM Numbering)
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

### Serial Valve Settings
```bash
VALVE_SERIAL_BAUD=115200  # Baud rate for /dev/ttyACM0
```

### LiveKit/WebRTC
```bash
LIVEKIT_HOST=https://livekit.yourdomain.com
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret
LIVEKIT_ICE_SERVERS=turns:turn.yourdomain.com:5349?transport=tcp
WEBRTC_DISABLE=0          # Set to 1 to force MJPEG fallback
```

### System Monitoring
```bash
SERVICE_CAMERA=camera-stream.service   # Systemd service name to monitor
SERVICE_STEPPER=valve-control.service  # Systemd service name to monitor
PORT_RTSP=8554                         # RTSP port to check
PORT_API=8000                          # API port to check
```

---

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

# Create udev rule for GPIO access
echo 'SUBSYSTEM=="gpio", GROUP="gpio", MODE="0660"' | sudo tee /etc/udev/rules.d/99-gpio.rules

# Reload udev rules
sudo udevadm control --reload-rules
sudo udevadm trigger

# Logout and login again for changes to take effect
```

### Motor Doesn't Move

1. Check power supply to driver
2. Verify GPIO pins are correct
3. Check if enable is active
4. Try inverting enable: `STEPPER_INVERT_ENABLE=0`

### Motor Moves in Wrong Direction

Swap the DIR pin value or modify wiring:
- Option 1: Change DIR pin in `.env`
- Option 2: Swap motor coil wires

### Motor Stutters or Skips Steps

1. Reduce RPM: `STEPPER_DEFAULT_RPM=30`
2. Check current limit on driver
3. Ensure adequate power supply

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

---

## System Overview Diagram

```
┌─────────────────────────────────────────────┐
│         Browser (http://127.0.0.1:8000)     │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│     FastAPI (port 8000)                     │
│     - Camera endpoints (/camera/)           │
│     - WebRTC config (/webrtc/)              │
│     - System stats (/stats/)                │
└─────────────────┬───────────────────────────┘
                  │
        ┌─────────┴──────────┐
        │                    │
┌───────▼────────┐  ┌────────▼─────────┐
│ LiveKit        │  │ Camera           │
│ (port 7880)    │  │ (/dev/video*)    │
│ - Signaling    │  │ - MJPEG stream   │
│ - SFU          │  │ - Snapshots      │
└────────────────┘  └──────────────────┘
```

---

## Security Notes

- This system is designed for internal lab use
- For production deployment, add authentication (JWT, OAuth2, etc.)
- Use NGINX as reverse proxy with HTTPS
- Restrict access via firewall rules
- Keep system and dependencies updated
- Keep `.env` file permissions restricted: `chmod 600 .env`

---

## Need Help?

- Check the main [README.md](README.md) for overview
- See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for production deployment
- See [TECHNICAL_REFERENCE.md](TECHNICAL_REFERENCE.md) for API documentation
- Open an issue on GitHub with detailed information
