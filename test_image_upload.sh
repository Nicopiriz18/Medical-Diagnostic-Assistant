#!/bin/bash

# Test script for image upload functionality
# This script tests the fixed image upload error handling

set -e

echo "============================================"
echo "Image Upload Test Suite"
echo "============================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if API is running
echo "1. Checking if API is running..."
if curl -s http://localhost:8000/health > /dev/null; then
    echo -e "${GREEN}✓${NC} API is running"
else
    echo -e "${RED}✗${NC} API is not running. Please start with: docker-compose up"
    exit 1
fi

# Create a test session
echo ""
echo "2. Creating test session..."
SESSION_RESPONSE=$(curl -s -X POST http://localhost:8000/v1/sessions \
  -H "Content-Type: application/json" \
  -d '{}')

SESSION_ID=$(echo $SESSION_RESPONSE | grep -o '"id":"[^"]*"' | cut -d'"' -f4)

if [ -z "$SESSION_ID" ]; then
    echo -e "${RED}✗${NC} Failed to create session"
    echo "Response: $SESSION_RESPONSE"
    exit 1
fi

echo -e "${GREEN}✓${NC} Session created: $SESSION_ID"

# Check if test image exists
echo ""
echo "3. Checking for test image..."
TEST_IMAGE=""

# Look for any PNG file in uploads directory
if [ -d "uploads" ] && [ "$(ls -A uploads/*.png 2>/dev/null)" ]; then
    TEST_IMAGE=$(ls uploads/*.png | head -n 1)
    echo -e "${GREEN}✓${NC} Using existing test image: $TEST_IMAGE"
else
    echo -e "${YELLOW}⚠${NC} No test image found in uploads/"
    echo "   Please provide a PNG image to test with."
    echo "   Usage: $0 <path_to_image.png>"
    
    if [ -n "$1" ]; then
        TEST_IMAGE="$1"
        if [ ! -f "$TEST_IMAGE" ]; then
            echo -e "${RED}✗${NC} Image file not found: $TEST_IMAGE"
            exit 1
        fi
    else
        exit 1
    fi
fi

# Upload image
echo ""
echo "4. Uploading image..."
UPLOAD_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
  -X POST "http://localhost:8000/v1/sessions/$SESSION_ID/images" \
  -F "file=@$TEST_IMAGE")

HTTP_CODE=$(echo "$UPLOAD_RESPONSE" | grep "HTTP_CODE:" | cut -d':' -f2)
RESPONSE_BODY=$(echo "$UPLOAD_RESPONSE" | sed '/HTTP_CODE:/d')

echo ""
echo "HTTP Status Code: $HTTP_CODE"
echo "Response: $RESPONSE_BODY"

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓${NC} Image uploaded successfully!"
    echo ""
    echo "5. Checking analysis..."
    
    # Get session messages
    MESSAGES=$(curl -s "http://localhost:8000/v1/sessions/$SESSION_ID")
    
    if echo "$MESSAGES" | grep -q "He analizado la imagen"; then
        echo -e "${GREEN}✓${NC} Image analysis completed"
    else
        echo -e "${YELLOW}⚠${NC} Image analysis not found in messages"
    fi
    
elif [ "$HTTP_CODE" = "500" ]; then
    echo -e "${RED}✗${NC} Server error during upload"
    echo ""
    echo "Checking for specific error messages..."
    
    if echo "$RESPONSE_BODY" | grep -q "API key"; then
        echo -e "${YELLOW}⚠${NC} API Key Issue Detected:"
        echo "   - Make sure OPENAI_API_KEY is set in .env file"
        echo "   - Verify the API key is valid"
        echo "   - Restart containers: docker-compose down && docker-compose up"
    elif echo "$RESPONSE_BODY" | grep -q "rate_limit"; then
        echo -e "${YELLOW}⚠${NC} Rate Limit Issue:"
        echo "   - OpenAI API rate limit exceeded"
        echo "   - Wait a few minutes and try again"
    else
        echo "   Error details: $RESPONSE_BODY"
    fi
    
else
    echo -e "${RED}✗${NC} Unexpected HTTP code: $HTTP_CODE"
fi

echo ""
echo "============================================"
echo "Test Complete"
echo "============================================"
echo ""
echo "To view detailed logs:"
echo "  docker-compose logs api --tail=50"
echo ""
echo "To test manually in frontend:"
echo "  Open http://localhost:3000"
