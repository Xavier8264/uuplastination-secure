#!/usr/bin/env python3
"""Simple test script for the valve API.

This script demonstrates the valve API functionality:
- Sends 'r' character when calling /api/valve/open
- Sends 'l' character when calling /api/valve/close

Usage:
    python test_valve_api.py
"""

import time
import requests

BASE_URL = "http://localhost:8000"

def test_valve_health():
    """Test the health endpoint."""
    print("Testing valve health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/valve/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_valve_open():
    """Test opening the valve (sends 'r')."""
    print("\nTesting valve open (sends 'r')...")
    try:
        response = requests.post(f"{BASE_URL}/api/valve/open")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_valve_close():
    """Test closing the valve (sends 'l')."""
    print("\nTesting valve close (sends 'l')...")
    try:
        response = requests.post(f"{BASE_URL}/api/valve/close")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    print("=" * 60)
    print("Valve API Test Script")
    print("=" * 60)
    
    # Test health
    health_ok = test_valve_health()
    
    if not health_ok:
        print("\n⚠️  Health check failed. Make sure:")
        print("   1. The API server is running")
        print("   2. The serial device /dev/ttyACM0 exists")
        print("   3. You have permissions to access the serial port")
        return
    
    # Test open (sends 'r')
    time.sleep(0.5)
    test_valve_open()
    
    # Test close (sends 'l')
    time.sleep(0.5)
    test_valve_close()
    
    print("\n" + "=" * 60)
    print("Test complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
