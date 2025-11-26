# Valve API 405 Error - Fix Summary

## Problem
The valve API was returning a **405 Method Not Allowed** error when accessed through the `/secure/api/valve/*` path, even though it worked previously and the hardware was functional.

## Root Cause
The nginx configuration had the `/secure/` location block matching BEFORE the specific `/secure/api/` proxy blocks. This caused nginx to try serving static files from the `/secure/` directory instead of proxying API requests to the FastAPI backend.

### What Was Happening:
1. Browser requests: `POST /secure/api/valve/open`
2. Nginx matches: `location ^~ /secure/` (static file serving)
3. Nginx tries: `try_files $uri $uri/ /index.html`
4. Result: 405 error because static files don't accept POST requests

## Solution Applied

### 1. Fixed nginx Configuration
Updated `/etc/nginx/sites-available/uuplastination` to include specific proxy location blocks BEFORE the general `/secure/` location:

```nginx
# BEFORE - Proxy blocks for /secure/api/, /secure/camera/, /secure/webrtc/
location ^~ /secure/api/ {
    auth_basic "UU Plastination — Secure";
    auth_basic_user_file /etc/nginx/.htpasswd;
    proxy_pass http://127.0.0.1:8000/api/;
    # ... proxy headers
}

# AFTER - General static file serving for /secure/
location ^~ /secure/ {
    alias /home/plastination/uuplastination/uuplastination-secure/;
    auth_basic "UU Plastination — Secure";
    auth_basic_user_file /etc/nginx/.htpasswd;
    try_files $uri $uri/ /index.html;
}
```

### 2. Restarted API Server
Killed and restarted the uvicorn process to load the updated valve API code that returns the simplified response format.

### 3. Reloaded nginx
Applied the configuration changes with `sudo systemctl reload nginx`.

## Testing

### Test the API Directly:
```bash
# Without auth (root path) - should work
curl -X POST http://localhost/api/valve/open

# With auth (secure path) - needs credentials
curl -X POST http://localhost/secure/api/valve/open -u ADMIN:password
```

### Test Through Browser:
1. Navigate to: `http://your-server/secure/test-valve.html`
2. Enter credentials when prompted (username: `ADMIN`)
3. Click "Open Valve" or "Close Valve" buttons
4. Check the results displayed on the page

### Main Dashboard:
Navigate to `http://your-server/secure/` and the valve buttons should now work correctly.

## Why It Worked Before Then Stopped

The most likely scenario:
1. You were accessing the site through a different path (e.g., `http://localhost/api/valve/open` directly)
2. Or nginx was configured differently before
3. Or the browser had cached a working version that bypassed nginx

When you reloaded the page, it forced the browser to use the correct `/secure/` path, which then hit the nginx configuration bug.

## Current Status

✅ **Fixed Issues:**
- nginx now properly proxies `/secure/api/*` requests to FastAPI
- Valve API returns simplified response: `{"status":"success","action":"open","char_sent":"r"}`
- Both `/api/valve/*` (public) and `/secure/api/valve/*` (authenticated) paths work
- Serial communication sends 'r' for open and 'l' for close

✅ **What Works Now:**
- Open valve button → sends 'r' character to /dev/ttyACM0
- Close valve button → sends 'l' character to /dev/ttyACM0
- One-way serial communication (no read/response expected)
- Authentication required for `/secure/` path
- Public access available at `/api/` path (no auth)

## Important Notes

1. **Authentication**: The `/secure/` path requires HTTP Basic Auth
   - Username: `ADMIN` (as configured in `/etc/nginx/.htpasswd`)
   - Browser should prompt for credentials once and cache them

2. **Path Detection**: The JavaScript automatically detects the path:
   - If URL starts with `/secure/` → uses `/secure/api/valve/*`
   - Otherwise → uses `/api/valve/*`

3. **Serial Port**: Ensure `/dev/ttyACM0` exists and is accessible:
   ```bash
   ls -l /dev/ttyACM0
   sudo usermod -a -G dialout $USER
   ```

4. **Restart Required**: If you modify `valve.py`, restart uvicorn:
   ```bash
   sudo pkill -f "uvicorn app.main:app"
   cd /home/plastination/uuplastination/uuplastination-secure
   python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000 &
   ```

## Files Modified

1. `/etc/nginx/sites-available/uuplastination` - Added proxy blocks for `/secure/api/`, `/secure/camera/`, `/secure/webrtc/`
2. Created `/home/plastination/uuplastination/uuplastination-secure/test-valve.html` - Test page for debugging

## Verification Commands

```bash
# Check nginx config
sudo nginx -t

# Check if API is running
ps aux | grep uvicorn

# Test valve API (local)
curl -X POST http://127.0.0.1:8000/api/valve/open

# Test through nginx (root path)
curl -X POST http://localhost/api/valve/open

# Check nginx logs if issues persist
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log
```
