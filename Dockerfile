# Smaller, supported base
FROM python:3.11-slim-bookworm

# Keep Python lean & predictable
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    MALLOC_ARENA_MAX=2 \
    GUNICORN_CMD_ARGS="--workers=1 --threads=2 --worker-class=gthread --timeout=120 --log-level=info --max-requests=1000 --max-requests-jitter=100"

WORKDIR /app

# Install PostgreSQL client library (needed for psycopg2)
RUN apt-get update \
 && apt-get install -y --no-install-recommends libpq5 \
 && rm -rf /var/lib/apt/lists/*

# Install Python deps first for better caching
COPY requirements.txt .
RUN pip install --no-compile -r requirements.txt

# Copy your app
COPY . .

# Start with Gunicorn
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:$PORT $GUNICORN_CMD_ARGS app:app"]
