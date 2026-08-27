FROM python:3.11-slim

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source and data
COPY . .

# Ingest knowledge base vector embeddings on build
RUN python -m src.rag.ingest

# Expose server port
EXPOSE 8000

# Set environment variables
ENV APP_HOST=0.0.0.0
ENV APP_PORT=8000
ENV PYTHONUNBUFFERED=1

# Start FastAPI application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
