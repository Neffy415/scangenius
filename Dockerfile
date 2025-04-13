FROM python:3.11-slim-buster

WORKDIR /app

# Update and upgrade system packages *before* copying requirements
RUN apt-get update -y && apt-get upgrade -y

# Install PostgreSQL client development libraries
RUN apt-get install -y libpq-dev

# Copy requirements *after* installing system deps
COPY requirements.txt .

# Install Python dependencies
RUN pip install -r requirements.txt --no-cache-dir

# Install Tesseract OCR engine and the English language pack.
RUN apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-eng

# Install poppler-utils for PDF processing (if needed).
RUN apt-get install -y --no-install-recommends poppler-utils

COPY . .

CMD ["gunicorn", "app:app"]
