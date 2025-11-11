#!/usr/bin/env python3
"""Create or reuse a LiveKit RTMP ingress and write stream key to file.
Run this at boot (systemd ExecStartPre) so your Pi publisher service can read the key.

Usage:
  LIVEKIT_HOST=https://livekit.example.com \
  LIVEKIT_API_KEY=xxx LIVEKIT_API_SECRET=yyy \
  python3 webrtc/init_ingress.py --room plastination --name pi-cam --out webrtc/ingress_key.txt
"""
from __future__ import annotations
import argparse
import os
import sys
from pathlib import Path

try:
    from livekit import api as lk  # type: ignore
except Exception as e:
    print(f"livekit-api not installed: {e}", file=sys.stderr)
    sys.exit(1)

HOST = os.getenv("LIVEKIT_HOST", "")
KEY = os.getenv("LIVEKIT_API_KEY", "")
SECRET = os.getenv("LIVEKIT_API_SECRET", "")

parser = argparse.ArgumentParser()
parser.add_argument("--room", default="plastination")
parser.add_argument("--name", default="pi-cam")
parser.add_argument("--out", default="webrtc/ingress_key.txt")
args = parser.parse_args()

if not HOST or not KEY or not SECRET:
    print("Missing LIVEKIT_HOST / LIVEKIT_API_KEY / LIVEKIT_API_SECRET", file=sys.stderr)
    sys.exit(2)

client = lk.ApiClient(host=HOST, api_key=KEY, api_secret=SECRET)

# Simple approach: always create a new ingress (could be optimized to reuse)
req = lk.CreateIngressRequest(
    input_type=lk.IngressInput.RTMP_INPUT,
    name=args.name,
    room_name=args.room,
)
try:
    resp = client.ingress.create_ingress(req)
except Exception as e:
    print(f"Failed to create ingress: {e}", file=sys.stderr)
    sys.exit(3)

out_path = Path(args.out)
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(f"RTMP_URL={resp.rtmp.url}\nSTREAM_KEY={resp.stream_key}\nROOM={args.room}\nINGRESS_ID={resp.ingress_id}\n")
print(f"Ingress created. Stream key written to {out_path}")
