# UU Plastination - Quick Start (Post-Fix)

## ✅ System Status: OPERATIONAL

All critical issues have been resolved. Your live webcam setup is now functional.

## What Was Fixed

1. **LiveKit Container** - Fixed configuration format, now running stable
2. **Environment Variables** - Added python-dotenv, all configs loading correctly  
3. **API Server** - Running on port 8000 with all endpoints functional
4. **Security** - Generated secure TURN secret, using public STUN servers
5. **Camera Support** - Hardware detected, OpenCV fallback available

See `WEBCAM_FIXES.md` for complete technical details.

## Quick Start

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

## System Overview

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

## Current Configuration

### ✅ Working Features
- LiveKit server (signaling)
- Token generation for WebRTC clients
- API endpoints (camera, stats, stepper, webrtc)
- Dashboard UI with WebRTC fallback
- MJPEG camera streaming (fallback mode)
- System health monitoring

### ⚠️ Needs Setup
- **Camera Streaming**: Install picamera2 or enable OpenCV
- **RTMP Ingress**: Run `python3 webrtc/init_ingress.py` to create ingress
- **TURN Server**: Enable coturn after obtaining TLS certificates
- **Production DNS**: Point domains to this server
- **HTTPS**: Configure nginx with SSL certificates

## Next Steps

### For Local Testing (Current Setup)
1. ✅ Services are running
2. ✅ API is accessible
3. Open dashboard: http://127.0.0.1:8000/
4. Camera will show MJPEG stream (if camera started)

### For Production Deployment

1. **Get TLS Certificates**
   ```bash
   sudo certbot certonly --standalone \
     -d livekit.uuplastination.com \
     -d turn.uuplastination.com
   ```

2. **Enable TURN Server**
   - Uncomment coturn in `webrtc/docker-compose.yml`
   - Update `.env` with cert paths
   - Restart: `./stop_services.sh && ./start_services.sh`

3. **Setup Camera Publishing**
   ```bash
   # Create RTMP ingress
   python3 webrtc/init_ingress.py
   
   # Start camera publisher (example)
   source venv/bin/activate
   python3 -m app.services.publisher
   ```

4. **Configure Nginx** (see `nginx/` directory for config snippets)

5. **Enable Systemd** (see `systemd/` for service examples)

## Troubleshooting

### Services won't start
```bash
# Check what's running
./check_status.sh

# View logs
docker logs livekit
tail -f /tmp/uuplastination-api.log
```

### Camera not working
```bash
# Check devices
ls -la /dev/video*

# Test camera
curl http://127.0.0.1:8000/camera/status

# Install picamera2 (Raspberry Pi)
source venv/bin/activate
pip install picamera2
```

### WebRTC connection fails
- Expected if no camera is publishing
- Dashboard will automatically fall back to MJPEG
- Check browser console for detailed errors
- Verify token generation: `curl http://127.0.0.1:8000/webrtc/token`

## File Reference

### New Scripts
- `start_services.sh` - Start all services
- `stop_services.sh` - Stop all services  
- `check_status.sh` - System health check
- `WEBCAM_FIXES.md` - Detailed fix documentation

### Modified Files
- `.env` - Updated with secure secrets and missing variables
- `webrtc/docker-compose.yml` - Fixed LiveKit configuration
- `app/main.py` - Added dotenv support
- `app/routers/webrtc.py` - Added dotenv support
- `requirements.txt` - Added python-dotenv

### Key Directories
- `webrtc/` - LiveKit and RTMP ingress configuration
- `app/` - FastAPI application
- `nginx/` - Reverse proxy configuration snippets
- `systemd/` - Service file examples

## Support

### View System Status
```bash
./check_status.sh
```

### View Logs
```bash
# API
tail -f /tmp/uuplastination-api.log

# LiveKit
docker logs -f livekit

# Ingress
docker logs -f livekit-ingress
```

### Test Endpoints
```bash
# Health check
curl http://127.0.0.1:8000/webrtc/health | python3 -m json.tool

# Token generation
curl "http://127.0.0.1:8000/webrtc/token?room=plastination"

# Camera status
curl http://127.0.0.1:8000/camera/status
```

## Environment Variables

Key variables in `.env`:
```bash
# Camera
CAMERA_NUM=0
CAMERA_WIDTH=1920
CAMERA_HEIGHT=1080
CAMERA_FPS=30

# LiveKit
LIVEKIT_HOST=https://livekit.uuplastination.com
LIVEKIT_API_KEY=devkey
LIVEKIT_API_SECRET=devsecret
LIVEKIT_ICE_SERVERS=stun:stun.l.google.com:19302

# TURN (for production)
TURN_REALM=uuplastination.com
TURN_STATIC_SECRET=bc3029211f1b5785f00a0aa9c3901201be333c6aa952ce31392bdd58a93ba041
```

## Security Notes

🔒 Current setup uses development credentials:
- API Key: `devkey` 
- API Secret: `devsecret`

**For production:**
1. Generate new credentials
2. Update both `.env` and `webrtc/docker-compose.yml`
3. Enable HTTPS
4. Configure authentication
5. Restrict firewall rules

---

**Status**: ✅ Development Ready | ⚠️ Production Requires Additional Setup

For complete technical documentation, see `WEBCAM_FIXES.md`
