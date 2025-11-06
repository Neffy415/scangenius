# Smaller, supported base
FROM python:3.11-slim-bookworm

# Keep Python lean & predictable
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    MALLOC_ARENA_MAX=2 \
    # Tune Gunicorn for low-RAM default; override via env if needed
    # REMOVED --bind from here; we will add it in the CMD
    GUNICORN_CMD_ARGS="--workers=1 --threads=2 --worker-class=gthread --timeout=120 --log-level=info --max-requests=1000 --max-requests-jitter=100"

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

# --- FIX ---
#
# 1. Use `sh -c` to correctly execute a shell command.
# 2. Add `gunicorn --bind 0.0.0.0:$PORT`
#    - `0.0.0.0` is required for Render to access your server.
#    - `$PORT` is the environment variable Render provides.
# 3. Reference your `$GUNICORN_CMD_ARGS` to include all your other settings.
# 4. Changed log-level to info for better startup debugging.
#
# Render will provide the $PORT variable at runtime.
# We use `sh -c` so that $PORT and $GUNICORN_CMD_ARGS are correctly expanded.
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:$PORT $GUNICORN_CMD_ARGS app:app"]