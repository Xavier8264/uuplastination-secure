# GPIO Pin Configuration Quick Reference

## How to Change GPIO Pins

Edit the `.env` file in the project root:

```bash
nano .env
```

Change these values to match your wiring:

```bash
VALVE_PIN_STEP=23    # Change to your STEP pin
VALVE_PIN_DIR=24     # Change to your DIR pin
VALVE_PIN_ENABLE=18  # Change to your ENABLE pin (or -1 to disable)
```

Then restart the application.

## Raspberry Pi GPIO Pinout (BCM Numbering)

```
     3.3V  (1)  (2)  5V
    GPIO2  (3)  (4)  5V
    GPIO3  (5)  (6)  GND
    GPIO4  (7)  (8)  GPIO14 (UART TX)
      GND  (9) (10)  GPIO15 (UART RX)
   GPIO17 (11) (12)  GPIO18 (PWM)
   GPIO27 (13) (14)  GND
   GPIO22 (15) (16)  GPIO23 ← STEP (default)
     3.3V (17) (18)  GPIO24 ← DIR (default)
   GPIO10 (19) (20)  GND
    GPIO9 (21) (22)  GPIO25
   GPIO11 (23) (24)  GPIO8
      GND (25) (26)  GPIO7
    GPIO0 (27) (28)  GPIO1
    GPIO5 (29) (30)  GND
    GPIO6 (31) (32)  GPIO12
   GPIO13 (33) (34)  GND
   GPIO19 (35) (36)  GPIO16
   GPIO26 (37) (38)  GPIO20
      GND (39) (40)  GPIO21
```

## Recommended Pins for Stepper Control

### Option 1 (Default)
- **STEP**: GPIO 23 (Physical Pin 16)
- **DIR**: GPIO 24 (Physical Pin 18)
- **ENABLE**: GPIO 18 (Physical Pin 12)
- **GND**: Any GND pin

### Option 2 (Alternative)
- **STEP**: GPIO 17 (Physical Pin 11)
- **DIR**: GPIO 27 (Physical Pin 13)
- **ENABLE**: GPIO 22 (Physical Pin 15)
- **GND**: Any GND pin

### Option 3 (Compact Grouping)
- **STEP**: GPIO 5 (Physical Pin 29)
- **DIR**: GPIO 6 (Physical Pin 31)
- **ENABLE**: GPIO 13 (Physical Pin 33)
- **GND**: Pin 30 or 34

## Safe GPIO Pins to Use

✅ **Safe to use**: 4, 5, 6, 12, 13, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27

⚠️ **Use with caution** (special functions):
- GPIO 0, 1: Reserved for ID EEPROM
- GPIO 2, 3: I2C (if using I2C devices)
- GPIO 7, 8, 9, 10, 11: SPI (if using SPI devices)
- GPIO 14, 15: UART (if using serial console)

## Example .env Configurations

### Configuration for A4988 Driver (Active-Low Enable)
```bash
VALVE_PIN_STEP=23
VALVE_PIN_DIR=24
VALVE_PIN_ENABLE=18
STEPPER_INVERT_ENABLE=1
```

### Configuration for TMC2208 Driver (Active-High Enable)
```bash
VALVE_PIN_STEP=23
VALVE_PIN_DIR=24
VALVE_PIN_ENABLE=18
STEPPER_INVERT_ENABLE=0
```

### Configuration Without Enable Pin
```bash
VALVE_PIN_STEP=23
VALVE_PIN_DIR=24
VALVE_PIN_ENABLE=-1
STEPPER_INVERT_ENABLE=1
```

## Testing Your GPIO Configuration

After changing pins, test with:

```bash
# Enable the motor
curl -X POST http://localhost:8000/api/stepper/enable

# Move 10 steps forward
curl -X POST "http://localhost:8000/api/stepper/step?steps=10"

# Check status
curl http://localhost:8000/api/stepper/status

# Disable the motor
curl -X POST http://localhost:8000/api/stepper/disable
```

## Troubleshooting

### Motor doesn't move
1. Check power supply to driver
2. Verify GPIO pins are correct
3. Check if enable is active
4. Try inverting enable: `STEPPER_INVERT_ENABLE=0`

### Motor moves in wrong direction
Swap the DIR pin value or modify wiring:
- Option 1: Change DIR pin in `.env`
- Option 2: Swap motor coil wires

### Motor stutters or skips steps
1. Reduce RPM: `STEPPER_DEFAULT_RPM=30`
2. Check current limit on driver
3. Ensure adequate power supply

## Need Help?

Check the main SETUP.md file or open an issue on GitHub.
