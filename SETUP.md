# Medical Diagnostic Assistant - Setup Guide

## Overview

This is a complete medical diagnostic assistant system that uses:
- **LangGraph agents** for conversational medical interviews
- **GPT-4o Vision** for medical image analysis
- **PostgreSQL** for session storage
- **FastAPI** for the backend API

## Prerequisites

1. **Python 3.11+**
2. **Docker & Docker Compose**
3. **API Keys:**
   - OpenAI API key (for GPT-4o)

## Quick Start

### 1. Clone and Navigate

```bash
cd Medical-Diagnostic-Assistant
```

### 2. Create Environment File

Create a `.env` file in the root directory (see `CONFIG.md` for template):

```env
# OpenAI
OPENAI_API_KEY=your_openai_key_here
OPENAI_MODEL_TEXT=gpt-4-turbo
OPENAI_MODEL_VISION=gpt-4o

# For legacy endpoint compatibility
LLM_BASE_URL=https://api.openai.com
LLM_API_KEY=your_openai_key_here
LLM_MODEL=gpt-4-turbo

# Database
DATABASE_URL=postgresql+asyncpg://medassist_user:medassist_dev_password@postgres:5432/medassist

# Storage (local for development)
LOCAL_STORAGE_PATH=./uploads

# Agent Config
MAX_INTERVIEW_TURNS=20
CONFIDENCE_THRESHOLD=0.7
APP_ENV=dev
```

### 3. Start Services with Docker

```bash
docker-compose up -d
```

This will start:
- PostgreSQL database
- API server (port 8000)
- Web frontend (port 3000)

### 4. Initialize Database

```bash
# Enter the API container
docker-compose exec api bash

# Run migrations
alembic upgrade head
```

### 5. Verify Setup

```bash
# Check health endpoint
curl http://localhost:8000/health

# Expected: {"ok": true}
```

## API Endpoints

### Legacy Endpoint (One-shot analysis)

```bash
POST /v1/analyze
```

### New Agent-Based Endpoints

#### 1. Create Session
```bash
POST /v1/sessions
Content-Type: application/json

{
  "user_id": "optional-user-id",
  "patient_info": {}
}

Response: { "id": "session-uuid", ... }
```

#### 2. Send Message
```bash
POST /v1/sessions/{session_id}/messages
Content-Type: application/json

{
  "content": "Tengo dolor de cabeza desde hace 3 días",
  "images": []
}

Response: { "id": 1, "role": "assistant", "content": "...", ... }
```

#### 3. Upload Image
```bash
POST /v1/sessions/{session_id}/images
Content-Type: multipart/form-data

file: [image file]

Response: { "url": "/uploads/...", "filename": "...", ... }
```

#### 4. Get Session History
```bash
GET /v1/sessions/{session_id}

Response: { "id": "...", "messages": [...], ... }
```

#### 5. Force Diagnosis
```bash
POST /v1/sessions/{session_id}/finalize

Response: { "status": "completed", "assessment": {...} }
```

#### 6. Get Diagnosis
```bash
GET /v1/sessions/{session_id}/diagnosis

Response: { "assessment": {...}, "confidence_score": 0.85, ... }
```

## Example Usage Flow

```python
import requests

BASE_URL = "http://localhost:8000"

# 1. Create session
session = requests.post(f"{BASE_URL}/v1/sessions", json={}).json()
session_id = session["id"]

# 2. Send initial message
msg = requests.post(
    f"{BASE_URL}/v1/sessions/{session_id}/messages",
    json={"content": "Hola, tengo dolor en el pecho"}
).json()
print(f"Agent: {msg['content']}")

# 3. Continue conversation
msg = requests.post(
    f"{BASE_URL}/v1/sessions/{session_id}/messages",
    json={"content": "Empezó hace 2 horas, es un dolor opresivo"}
).json()
print(f"Agent: {msg['content']}")

# 4. Upload image (optional)
with open("chest_xray.jpg", "rb") as f:
    img = requests.post(
        f"{BASE_URL}/v1/sessions/{session_id}/images",
        files={"file": f}
    ).json()

# 5. Continue until agent decides to diagnose, or force it
diagnosis = requests.post(
    f"{BASE_URL}/v1/sessions/{session_id}/finalize"
).json()

print("Assessment:", diagnosis["assessment"])
```

## Development

### Running Locally (without Docker)

```bash
cd apps/api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run PostgreSQL separately
# Update DATABASE_URL in .env to point to your local Postgres

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload --port 8000
```

### Running Tests

```bash
cd apps/api
pytest tests/ -v
```

### Adding More Medical Knowledge

```bash
# Add a new guideline (markdown or PDF)
cp my_guideline.md apps/api/data/clinical_guidelines/

# Ingest it
python scripts/ingest_knowledge.py --file apps/api/data/clinical_guidelines/my_guideline.md

# Or add cases to sample_cases.json and re-ingest
python scripts/ingest_knowledge.py --file apps/api/data/sample_cases.json
```

## Architecture

```
┌─────────────┐
│   User      │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────┐
│         FastAPI Endpoints           │
└──────┬─────────────────────┬────────┘
       │                     │
       ▼                     ▼
┌─────────────┐      ┌─────────────┐
│  LangGraph  │      │ PostgreSQL  │
│   Agents    │      │  Sessions   │
└──────┬──────┘      └─────────────┘
       │
       ▼
   ┌─────────────┐
   │ GPT-4o      │
   │ Vision      │
   └─────────────┘
```

### Agent Flow

1. **Interviewer Agent**: Asks questions, extracts information
2. **Image Analyzer Agent**: Analyzes medical images when uploaded
3. **Diagnostic Agent**: Generates final assessment
4. **Orchestrator**: Manages flow between agents

## Troubleshooting

### Database Connection Issues

```bash
# Check if PostgreSQL is running
docker-compose ps

# View logs
docker-compose logs postgres

# Restart services
docker-compose restart
```

### Migration Issues

```bash
# Check current migration
alembic current

# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Production Considerations

1. **Security:**
   - Use proper authentication/authorization
   - Encrypt sensitive patient data
   - Use HTTPS
   - Restrict CORS origins

2. **Storage:**
   - Use S3 for image storage in production
   - Set `S3_BUCKET`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`

3. **Database:**
   - Use managed PostgreSQL (AWS RDS, etc.)
   - Set up backups
   - Use strong passwords

4. **Monitoring:**
   - Add logging and monitoring
   - Track API usage and costs (OpenAI)
   - Monitor error rates

5. **Medical Compliance:**
   - This is a **support tool**, not a replacement for medical professionals
   - Add proper disclaimers
   - Consider HIPAA compliance if handling real patient data
   - Get legal/medical validation before clinical use

## Support

For issues or questions:
1. Check logs: `docker-compose logs api`
2. Review configuration in `.env`
3. Verify API keys are valid

## License

See LICENSE file.
