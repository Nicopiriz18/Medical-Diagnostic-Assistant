# Testing Guide: Image Upload Fix

This guide explains how to test the image upload functionality after implementing the error handling improvements.

## Prerequisites

1. **Create .env file** (if not already present):
   ```bash
   cp .env.example .env
   ```

2. **Add your OpenAI API Key** to `.env`:
   ```env
   OPENAI_API_KEY=sk-your-actual-api-key-here
   ```

3. **Restart Docker containers** to pick up environment changes:
   ```bash
   docker-compose down
   docker-compose up --build
   ```

## Test Scenarios

### Scenario 1: Missing API Key (Error Handling Test)

**Setup:**
- Remove or comment out `OPENAI_API_KEY` in `.env`
- Restart containers

**Expected Behavior:**
- Application should start with warning messages in logs:
  ```
  ❌ OPENAI_API_KEY is not configured - image analysis and chat will not work
  ```
- When uploading an image, you should see a clear error message:
  ```
  Error de configuración: La API key de OpenAI no está configurada o es inválida.
  ```

**Test:**
```bash
# Check logs when app starts
docker-compose logs api | grep "OPENAI_API_KEY"

# Try to upload an image (should fail gracefully)
curl -X POST "http://localhost:8000/v1/sessions/<session_id>/images" \
  -F "file=@test_image.png"
```

### Scenario 2: Invalid API Key (Authentication Error)

**Setup:**
- Set `OPENAI_API_KEY=sk-invalid-key-12345` in `.env`
- Restart containers

**Expected Behavior:**
- Application starts without warnings
- Image upload fails with authentication error
- Error logs show: "OpenAI API authentication failed"
- User sees: "Error de configuración: La API key de OpenAI no está configurada o es inválida"

### Scenario 3: Valid API Key (Success Case)

**Setup:**
- Set valid `OPENAI_API_KEY` in `.env`
- Restart containers

**Expected Behavior:**
- Application starts with success messages:
  ```
  ✓ OpenAI API Key is configured
  ✓ Database URL is configured
  ✓ Using local storage at: ./uploads
  ```
- Image upload succeeds
- Image is analyzed by GPT-4o Vision
- Analysis appears in the chat

**Test:**
```bash
# 1. Create a session
SESSION_RESPONSE=$(curl -s -X POST http://localhost:8000/v1/sessions \
  -H "Content-Type: application/json" \
  -d '{}')

SESSION_ID=$(echo $SESSION_RESPONSE | jq -r '.id')
echo "Session ID: $SESSION_ID"

# 2. Upload an image (use any .png file)
curl -X POST "http://localhost:8000/v1/sessions/$SESSION_ID/images" \
  -F "file=@your_test_image.png" \
  -v

# 3. Check the response and logs
docker-compose logs api --tail=50
```

### Scenario 4: Using the Frontend

**Test:**
1. Open http://localhost:3000 in your browser
2. Start a new conversation
3. Click the 📎 (paperclip) button
4. Select a PNG image
5. Observe the behavior:
   - **With valid API key:** Image uploads, analysis appears
   - **Without API key:** Clear error message is displayed

## Checking Logs

The improved error handling adds detailed logging:

```bash
# Watch logs in real-time
docker-compose logs -f api

# Check for specific events
docker-compose logs api | grep "Saving image"
docker-compose logs api | grep "Image analysis"
docker-compose logs api | grep "ERROR"
```

## Expected Log Output (Success Case)

```
INFO - ✓ OpenAI API Key is configured
INFO - ✓ Database URL is configured
INFO - ✓ Using local storage at: ./uploads
INFO - Saving image for session abc-123: test.png
INFO - Image saved successfully: /uploads/abc-123_def456.png
INFO - Processing image through analyzer: /uploads/abc-123_def456.png
INFO - Initializing ImageAnalyzerAgent with model: gpt-4o
INFO - Calling OpenAI Vision API for image analysis
INFO - Received response from OpenAI Vision API
INFO - Image analysis completed successfully
```

## Expected Log Output (Error Case - No API Key)

```
ERROR - ❌ OPENAI_API_KEY is not configured - image analysis and chat will not work
ERROR - OPENAI_API_KEY is not configured!
ERROR - Error uploading/analyzing image for session abc-123: OPENAI_API_KEY must be configured
```

## Troubleshooting

### Problem: Still seeing generic "Error al subir la imagen"

**Solution:** Make sure you've restarted the containers after code changes:
```bash
docker-compose down
docker-compose up --build
```

### Problem: Can't find .env file

**Solution:** Create it from the example:
```bash
cp .env.example .env
nano .env  # or use your preferred editor
```

### Problem: Image uploads but no analysis

**Check:**
1. Verify API key is valid and has credits
2. Check logs for specific error messages
3. Verify the image format is supported (.png, .jpg, etc.)

## Success Criteria

✅ Application logs show clear status of configuration at startup
✅ Missing API key produces helpful error message (not generic 500)
✅ Invalid API key produces authentication error message
✅ Valid API key allows successful image upload and analysis
✅ All errors are logged with full details for debugging
✅ User sees friendly error messages in Spanish
