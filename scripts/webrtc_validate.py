#!/usr/bin/env python3
import os
import sys
import socket
from urllib.parse import urlparse

import json

import requests

BASE = os.environ.get("VALIDATE_BASE", "http://127.0.0.1:8000")

# Allow environment injection for expected host for context in PASS/FAIL display
EXPECTED_LIVEKIT_HOST = os.environ.get("EXPECTED_LIVEKIT_HOST", "")


def get(path: str):
    try:
        r = requests.get(BASE + path, timeout=5)
        return r.status_code, r.json()
    except Exception as e:
        return 0, {"error": str(e)}


def tcp_check(url: str):
    try:
        u = urlparse(url)
        host = u.hostname
        port = u.port or (443 if u.scheme == "https" else 80)
        with socket.create_connection((host, port), timeout=3):
            return True, None
    except Exception as e:
        return False, str(e)


def main():
    print(f"Validate base: {BASE}")
    sc, cfg = get("/webrtc/config")
    print(f"CONFIG {sc} => {json.dumps(cfg, indent=2)}")

    sc, h = get("/webrtc/health")
    print(f"HEALTH {sc} => {json.dumps(h, indent=2)}")

    sc, d = get("/webrtc/diagnostics")
    print(f"DIAGNOSTICS {sc} => {json.dumps(d, indent=2)}")

    # Simple PASS/FAIL summary
    failures = []

    # Host
    host = cfg.get("host")
    if not host:
        failures.append("No host in /webrtc/config")
    else:
        if host.startswith("http"):
            ok, err = tcp_check(host)
            if not ok:
                failures.append(f"Signaling host not reachable via TCP: {err}")
        else:
            # relative path requires reverse proxy; we cannot test without full server context
            pass

    # Expected host mismatch (informational)
    if EXPECTED_LIVEKIT_HOST and host and host != EXPECTED_LIVEKIT_HOST:
        print(f"INFO: host reported '{host}' differs from EXPECTED_LIVEKIT_HOST '{EXPECTED_LIVEKIT_HOST}'")

    # API creds
    if not h.get("api_credentials_configured"):
        failures.append("LIVEKIT_API_KEY/SECRET not configured")

    # ICE servers
    if not h.get("ice_servers_count"):
        failures.append("No ICE servers configured (LIVEKIT_ICE_SERVERS)")

    # Disabled flag
    if h.get("disabled"):
        failures.append("WEBRTC_DISABLE is active")

    print("\nChecks:")
    for f in failures:
        print(" FAIL:", f)
    if not failures:
        print(" PASS: All critical WebRTC readiness checks passed")

    exit_code = 0 if not failures else 2
    print(f"\nExit code: {exit_code}")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
