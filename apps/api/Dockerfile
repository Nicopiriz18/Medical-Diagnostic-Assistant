FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Normalize line endings for startup script (Windows CRLF -> LF)
RUN sed -i 's/\r$//' scripts/startup.sh

# Create uploads directory
RUN mkdir -p /app/uploads

# Make startup script executable
RUN chmod +x scripts/startup.sh

# Expose port
EXPOSE 8000

# Run startup script and then start server
CMD ["sh", "-c", "sh scripts/startup.sh && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
