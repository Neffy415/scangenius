# Use a supported Debian
FROM python:3.11-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app

# Install system deps (no upgrade step needed in containers)
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      libpq-dev gcc \
 && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

CMD ["gunicorn", "app:app"]
