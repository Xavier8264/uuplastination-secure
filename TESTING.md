# Testing Checklist

Use this checklist to verify your installation is working correctly.

## Pre-Installation Tests

### Hardware Check
- [ ] Raspberry Pi is powered on and accessible
- [ ] Raspberry Pi Camera is connected to CSI port
- [ ] Stepper motor driver is connected to power supply
- [ ] GPIO wires are connected from Pi to stepper driver
- [ ] You know which GPIO pins you're using (BCM numbering)

### Software Check
- [ ] Raspberry Pi OS is installed and updated
- [ ] Python 3 is installed (`python3 --version`)
- [ ] Camera is enabled in raspi-config
- [ ] You can access Pi via SSH or direct connection

## Installation Tests

### Basic Setup
- [ ] Repository cloned successfully
- [ ] Virtual environment created (`venv/` directory exists)
- [ ] Dependencies installed without errors
- [ ] `.env` file created from `.env.example`
- [ ] GPIO pins configured in `.env` to match your wiring

### Camera Test (Hardware)
```bash
# Test camera before running app
libcamera-hello
```
- [ ] Camera preview window appears
- [ ] Image is clear and in focus
- [ ] No error messages

```bash
# Check camera detection
vcgencmd get_camera
```
- [ ] Output shows `detected=1` and `supported=1`

### GPIO Test (Optional - only if you have test equipment)
```bash
# Test GPIO access
python3 << EOF
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
print("GPIO access OK")
GPIO.cleanup()
EOF
```
- [ ] No permission errors
- [ ] Script completes successfully

## Application Tests

### Start Application
```bash
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
- [ ] Server starts without errors
- [ ] No import errors
- [ ] Listening on 0.0.0.0:8000

### Web Interface Tests

#### Access Dashboard
Open `http://your-pi-ip:8000` in browser
- [ ] Page loads without errors
- [ ] Apple-inspired design appears
- [ ] No 404 errors in browser console

#### Camera Widget
- [ ] Camera feed appears in top-left section
- [ ] Live timestamp updates every second
- [ ] FPS counter shows (should be around 30)
- [ ] "Connected" badge is green

If camera doesn't work:
- [ ] Check browser console for errors
- [ ] Try accessing `/camera/stream.mjpg` directly
- [ ] Verify camera is enabled: `vcgencmd get_camera`

#### Valve Control Widget
- [ ] "Manual Valve Control" card visible on right side
- [ ] Current position shows percentage
- [ ] Progress bar displays
- [ ] "Open +5%" and "Close -5%" buttons present
- [ ] Status shows "Ready"

#### System Health Widget
- [ ] CPU Temperature displays (should be 40-70°C)
- [ ] CPU Usage displays (should be 0-100%)
- [ ] Memory displays in GB
- [ ] Camera badge shows "Active" (green)
- [ ] Stepper Motor badge shows status
- [ ] Network badge shows "Active"
- [ ] Uptime displays (e.g., "4d 12h 34m")

#### Bubble Rate Widget
- [ ] Current rate displays a number
- [ ] Chart displays with data
- [ ] Time range buttons (1h, 6h, 24h, 7d) present
- [ ] Chart updates over time

## API Tests

### Camera API
```bash
# Get camera status
curl http://localhost:8000/camera/status
```
- [ ] Returns JSON with camera info
- [ ] Shows "running": true or false

```bash
# Test snapshot
curl http://localhost:8000/camera/snapshot --output test.jpg
```
- [ ] Creates test.jpg file
- [ ] Image opens and shows camera view

### Stepper/Valve API
```bash
# Get stepper status
curl http://localhost:8000/api/stepper/status
```
- [ ] Returns JSON with motor status
- [ ] Shows enabled/disabled state
- [ ] Shows current position in steps

```bash
# Enable motor
curl -X POST http://localhost:8000/api/stepper/enable
```
- [ ] Returns success message
- [ ] Motor becomes enabled (check status endpoint)

```bash
# Test movement (SMALL MOVEMENT!)
curl -X POST "http://localhost:8000/api/stepper/step?steps=10&rpm=30"
```
- [ ] Motor moves (listen for stepping sound)
- [ ] Movement is smooth (not jerky)
- [ ] Correct direction
- [ ] No error message

⚠️ **SAFETY**: Use small step values (10-50) for testing!

```bash
# Emergency stop
curl -X POST http://localhost:8000/api/stepper/abort
```
- [ ] Motor stops immediately
- [ ] Status shows not moving

```bash
# Test valve endpoints
curl -X POST http://localhost:8000/api/valve/open
curl http://localhost:8000/api/valve/position
```
- [ ] Open command works
- [ ] Position increases by 5%
- [ ] Motor moves

```bash
# Disable motor
curl -X POST http://localhost:8000/api/stepper/disable
```
- [ ] Motor disables
- [ ] Motor is no longer holding position

### System Metrics API
```bash
# Get metrics
curl http://localhost:8000/api/system/metrics
```
- [ ] Returns JSON with metrics
- [ ] cpuTemp is reasonable (40-70°C)
- [ ] cpuUsage is 0-100
- [ ] memoryUsage and memoryTotal present
- [ ] uptime is formatted string

## Functional Tests

### Valve Control from Web Interface
1. Open dashboard in browser
2. Navigate to "Manual Valve Control" widget
3. [ ] Click "Open +5%" button
   - [ ] Status changes to "Moving..."
   - [ ] Motor makes stepping sound
   - [ ] Position increases by 5%
   - [ ] Progress bar updates
   - [ ] Status returns to "Ready"
4. [ ] Click "Close -5%" button
   - [ ] Status changes to "Moving..."
   - [ ] Motor steps in reverse
   - [ ] Position decreases by 5%
   - [ ] Status returns to "Ready"

### Live Monitoring
1. Keep dashboard open for 30 seconds
2. [ ] Camera feed continuously updates
3. [ ] System metrics refresh automatically
4. [ ] CPU usage changes reflect reality
5. [ ] Timestamp updates every second
6. [ ] No console errors

### Multiple Clients
1. Open dashboard in two different browsers/tabs
2. [ ] Both show camera feed
3. [ ] Click button in one tab
4. [ ] Other tab updates after refresh

## Performance Tests

### Camera Performance
- [ ] Camera stream is smooth (not choppy)
- [ ] No significant lag (< 1 second)
- [ ] FPS is stable (around configured value)
- [ ] CPU usage is reasonable (< 80%)

### Network Performance
- [ ] Dashboard loads quickly (< 3 seconds)
- [ ] API calls respond quickly (< 500ms)
- [ ] No timeout errors

## Troubleshooting Tests

### If camera doesn't work:
```bash
# Test camera directly
libcamera-hello

# Check camera status
vcgencmd get_camera

# Check application logs
journalctl -u plastination-dashboard -f
# or if running manually, check terminal output
```

### If motor doesn't move:
```bash
# Check GPIO permissions
groups | grep gpio

# Test enable pin
curl -X POST http://localhost:8000/api/stepper/enable
curl http://localhost:8000/api/stepper/status

# Try different direction
curl -X POST "http://localhost:8000/api/stepper/step?steps=50&direction=fwd"
curl -X POST "http://localhost:8000/api/stepper/step?steps=50&direction=rev"

# Check enable inversion
# Edit .env and change:
# STEPPER_INVERT_ENABLE=0
# Then restart app
```

### If getting permission errors:
```bash
# Add user to gpio group
sudo usermod -a -G gpio $USER

# Log out and log back in
# Or reboot
sudo reboot
```

## Production Readiness Tests

### Systemd Service
- [ ] Service file created
- [ ] Service enables without errors
- [ ] Service starts automatically
- [ ] Service restarts on failure
- [ ] Logs accessible via journalctl

### Security
- [ ] API only accessible from expected IPs
- [ ] Nginx reverse proxy configured
- [ ] HTTPS/TLS enabled
- [ ] Authentication implemented
- [ ] Rate limiting configured

### Stability
- [ ] Run for 24 hours without crashes
- [ ] Memory usage stable (not increasing)
- [ ] CPU usage reasonable
- [ ] No error accumulation in logs

## Success Criteria

Your installation is successful if:
- ✅ Dashboard loads and displays properly
- ✅ Camera feed shows live video
- ✅ Valve control buttons move the motor
- ✅ System metrics display and update
- ✅ No errors in browser console
- ✅ API endpoints respond correctly
- ✅ Motor moves smoothly in both directions

## Getting Help

If tests fail:
1. Check SETUP.md for detailed instructions
2. Review GPIO_SETUP.md for wiring help
3. Look at application logs for errors
4. Verify .env configuration matches your hardware
5. Open an issue on GitHub with:
   - Which test failed
   - Error messages
   - Your hardware configuration
   - Logs/output

---

**Test Date**: ___________
**Tested By**: ___________
**Result**: ☐ Pass  ☐ Fail  ☐ Partial
**Notes**: ___________________________________________
