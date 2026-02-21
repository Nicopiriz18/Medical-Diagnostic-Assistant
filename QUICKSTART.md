# Quick Start Guide 🚀

Get the Medical Diagnostic Assistant running in 5 minutes!

## Prerequisites

- Docker Desktop installed and running
- OpenAI API key ([get one here](https://platform.openai.com/api-keys))

## Step 1: Create .env File

Create a `.env` file in the project root:

```bash
# Minimum required configuration
OPENAI_API_KEY=sk-your-key-here

# These can stay as defaults
LLM_API_KEY=sk-your-key-here
LLM_BASE_URL=https://api.openai.com
LLM_MODEL=gpt-4-turbo
DATABASE_URL=postgresql+asyncpg://medassist_user:medassist_dev_password@postgres:5432/medassist
LOCAL_STORAGE_PATH=./uploads
```

## Step 2: Start Everything

```bash
docker-compose up -d
```

This starts:
- PostgreSQL database
- API server with auto-initialization
- Frontend (if configured)

**Wait ~30 seconds** for initialization to complete.

## Step 3: Test It!

### Health Check
```bash
curl http://localhost:8000/health
# Expected: {"ok": true}
```

### Start a Conversation

#### Create Session
```bash
curl -X POST http://localhost:8000/v1/sessions \
  -H "Content-Type: application/json" \
  -d '{}'
```

Save the session `id` from the response.

#### Send First Message
```bash
SESSION_ID="your-session-id-here"

curl -X POST http://localhost:8000/v1/sessions/$SESSION_ID/messages \
  -H "Content-Type: application/json" \
  -d '{"content": "Hola, tengo dolor de cabeza intenso desde hace 2 días"}'
```

You'll get an AI response asking follow-up questions!

#### Continue the Conversation
```bash
curl -X POST http://localhost:8000/v1/sessions/$SESSION_ID/messages \
  -H "Content-Type: application/json" \
  -d '{"content": "Es un dolor pulsátil en el lado derecho, con náuseas y me molesta la luz"}'
```

#### Get Diagnosis (after several exchanges)
```bash
curl -X POST http://localhost:8000/v1/sessions/$SESSION_ID/finalize
```

## Step 4: Explore the API

Visit **http://localhost:8000/docs** for interactive API documentation!

## Quick Commands

### View Logs
```bash
docker-compose logs -f api
```

### Restart Services
```bash
docker-compose restart
```

### Stop Everything
```bash
docker-compose down
```

### Reset Database
```bash
docker-compose down -v
docker-compose up -d
```

## Troubleshooting

### "Connection refused" error
- Wait a bit longer, services are still starting
- Check logs: `docker-compose logs api`

### "OpenAI API error"
- Verify your OpenAI API key is correct
- Check you have credits available

### Database errors
- Try: `docker-compose down -v && docker-compose up -d`

## What's Happening Behind the Scenes?

1. **PostgreSQL** starts first
2. **API container** waits for database
3. **Alembic** runs database migrations
4. **API server** starts on port 8000

## Next Steps

- Read [SETUP.md](SETUP.md) for detailed configuration
- Read [README.md](README.md) for architecture overview
- Try the Python example in SETUP.md

## Example Python Client

```python
import requests

BASE = "http://localhost:8000"

# Create session
session = requests.post(f"{BASE}/v1/sessions", json={}).json()
sid = session["id"]
print(f"Session: {sid}")

# Chat
def chat(message):
    r = requests.post(
        f"{BASE}/v1/sessions/{sid}/messages",
        json={"content": message}
    ).json()
    print(f"Agent: {r['content']}\n")
    return r

# Conversation
chat("Tengo fiebre alta y dolor de garganta")
chat("Empezó hace 3 días, la fiebre es de 39°C")
chat("También me duele mucho al tragar")

# Get diagnosis
diag = requests.post(f"{BASE}/v1/sessions/{sid}/finalize").json()
print("Assessment:", diag["assessment"])
```

## Need Help?

- Check logs: `docker-compose logs api`
- Read full docs: [SETUP.md](SETUP.md)
- Review errors in the API response

---

🎉 **You're all set!** The AI medical assistant is running and ready to conduct interviews.
