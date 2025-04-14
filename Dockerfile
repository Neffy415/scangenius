FROM python:3.11-slim-buster

ENV DEBIAN_FRONTEND=noninteractive

# Set working directory
WORKDIR /app

# Update system packages
RUN apt-get update -y && apt-get upgrade -y

# Install system dependencies
RUN apt-get install -y --no-install-recommends \
    libpq-dev \
    libgl1 \
    tesseract-ocr \
    tesseract-ocr-eng \
    poppler-utils \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy Python requirements first to leverage Docker caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy app source code into container
COPY . .

# Start app with gunicorn
CMD ["gunicorn", "app:app"]
