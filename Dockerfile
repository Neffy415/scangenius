# Smaller, supported base
FROM python:3.11-slim-bookworm

# Keep Python lean & predictable
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    MALLOC_ARENA_MAX=2 \
    # Tune Gunicorn for low-RAM default; override via env if needed
    GUNICORN_CMD_ARGS="--workers=1 --threads=2 --worker-class=gthread --timeout=120 --log-level=warning --max-requests=1000 --max-requests-jitter=100"

WORKDIR /app

# Only the shared libs you actually need at runtime
# (use libpq5 when using psycopg*-binary; remove entirely if you don't use Postgres)
RUN apt-get update \
 && apt-get install -y --no-install-recommends libpq5 \
 && rm -rf /var/lib/apt/lists/*

# Install Python deps first for better caching
COPY requirements.txt .
# Prefer prebuilt wheels to avoid compiling (saves RAM).
# If possible, in requirements.txt use psycopg[binary] or psycopg2-binary (not psycopg2 from source).
RUN pip install --no-compile -r requirements.txt

# Now copy your app
COPY . .

# One small worker, threaded, keeps memory in check
CMD ["bash", "-lc", "gunicorn app:app"]
