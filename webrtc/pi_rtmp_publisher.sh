#!/usr/bin/env bash
# RTMP publisher for Raspberry Pi camera using libcamera-vid + ffmpeg
# Reads RTMP URL/KEY from webrtc/ingress_key.txt or env variables.
# Auto-restarts on failure with exponential backoff.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/.."
KEY_FILE="$ROOT_DIR/webrtc/ingress_key.txt"
LOG_DIR="${LOG_DIR:-/var/log/pi-camera}"; mkdir -p "$LOG_DIR" || true
LOG_FILE="$LOG_DIR/publisher.log"

# Camera settings (override via env)
CAMERA_WIDTH=${CAMERA_WIDTH:-1280}
CAMERA_HEIGHT=${CAMERA_HEIGHT:-720}
CAMERA_FPS=${CAMERA_FPS:-30}

# Read from file if present
if [[ -f "$KEY_FILE" ]]; then
  # shellcheck disable=SC1090
  source "$KEY_FILE"
fi

# Or from env
RTMP_URL=${RTMP_URL:-}
STREAM_KEY=${STREAM_KEY:-}

if [[ -z "${RTMP_URL:-}" || -z "${STREAM_KEY:-}" ]]; then
  echo "Missing RTMP_URL or STREAM_KEY. Create ingress via webrtc/init_ingress.py first." | tee -a "$LOG_FILE"
  exit 2
fi

TARGET="${RTMP_URL%/}/${STREAM_KEY}"

# Check tools
command -v ffmpeg >/dev/null 2>&1 || { echo "ffmpeg not found" | tee -a "$LOG_FILE"; exit 3; }
if ! command -v libcamera-vid >/dev/null 2>&1; then
  echo "libcamera-vid not found; will try ffmpeg v4l2 fallback" | tee -a "$LOG_FILE"
fi

# Run loop
BACKOFF=2
MAX_BACKOFF=30

echo "Starting Pi RTMP publisher -> $TARGET" | tee -a "$LOG_FILE"

while true; do
  START_TS=$(date -Is)
  echo "[$START_TS] Launching pipeline..." | tee -a "$LOG_FILE"
  if command -v libcamera-vid >/dev/null 2>&1; then
    # libcamera produces H.264 Annex B. We wrap to FLV via ffmpeg.
    # --inline ensures SPS/PPS are sent regularly for live streaming.
    set +e
    libcamera-vid \
      -t 0 \
      --width "$CAMERA_WIDTH" --height "$CAMERA_HEIGHT" \
      --framerate "$CAMERA_FPS" \
      --inline \
      --codec h264 \
      -o - \
      2>>"$LOG_FILE" \
      | ffmpeg -loglevel warning -re -f h264 -i - -c:v copy -f flv "$TARGET" 2>>"$LOG_FILE"
    RC=$?
    set -e
  else
    # Fallback: capture via v4l2 (USB UVC cams)
    set +e
    ffmpeg -loglevel warning -f v4l2 -input_format mjpeg \
      -video_size ${CAMERA_WIDTH}x${CAMERA_HEIGHT} -framerate "$CAMERA_FPS" \
      -i /dev/video0 \
      -c:v libx264 -preset veryfast -tune zerolatency -b:v 2500k \
      -pix_fmt yuv420p -g 60 -f flv "$TARGET" 2>>"$LOG_FILE"
    RC=$?
    set -e
  fi
  echo "Pipeline exited rc=$RC" | tee -a "$LOG_FILE"
  sleep "$BACKOFF"
  BACKOFF=$(( BACKOFF < MAX_BACKOFF ? BACKOFF * 2 : MAX_BACKOFF ))

echo "Restarting with backoff ${BACKOFF}s" | tee -a "$LOG_FILE"

done
