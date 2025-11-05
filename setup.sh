#!/bin/bash
# UU Plastination Quick Setup Script
# Run this on your Raspberry Pi to set up the environment

set -e

echo "======================================"
echo "UU Plastination Control System Setup"
echo "======================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running on Raspberry Pi
if [ ! -f /proc/device-tree/model ]; then
    echo -e "${YELLOW}Warning: Not running on Raspberry Pi${NC}"
    echo "This script is designed for Raspberry Pi. Continue anyway? (y/n)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "Step 1: Checking Python..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 not found. Installing...${NC}"
    sudo apt update
    sudo apt install -y python3 python3-pip python3-venv
else
    echo -e "${GREEN}✓ Python 3 found${NC}"
fi

echo ""
echo "Step 2: Checking picamera2..."
if ! python3 -c "import picamera2" 2>/dev/null; then
    echo -e "${YELLOW}picamera2 not found. Installing...${NC}"
    sudo apt install -y python3-picamera2
else
    echo -e "${GREEN}✓ picamera2 found${NC}"
fi

echo ""
echo "Step 3: Checking camera..."
if command -v vcgencmd &> /dev/null; then
    camera_status=$(vcgencmd get_camera)
    echo "Camera status: $camera_status"
    if [[ "$camera_status" == *"detected=0"* ]]; then
        echo -e "${YELLOW}Warning: Camera not detected${NC}"
        echo "You may need to enable the camera:"
        echo "  sudo raspi-config"
        echo "  Interface Options → Camera → Enable"
        echo ""
    else
        echo -e "${GREEN}✓ Camera detected${NC}"
    fi
fi

echo ""
echo "Step 4: Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${YELLOW}Virtual environment already exists${NC}"
fi

echo ""
echo "Step 5: Installing Python dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"

echo ""
echo "Step 6: Setting up configuration..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo -e "${GREEN}✓ Created .env file from template${NC}"
    echo ""
    echo -e "${YELLOW}IMPORTANT: Edit .env to configure your GPIO pins:${NC}"
    echo "  nano .env"
    echo ""
    echo "Default GPIO pins (BCM numbering):"
    echo "  VALVE_PIN_STEP=23   (Physical Pin 16)"
    echo "  VALVE_PIN_DIR=24    (Physical Pin 18)"
    echo "  VALVE_PIN_ENABLE=18 (Physical Pin 12)"
    echo ""
else
    echo -e "${YELLOW}.env file already exists${NC}"
fi

echo ""
echo "Step 7: Checking GPIO permissions..."
if groups | grep -q gpio; then
    echo -e "${GREEN}✓ User is in gpio group${NC}"
else
    echo -e "${YELLOW}Adding user to gpio group...${NC}"
    sudo usermod -a -G gpio $USER
    echo -e "${YELLOW}You need to log out and log back in for this to take effect${NC}"
fi

echo ""
echo "======================================"
echo -e "${GREEN}Setup Complete!${NC}"
echo "======================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Configure GPIO pins (if needed):"
echo "   nano .env"
echo ""
echo "2. Wire your stepper motor driver according to GPIO_SETUP.md"
echo ""
echo "3. Connect your Raspberry Pi Camera to the CSI port"
echo ""
echo "4. Run the application:"
echo "   source venv/bin/activate"
echo "   uvicorn app.main:app --host 0.0.0.0 --port 8000"
echo ""
echo "5. Access the dashboard:"
echo "   http://$(hostname -I | awk '{print $1}'):8000"
echo ""
echo "For detailed instructions, see:"
echo "  - SETUP.md - Complete setup guide"
echo "  - GPIO_SETUP.md - GPIO wiring help"
echo "  - .env.example - Configuration reference"
echo ""
echo "To set up as a system service, see SETUP.md"
echo ""
