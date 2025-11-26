#!/bin/bash
# Simple valve API test script
# Tests both open and close endpoints

BASE_URL="${1:-http://localhost/secure}"

echo "Testing Valve API at: $BASE_URL"
echo "================================"
echo ""

echo "Testing OPEN valve (sends 'r')..."
RESPONSE=$(curl -s -X POST "$BASE_URL/api/valve/open" -w "\n%{http_code}")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "200" ]; then
    echo "✓ Status: $HTTP_CODE"
    echo "✓ Response: $BODY"
else
    echo "✗ Status: $HTTP_CODE"
    echo "✗ Response: $BODY"
fi

echo ""
sleep 1

echo "Testing CLOSE valve (sends 'l')..."
RESPONSE=$(curl -s -X POST "$BASE_URL/api/valve/close" -w "\n%{http_code}")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "200" ]; then
    echo "✓ Status: $HTTP_CODE"
    echo "✓ Response: $BODY"
else
    echo "✗ Status: $HTTP_CODE"
    echo "✗ Response: $BODY"
fi

echo ""
echo "Done!"
