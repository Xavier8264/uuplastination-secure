# Valve API - Simplified Implementation

## Overview
The valve API has been simplified to provide a clean, one-way serial communication interface that sends single characters ('r' and 'l') through `/dev/ttyACM0` based on button presses from the frontend.

## Changes Made

### 1. Simplified `/app/routers/valve.py`
Removed all unnecessary features and kept only the core functionality:

**Removed:**
- Environment variable configuration for device path
- Virtual position tracking (`_valve_position`, `STEP_PERCENT`, etc.)
- Position reporting endpoint (`/position`)
- Raw character endpoint (`/raw`)
- Exclusive lock mode (was causing potential "device busy" errors)
- Unnecessary sleep delays
- Complex error handling logic

**Kept:**
- Simple character sending function (`_send_char`)
- `/api/valve/open` - sends 'r' character
- `/api/valve/close` - sends 'l' character  
- `/api/valve/health` - checks serial port availability
- Basic error handling for serial communication

### 2. API Endpoints

#### `POST /api/valve/open`
- Sends 'r' character through serial port
- Returns: `{"status": "success", "action": "open", "char_sent": "r"}`

#### `POST /api/valve/close`
- Sends 'l' character through serial port
- Returns: `{"status": "success", "action": "close", "char_sent": "l"}`

#### `GET /api/valve/health`
- Checks if `/dev/ttyACM0` is accessible
- Returns device path and baud rate if successful
- Returns error if serial port is unavailable

### 3. Configuration
**Hardcoded:**
- Device: `/dev/ttyACM0`
- Baud rate: 115200 (can be overridden with `VALVE_SERIAL_BAUD` env var)
- Characters: 'r' for open, 'l' for close

### 4. Frontend Integration
The existing frontend buttons already work correctly:
- "Open" button → calls `/api/valve/open` → sends 'r'
- "Close" button → calls `/api/valve/close` → sends 'l'

No frontend changes needed.

## How It Works

1. **User clicks "Open" button** in the web interface
2. Frontend sends `POST` request to `/api/valve/open`
3. API opens serial connection to `/dev/ttyACM0`
4. Sends 'r' character through serial port
5. Flushes and closes connection
6. Returns success response to frontend

The same process happens for "Close" with 'l' character.

## Error Handling

The API handles common errors:
- **Serial port not found**: Returns 503 status
- **Serial port busy**: Returns 503 status
- **Permission denied**: Returns 503 status
- **pyserial not installed**: Returns 500 status

## Testing

Use the included test script:
```bash
python test_valve_api.py
```

Or test manually with curl:
```bash
# Health check
curl http://localhost:8000/api/valve/health

# Send 'r' (open)
curl -X POST http://localhost:8000/api/valve/open

# Send 'l' (close)
curl -X POST http://localhost:8000/api/valve/close
```

## Serial Port Setup

Ensure the serial port is accessible:
```bash
# Check if device exists
ls -l /dev/ttyACM0

# Add user to dialout group (if permission denied)
sudo usermod -a -G dialout $USER

# Verify permissions
groups $USER
```

## Dependencies

Required Python package:
```bash
pip install pyserial
```

## Notes

- **One-way communication only**: The API does NOT read from the serial port
- **No state tracking**: The API doesn't track valve position or state
- **Simple and reliable**: Each request opens, writes one character, and closes the port
- **No authentication**: Add authentication if needed for production use
