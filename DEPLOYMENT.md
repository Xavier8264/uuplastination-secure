# Deployment Checklist – UU Plastination Secure

Complete guide to deploy the camera streaming system with LiveKit WebRTC and RTMP publisher.

## Prerequisites

- [ ] Raspberry Pi 4/5 with Raspberry Pi OS (64-bit recommended)
- [ ] Pi Camera Module connected to CSI port
- [ ] Server/VM for LiveKit stack (can be the same Pi or separate server)
- [ ] Public domain with DNS control
- [ ] SSL/TLS certificates (Let's Encrypt recommended)

## Part 1: Server Setup (LiveKit + API)

### 1.1 Install Dependencies

```bash
# On Debian/Ubuntu server
sudo apt update
sudo apt install -y docker.io docker-compose nginx certbot python3-certbot-nginx git python3-venv

# Enable Docker
sudo systemctl enable --now docker
sudo usermod -aG docker $USER
```

### 1.2 Clone Repository

```bash
cd /var/www/secure
git clone https://github.com/Xavier8264/uuplastination-secure.git
cd uuplastination-secure
```

### 1.3 Configure Environment

```bash
cp .env.example .env
nano .env
```

**Required variables:**
```bash
# LiveKit (use subdomain for best results)
LIVEKIT_HOST=https://livekit.uuplastination.com
LIVEKIT_API_KEY=your_api_key_here
LIVEKIT_API_SECRET=your_secret_here

# ICE/TURN servers
LIVEKIT_ICE_SERVERS=turns:turn.uuplastination.com:5349?transport=tcp

# TURN configuration
TURN_REALM=uuplastination.com
TURN_STATIC_SECRET=$(openssl rand -hex 32)
TURN_EXTERNAL_IP=your.server.public.ip
TURN_CERT_DIR=/etc/letsencrypt/live/turn.uuplastination.com

# Camera defaults (override on Pi)
CAMERA_WIDTH=1280
CAMERA_HEIGHT=720
CAMERA_FPS=30
```

### 1.4 Setup SSL Certificates

```bash
# For LiveKit subdomain
sudo certbot certonly --nginx -d livekit.uuplastination.com

# For TURN subdomain
sudo certbot certonly --nginx -d turn.uuplastination.com

# For main site (if not already done)
sudo certbot certonly --nginx -d www.uuplastination.com
```

### 1.5 Start LiveKit Stack

```bash
cd webrtc
docker compose up -d
docker compose logs -f  # Verify no errors
```

**Verify LiveKit is running:**
```bash
curl http://localhost:7880
# Should return LiveKit server info
```

### 1.6 Install Python API

```bash
cd /var/www/secure/uuplastination-secure
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# On Raspberry Pi, also install picamera2:
# sudo apt install -y python3-picamera2
# pip install picamera2
```

### 1.7 Install API Systemd Service

```bash
sudo cp systemd/uuplastination-api.service.example /etc/systemd/system/uuplastination-api.service

# Edit paths if needed
sudo nano /etc/systemd/system/uuplastination-api.service
# Update WorkingDirectory and EnvironmentFile paths

sudo systemctl daemon-reload
sudo systemctl enable --now uuplastination-api.service
sudo systemctl status uuplastination-api.service
```

### 1.8 Configure Nginx

**Add includes to your secure server block:**

Edit your Nginx site configuration (e.g., `/etc/nginx/sites-available/uuplastination-secure`):

```nginx
server {
    listen 443 ssl http2;
    server_name www.uuplastination.com;
    
    ssl_certificate /etc/letsencrypt/live/www.uuplastination.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/www.uuplastination.com/privkey.pem;
    
    # Your existing location blocks...
    
    # Add these includes for the secure section:
    location /secure/ {
        # Your auth/access control here...
        
        # Include API proxies
        include /var/www/secure/uuplastination-secure/nginx/secure_api_location.conf;
        include /var/www/secure/uuplastination-secure/nginx/secure_webrtc_location.conf;
        include /var/www/secure/uuplastination-secure/nginx/secure_camera_location.conf;
        
        # Serve static files
        alias /var/www/secure/uuplastination-secure/;
        try_files $uri $uri/ /secure/index.html;
    }
}

# LiveKit signaling server (subdomain recommended)
server {
    listen 443 ssl http2;
    server_name livekit.uuplastination.com;
    
    ssl_certificate /etc/letsencrypt/live/livekit.uuplastination.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/livekit.uuplastination.com/privkey.pem;
    
    location / {
        proxy_pass http://127.0.0.1:7880/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
    }
}
```

**Test and reload:**
```bash
sudo nginx -t
sudo systemctl reload nginx
```

### 1.9 Open Firewall Ports

```bash
# For LiveKit/TURN
sudo ufw allow 443/tcp    # HTTPS + TURNS
sudo ufw allow 5349/tcp   # TURNS alternative port
sudo ufw allow 3478/udp   # TURN (optional, improves NAT traversal)
```

**Important:** If using Cloudflare, ensure TURN domain DNS is "DNS only" (not proxied), as Cloudflare doesn't proxy UDP.

## Part 2: Raspberry Pi Camera Publisher Setup

### 2.1 Install Prerequisites on Pi

```bash
# On the Raspberry Pi
sudo apt update
sudo apt install -y git python3-venv ffmpeg libcamera-apps

# Verify camera
libcamera-hello
# Should show camera preview for 5 seconds
```

### 2.2 Clone Repository on Pi

```bash
cd /home/pi
git clone https://github.com/Xavier8264/uuplastination-secure.git
cd uuplastination-secure
```

### 2.3 Configure Pi Environment

```bash
cp .env.example .env
nano .env
```

**Set camera and LiveKit variables:**
```bash
LIVEKIT_HOST=https://livekit.uuplastination.com
LIVEKIT_API_KEY=your_api_key_here
LIVEKIT_API_SECRET=your_secret_here

CAMERA_WIDTH=1280
CAMERA_HEIGHT=720
CAMERA_FPS=30
```

### 2.4 Install Python Dependencies on Pi

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Also install picamera2 system package
sudo apt install -y python3-picamera2
```

### 2.5 Create LiveKit Ingress

**Run once to create the RTMP ingress:**

```bash
source venv/bin/activate
python3 webrtc/init_ingress.py --room plastination --name pi-cam --out webrtc/ingress_key.txt

# Verify ingress_key.txt was created
cat webrtc/ingress_key.txt
```

**Expected output:**
```
RTMP_URL=rtmp://your-server/live
STREAM_KEY=some-long-key
ROOM=plastination
INGRESS_ID=IN_...
```

### 2.6 Test Publisher Manually (Optional)

```bash
# Create log directory
sudo mkdir -p /var/log/pi-camera
sudo chown pi:pi /var/log/pi-camera

# Run publisher script
bash webrtc/pi_rtmp_publisher.sh
```

Press Ctrl+C to stop after verifying it connects.

### 2.7 Install Publisher Systemd Service

```bash
sudo cp systemd/pi-camera-publisher.service.example /etc/systemd/system/pi-camera-publisher.service

# Edit if your paths differ
sudo nano /etc/systemd/system/pi-camera-publisher.service
# Update WorkingDirectory to /home/pi/uuplastination-secure
# Update EnvironmentFile to /home/pi/uuplastination-secure/.env

# Create log directory with proper permissions
sudo mkdir -p /var/log/pi-camera
sudo chown pi:pi /var/log/pi-camera

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable --now pi-camera-publisher.service
sudo systemctl status pi-camera-publisher.service
```

### 2.8 Verify Publisher Health

```bash
# Check logs
tail -f /var/log/pi-camera/publisher.log

# Check service status
sudo systemctl status pi-camera-publisher.service

# Verify camera status from API (from any machine)
curl https://www.uuplastination.com/secure/camera/status
```

## Part 3: Verify Complete System

### 3.1 Check LiveKit Room

Visit LiveKit dashboard or check via API:
```bash
# Should show participant "pi-cam" with video track
curl -s "http://localhost:7880/rooms" | jq .
```

### 3.2 Test Web Dashboard

1. Open browser: `https://www.uuplastination.com/secure/`
2. Check "Live Camera Feed" widget
3. Verify it shows "● WebRTC" status (not "Retrying…")
4. Video should appear with low latency (<1 second)

**If showing MJPEG instead:**
- Check browser console for errors
- Verify `/webrtc/config` returns correct LIVEKIT_HOST
- Verify `/webrtc/token` returns a valid JWT
- Check TURN connectivity (port 5349 reachable)

### 3.3 Test API Endpoints

```bash
BASE=https://www.uuplastination.com/secure

# Camera
curl "$BASE/camera/status"
curl "$BASE/camera/snapshot" -o test.jpg

# System metrics
curl "$BASE/api/stats"
curl "$BASE/api/system/metrics"

# Stepper (if hardware connected)
curl "$BASE/api/stepper/status"

# WebRTC
curl "$BASE/webrtc/config"
curl "$BASE/webrtc/token?room=plastination&role=viewer"
```

### 3.4 Monitor Health

**On the server:**
```bash
# API logs
sudo journalctl -u uuplastination-api.service -f

# LiveKit logs
cd /var/www/secure/uuplastination-secure/webrtc
docker compose logs -f
```

**On the Pi:**
```bash
# Publisher logs
tail -f /var/log/pi-camera/publisher.log

# Service status
sudo systemctl status pi-camera-publisher.service
```

## Troubleshooting

### Publisher keeps restarting

**Check ribbon cable:**
```bash
libcamera-hello
vcgencmd get_camera
```

**Check permissions:**
```bash
groups pi | grep video  # Should include 'video' group
```

### WebRTC connection fails, only MJPEG works

**Verify token generation:**
```bash
curl https://www.uuplastination.com/secure/webrtc/token?room=plastination
# Should return JSON with "token" field
```

**Check TURN connectivity from client machine:**
```bash
# Test TURNS port
openssl s_client -connect turn.uuplastination.com:5349
```

**Browser console errors:**
- "Failed to fetch token" → API not reachable or CORS issue
- "ICE failed" → TURN server not reachable or misconfigured
- "Track subscription timeout" → Publisher not connected to LiveKit

### MJPEG gives 503 error

**On non-Pi systems:**
- Expected if picamera2 not installed
- Use Pi for testing or mock data

**On Pi:**
```bash
# Verify camera detected
libcamera-hello

# Check API logs
sudo journalctl -u uuplastination-api.service -n 50
```

### High latency or buffering

**Reduce bitrate:**
Edit `webrtc/pi_rtmp_publisher.sh` and add `-b:v 1500k` to ffmpeg command.

**Check network:**
```bash
# Ping LiveKit server
ping livekit.uuplastination.com

# Check bandwidth
iperf3 -c your-server-ip
```

## Maintenance

### Update certificates (auto-renewed by certbot)
```bash
sudo certbot renew --dry-run
```

### Update code
```bash
cd /var/www/secure/uuplastination-secure
git pull
sudo systemctl restart uuplastination-api.service

# On Pi
cd /home/pi/uuplastination-secure
git pull
sudo systemctl restart pi-camera-publisher.service
```

### Restart services
```bash
# Server
sudo systemctl restart uuplastination-api.service
cd /var/www/secure/uuplastination-secure/webrtc
docker compose restart

# Pi
sudo systemctl restart pi-camera-publisher.service
```

## Security Checklist

- [ ] API bound to 127.0.0.1 only (not exposed directly)
- [ ] Nginx rate limiting enabled for `/api/stepper/*`
- [ ] Cloudflare Access or HTTP Basic Auth enabled for `/secure/`
- [ ] TURN uses static-auth-secret (not static credentials)
- [ ] SSL/TLS certificates valid and auto-renewing
- [ ] Firewall (ufw) configured to allow only necessary ports
- [ ] `.env` files have restricted permissions (600)

```bash
chmod 600 .env
```

---

**Deployment complete!** Your Pi camera should now continuously stream to your secure dashboard with WebRTC, falling back to MJPEG if needed.
