FROM python:3.11-slim-buster

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt --no-cache-dir

# Install PostgreSQL client development libraries
RUN apt-get update -y && apt-get install -y libpq-dev

# Install Tesseract OCR engine and the English language pack.
RUN apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-eng

# Install poppler-utils for PDF processing (if needed).
RUN apt-get install -y --no-install-recommends poppler-utils

COPY . .

CMD ["gunicorn", "app:app"]
