# WebRTC Live Camera via LiveKit

This repository adds a LiveKit + Ingress + coturn stack to deliver the Raspberry Pi camera to the web UI using WebRTC.

## Components

- LiveKit Server: signaling + SFU (WS at 7880; use HTTPS/WSS via reverse proxy)
- LiveKit Ingress: accepts RTMP/WHIP, publishes into a room
- coturn: TURN/TURNS for NAT traversal (recommended TURNS on 5349 or 443)

Frontend at `index.html` auto-attempts a WebRTC connection with retries; if unavailable, it falls back to MJPEG and keeps retrying.

## DNS and HTTPS (Production)

You must expose signaling and TURN on public hostnames:

- livekit.<your-domain> -> HTTPS/WSS to LiveKit (via Nginx or Cloudflare Tunnel). Prefer a dedicated subdomain over a path.
- turn.<your-domain> -> TURNS (5349/tcp or 443/tcp) directly reachable on the Internet (Cloudflare proxy OFF)

Important: Cloudflare Tunnel does not proxy UDP; prefer TURNS over TCP (5349) or expose 443 directly. If you cannot expose TURN publicly, WebRTC may fail under NAT.

## Configure

1. Copy .env.example to .env and set:
    - LIVEKIT_HOST=https://livekit.<your-domain>  # recommended subdomain
       # If you absolutely must use a path on your main site: https://www.<your-domain>/secure/livekit
   - LIVEKIT_API_KEY / LIVEKIT_API_SECRET
   - LIVEKIT_ICE_SERVERS=turns:turn.<your-domain>:5349?transport=tcp
   - TURN_REALM=<your-domain>
   - TURN_STATIC_SECRET=random long hex (32+ chars)
   - TURN_EXTERNAL_IP=your public IP (if behind NAT)
   - TURN_CERT_DIR path containing fullchain.pem and privkey.pem for turn.<your-domain>

2. Start the stack:

   - Option A (host networking; preferred on a dedicated host):
     - Ensure ports 7880/tcp (or proxied), 5349/tcp (TURNS), 3478/udp (TURN) are reachable.

3. Bring up services:

   docker compose -f webrtc/docker-compose.yml up -d

## Publishing from the Pi (RTMP Ingress)

We use LiveKit Ingress (RTMP) so the Pi can publish without running a full WebRTC client.

1. Create an RTMP Ingress and get stream key:

   Use Python (requires `livekit-api`):

   from livekit import api as lk

   client = lk.ApiClient(host=LIVEKIT_HOST, api_key=LIVEKIT_API_KEY, api_secret=LIVEKIT_API_SECRET)
   # Create RTMP ingress for room "plastination"
   req = lk.CreateIngressRequest(input_type=lk.IngressInput.RTMP_INPUT, name="pi-cam", room_name="plastination")
   resp = client.ingress.create_ingress(req)
   print(resp.rtmp.url, resp.stream_key)

2. Push RTMP from the Pi (example with libcamera + ffmpeg):

   libcamera-vid -t 0 --inline -n -o - \
     | ffmpeg -re -f h264 -i - -c:v copy -f flv rtmp://<livekit-hostname>/live/<STREAM_KEY>

   - If you don't have H.264 elementary stream, use:

     ffmpeg -f v4l2 -input_format mjpeg -i /dev/video0 -c:v libx264 -preset veryfast -tune zerolatency -f flv rtmp://<livekit-hostname>/live/<STREAM_KEY>

3. Open your dashboard page; the viewer auto-subscribes to the room and displays the first video track. It will keep retrying WebRTC if the producer isn't up yet.

### Optional: Auto-create ingress on boot
Use `webrtc/init_ingress.py` to create an ingress and write the stream key to a file. Combine with a systemd unit to start the publisher automatically.

## Systemd (Production)

Example service templates are provided in `systemd/`:
- `uuplastination-api.service.example` – runs FastAPI on 127.0.0.1:8000
- `livekit.service.example` – manages LiveKit stack via docker compose (livekit + ingress + coturn)

Adjust paths, copy to `/etc/systemd/system/`, then:

sudo systemctl daemon-reload
sudo systemctl enable uuplastination-api.service livekit.service
sudo systemctl start uuplastination-api.service livekit.service

## Troubleshooting

- If WebRTC fails and MJPEG shows, check browser console for errors.
- Ensure LIVEKIT_HOST is reachable over HTTPS and token endpoint (/webrtc/token) returns a token.
- Verify TURNS connectivity: port 5349/tcp reachable from clients; consider 443/tcp if 5349 blocked.
- For strict NATs, TURN UDP (3478) improves reliability.
