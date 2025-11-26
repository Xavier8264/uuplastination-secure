# Simple Valve API - One-Way Serial Communication

## Summary
The valve API has been simplified to do **exactly one thing**: send single characters through `/dev/ttyACM0`.

- **POST /api/valve/open** → sends `'r'` → returns `"OK"`
- **POST /api/valve/close** → sends `'l'` → returns `"OK"`

**No reading from serial port. No complex error handling. Just send and return OK.**

## What Changed

1. **Response simplified**: Instead of returning JSON like `{"status": "success", "action": "open"}`, endpoints now return plain `"OK"` string
2. **Exclusive serial access**: Added `exclusive=True` flag to prevent multiple connections
3. **One-way only**: Removed all code that tried to read responses from serial port
4. **Clean error handling**: If serial port is busy/unavailable, returns appropriate HTTP error (503 or 500)

## How It Works

```python
def _send_char(ch: str) -> None:
    """Send a single character through serial port."""
    ser = serial.Serial(
        "/dev/ttyACM0",
        115200,
        timeout=0,
        write_timeout=0.5,
        exclusive=True  # Only one connection at a time
    )
    ser.write(ch.encode("utf-8"))
    ser.flush()
    ser.close()
```

## Testing

### Direct Serial Test (No HTTP)
```bash
python3 -c "
from app.routers.valve import _send_char
_send_char('r')  # Open valve
_send_char('l')  # Close valve
"
```

### HTTP API Test
```bash
# Using the test script
./test_valve_simple.sh

# Or manually
curl -X POST http://localhost/secure/api/valve/open
# Response: "OK"

curl -X POST http://localhost/secure/api/valve/close
# Response: "OK"
```

## Response Codes

- **200 OK**: Character sent successfully → Response body: `"OK"`
- **500 Internal Server Error**: Serial communication failed
- **503 Service Unavailable**: Serial port is busy or locked by another process

## No More 405 Errors

The 405 error was happening because the Arduino/serial device was trying to send responses back, but we weren't reading them, causing the serial buffer to fill up and lock.

**Solution**: We don't care about responses. We just send the character and close the connection immediately.

## Client-Side JavaScript

The frontend (`index.html`) already handles this correctly:

```javascript
async function sendValve(url, label){
  stateEl.textContent = label + '…';
  openBtn.disabled = true; 
  closeBtn.disabled = true;
  
  try {
    const res = await fetch(url, { 
      method:'POST', 
      credentials:'include' 
    });
    
    if(res.ok){
      valveApiStatus.textContent = 'OK';  // ✓ Shows "OK"
    } else {
      valveApiStatus.textContent = 'Error ' + res.status;
    }
  } catch(e){
    valveApiStatus.textContent = 'Network error';
  }
  
  stateEl.textContent = 'Ready';
  openBtn.disabled = false; 
  closeBtn.disabled = false;
}
```

## Troubleshooting

### Port Busy Error
If you get "Serial port busy" error:

```bash
# Check what's using the port
lsof /dev/ttyACM0

# Kill the process if needed
sudo fuser -k /dev/ttyACM0

# Or restart the API
sudo systemctl restart uuplastination-api
```

### Permission Denied
```bash
# Add user to dialout group
sudo usermod -a -G dialout $USER

# Reboot or re-login for changes to take effect
```

## That's It!

Simple. Clean. One-way communication. Just send `r` or `l` and return `OK`.
