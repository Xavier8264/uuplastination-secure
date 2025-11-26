#!/bin/bash
# Quick test script for valve API endpoints

BASE_URL="http://localhost:8000"

echo "=========================================="
echo "Valve API Quick Test"
echo "=========================================="

echo -e "\n1. Health Check:"
curl -s "${BASE_URL}/api/valve/health" | python3 -m json.tool

echo -e "\n2. Open Valve (sends 'r'):"
curl -s -X POST "${BASE_URL}/api/valve/open" | python3 -m json.tool

sleep 1

echo -e "\n3. Close Valve (sends 'l'):"
curl -s -X POST "${BASE_URL}/api/valve/close" | python3 -m json.tool

echo -e "\n=========================================="
echo "Test Complete"
echo "=========================================="
