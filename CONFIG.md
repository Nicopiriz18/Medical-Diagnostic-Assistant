# Configuration Guide

Create a `.env` file in the root directory with the following variables:

```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL_TEXT=gpt-4-turbo
OPENAI_MODEL_VISION=gpt-4o

# Legacy LLM Config (for backward compatibility)
LLM_BASE_URL=https://api.openai.com
LLM_API_KEY=your_openai_api_key_here
LLM_MODEL=gpt-4-turbo

# PostgreSQL Configuration
DATABASE_URL=postgresql+asyncpg://medassist_user:medassist_dev_password@postgres:5432/medassist

# Storage Configuration
# For local storage (default in development)
LOCAL_STORAGE_PATH=./uploads
# For S3 (uncomment for production)
# S3_BUCKET=medical-images
# S3_REGION=us-east-1
# AWS_ACCESS_KEY_ID=your_access_key
# AWS_SECRET_ACCESS_KEY=your_secret_key

# Agent Configuration
MAX_INTERVIEW_TURNS=20
CONFIDENCE_THRESHOLD=0.7

# Application Environment
APP_ENV=dev
```

## Setup Instructions

1. Copy this configuration to a new `.env` file
2. Replace placeholder values with your actual API keys
3. Ensure PostgreSQL credentials match docker-compose.yml
4. Create the uploads directory: `mkdir uploads`
