from __future__ import annotations

import json
import os
import platform
import socket
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import psutil
from fastapi import APIRouter


# Configurable service names and ports (override via environment variables)
SERVICE_CAMERA = os.getenv("SERVICE_CAMERA", "camera-stream.service")
SERVICE_STEPPER = os.getenv("SERVICE_STEPPER", "valve-control.service")
PORT_RTSP = int(os.getenv("PORT_RTSP", "8554"))
PORT_API = int(os.getenv("PORT_API", "8000"))


router = APIRouter(prefix="/api", tags=["stats"])


def _read_cpu_temp_c() -> Optional[float]:
    """Best-effort CPU temperature in Celsius.

    Preference order:
    1) vcgencmd measure_temp (from libraspberrypi-bin)
    2) /sys/class/thermal/thermal_zone*/temp
    3) psutil.sensors_temperatures
    Returns None if unavailable.
    """
    # 1) vcgencmd
    try:
        proc = subprocess.run(
            ["vcgencmd", "measure_temp"],
            capture_output=True,
            text=True,
            timeout=0.4,
            check=False,
        )
        out = (proc.stdout or "").strip()
        if out:
            # Format: temp=49.2'C
            if out.startswith("temp=") and "'C" in out:
                val = out.split("=", 1)[1].split("'C", 1)[0]
                return float(val)
    except Exception:
        pass

    # 2) thermal zones
    try:
        base = Path("/sys/class/thermal")
        zones = sorted(base.glob("thermal_zone*/temp"))
        for z in zones:
            try:
                raw = z.read_text().strip()
                if raw:
                    v = float(raw)
                    # Some report millidegrees
                    if v > 1000:
                        v = v / 1000.0
                    # Basic sanity
                    if 0.0 < v < 120.0:
                        return v
            except Exception:
                continue
    except Exception:
        pass

    # 3) psutil (may be empty on many Linux distros)
    try:
        temps = psutil.sensors_temperatures(fahrenheit=False)
        if temps:
            for _, entries in temps.items():
                for e in entries:
                    if e.current is not None and 0.0 < e.current < 120.0:
                        return float(e.current)
    except Exception:
        pass

    return None


def _cpu_usage_percent() -> Optional[float]:
    try:
        # fast sample; psutil will use last interval
        return float(psutil.cpu_percent(interval=0.05))
    except Exception:
        return None


def _memory_stats() -> Dict[str, Optional[float]]:
    try:
        vm = psutil.virtual_memory()
        return {
            "total": float(vm.total),
            "used": float(vm.used),
            "available": float(vm.available),
            "percent": float(vm.percent),
        }
    except Exception:
        return {"total": None, "used": None, "available": None, "percent": None}


def _uptime_seconds() -> Optional[float]:
    try:
        return float(time.time() - psutil.boot_time())
    except Exception:
        return None


def _ipv4_addresses() -> List[str]:
    addrs: List[str] = []
    try:
        for iface, info in psutil.net_if_addrs().items():
            for snic in info:
                if getattr(snic, "family", None) == socket.AF_INET:
                    ip = snic.address
                    if ip and ip != "127.0.0.1":
                        addrs.append(ip)
    except Exception:
        pass
    return sorted(set(addrs))


def _internet_reachable(timeout: float = 0.3) -> Optional[bool]:
    # UDP socket connect trick: no traffic sent, but routing/AR table checked
    targets = [("1.1.1.1", 53), ("8.8.8.8", 53)]
    for host, port in targets:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(timeout)
            s.connect((host, port))
            s.close()
            return True
        except Exception:
            continue
    return False


def _systemd_state(unit: str) -> str:
    try:
        proc = subprocess.run(
            ["systemctl", "is-active", unit],
            capture_output=True,
            text=True,
            timeout=0.5,
            check=False,
        )
        out = (proc.stdout or "").strip()
        return out if out else "unknown"
    except Exception:
        return "unknown"


def _port_open(port: int, host: str = "127.0.0.1", timeout: float = 0.25) -> Optional[bool]:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False


def _os_info() -> Dict[str, Optional[str]]:
    pretty: Optional[str] = None
    try:
        # Prefer /etc/os-release
        p = Path("/etc/os-release")
        if p.exists():
            data: Dict[str, str] = {}
            for line in p.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    data[k] = v.strip().strip('"')
            pretty = data.get("PRETTY_NAME")
    except Exception:
        pass
    try:
        kernel = platform.release()
    except Exception:
        kernel = None
    try:
        arch = platform.machine()
    except Exception:
        arch = None
    return {"pretty_name": pretty, "kernel": kernel, "arch": arch}


@router.get("/stats")
def get_stats() -> Dict[str, Any]:
    # Build payload with graceful fallbacks and short timeouts
    cpu_temp = _read_cpu_temp_c()
    cpu_usage = _cpu_usage_percent()
    mem = _memory_stats()
    uptime = _uptime_seconds()
    ipv4 = _ipv4_addresses()
    internet = _internet_reachable()

    services = {
        "camera": _systemd_state(SERVICE_CAMERA),
        "stepper": _systemd_state(SERVICE_STEPPER),
        "nginx": _systemd_state("nginx"),
        "tailscaled": _systemd_state("tailscaled"),
        "webhook_deploy": _systemd_state("webhook-deploy.service"),
    }

    ports = {
        "rtsp_8554": _port_open(PORT_RTSP),
        "api_8000": _port_open(PORT_API),
    }

    osi = _os_info()

    try:
        ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    except Exception:
        ts = None

    return {
        "cpu": {"temp_c": cpu_temp, "usage_percent": cpu_usage},
        "memory": mem,
        "uptime_seconds": uptime,
        "network": {"ipv4_addresses": ipv4, "internet_reachable": internet},
        "services": services,
        "ports": ports,
        "os": osi,
        "timestamp": ts,
    }
