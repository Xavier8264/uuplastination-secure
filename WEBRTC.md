# WebRTC Live Camera via LiveKit

This repository adds a LiveKit + Ingress + coturn stack to deliver the Raspberry Pi camera to the web UI using WebRTC.

## Components

- LiveKit Server: signaling + SFU (WS at 7880; use HTTPS/WSS via reverse proxy)
- LiveKit Ingress: accepts RTMP/WHIP, publishes into a room
- coturn: TURN/TURNS for NAT traversal (recommended TURNS on 5349 or 443)

Frontend at `index.html` auto-attempts a WebRTC connection; if unavailable, it falls back to MJPEG.

## DNS and HTTPS

You must expose signaling and TURN on public hostnames:

- livekit.<your-domain> -> HTTPS/WSS to LiveKit (via proxy or Cloudflare Tunnel)
- turn.<your-domain> -> TURNS (5349/tcp or 443/tcp) directly reachable on the Internet

Important: Cloudflare Tunnel does not proxy UDP; prefer TURNS over TCP (5349) or expose 443 directly. If you cannot expose TURN publicly, WebRTC may fail under NAT.

## Configure

1. Copy .env.example to .env and set:
   - LIVEKIT_HOST=https://livekit.<your-domain>
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

## Publishing from the Pi

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

3. Open your dashboard page; the viewer auto-subscribes to the room and displays the first video track.

## Troubleshooting

- If WebRTC fails and MJPEG shows, check browser console for errors.
- Ensure LIVEKIT_HOST is reachable over HTTPS and token endpoint (/webrtc/token) returns a token.
- Verify TURNS connectivity: port 5349/tcp reachable from clients; consider 443/tcp if 5349 blocked.
- For strict NATs, TURN UDP (3478) improves reliability.
