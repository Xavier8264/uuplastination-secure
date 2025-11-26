# API Analysis & Cleanup Report

## Frontend API Usage (from index.html)

The frontend (`index.html`) actually calls these API endpoints:

### ✅ **Active Endpoints Used by Frontend:**

1. **Valve API** (`/api/valve/*`)
   - `POST /api/valve/open` - Sends 'r' character
   - `POST /api/valve/close` - Sends 'l' character
   - Used by: Open/Close buttons in Manual Valve Control section

2. **Stats API** (`/api/system/metrics`)
   - `GET /api/system/metrics` - Returns CPU temp, usage, memory, uptime
   - Used by: System Health panel (CPU, Memory, Uptime display)

3. **Stepper API** (`/api/stepper/status`)
   - `GET /api/stepper/status` - Returns stepper motor status (enabled, moving, position)
   - Used by: Stepper status badge display

4. **Camera API** (`/camera/*`)
   - `GET /camera/status` - Returns camera status
   - Used by: Camera feed section

5. **WebRTC API** (`/webrtc/*`)
   - `GET /webrtc/config` - Returns LiveKit configuration
   - `GET /webrtc/token` - Returns access token for WebRTC connection
   - Used by: Video streaming (LiveKit WebRTC player)

---

## Files Removed

### 🗑️ **Deleted Files:**

1. **`app/routers/valve_old.py`**
   - **Reason**: Obsolete implementation, replaced by simplified `valve.py`
   - **Impact**: None - was not imported in `main.py`

2. **`assets/js/dashboard.js`**
   - **Reason**: Not loaded/used by `index.html`
   - **Impact**: None - all functionality is embedded in `index.html` inline scripts

---

## Current Router Status

### 📁 **Active Routers** (all used by frontend):

| Router File | Prefix | Endpoints Used | Status |
|------------|--------|----------------|--------|
| `valve.py` | `/api/valve` | `/open`, `/close` | ✅ Active |
| `stats.py` | `/api` | `/system/metrics` | ✅ Active |
| `stepper.py` | `/api/stepper` | `/status` | ✅ Active |
| `camera.py` | `/camera` | `/status`, `/stream.mjpg`, `/snapshot` | ✅ Active |
| `webrtc.py` | `/webrtc` | `/config`, `/token` | ✅ Active |

### 📊 **Endpoint Usage Summary:**

**Valve API:**
- Simple one-way serial communication
- Only uses `/open` and `/close` endpoints
- Other endpoints (`/health`, `/position`, `/raw`) exist but are unused by frontend

**Stats API:**
- Provides system metrics
- Uses `/system/metrics` endpoint
- Also has `/stats` endpoint (more detailed, not used by current frontend)

**Stepper API:**
- Full stepper motor control available
- Frontend only polls `/status` for display
- Control endpoints exist but buttons not in current UI

**Camera API:**
- Provides camera streaming capabilities
- Frontend checks `/status`
- Stream endpoints available for future use

**WebRTC API:**
- LiveKit integration for video streaming
- Frontend uses `/config` and `/token`
- Additional endpoints for ingress and diagnostics exist

---

## Recommendations

### ⚠️ **Unused Endpoints (exist but not called by frontend):**

1. **Valve API:**
   - `GET /api/valve/health` - Could be useful for health checks
   - Consider keeping for monitoring purposes

2. **Stats API:**
   - `GET /api/stats` - More detailed system info
   - Could be useful for admin/debug page

3. **Stepper API:**
   - Control endpoints (`/enable`, `/disable`, `/step`, `/abort`, `/open`, `/close`)
   - Exist but no UI controls in current frontend
   - Keep for future implementation or API access

4. **Camera API:**
   - `GET /camera/stream.mjpg` - MJPEG stream endpoint
   - `GET /camera/snapshot` - Single frame capture
   - `POST /camera/start`, `/camera/stop`
   - Available for future use

5. **WebRTC API:**
   - `POST /webrtc/ingress/create`
   - `GET /webrtc/health`
   - `GET /webrtc/diagnostics`
   - Useful for setup and debugging

### ✅ **All routers should be kept:**
- Each router has at least one endpoint actively used by the frontend
- Additional endpoints provide useful functionality for future features or API consumers
- No completely unused routers detected

---

## Clean Code Summary

**What was removed:**
- ❌ `valve_old.py` - duplicate/obsolete valve implementation
- ❌ `assets/js/dashboard.js` - unused JavaScript file

**What remains:**
- ✅ All 5 router files are necessary and actively used
- ✅ `main.py` imports and mounts all required routers
- ✅ Frontend has minimal inline JavaScript with clear API calls
- ✅ Valve API is now simplified to only essential functionality

**Result:**
- Clean, minimal codebase
- No dead code or duplicate files
- All API routes properly organized and documented
- Frontend uses clear, simple API calls
