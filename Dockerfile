# Use an official Python runtime as a parent image.
# Choose a version that matches your local development environment.
FROM python:3.11-slim-buster

# Set the working directory inside the container.
WORKDIR /app

# Copy the requirements file into the container at /app.
COPY requirements.txt .

# Install Python dependencies from requirements.txt.
# The --no-cache-dir flag helps reduce the image size.
RUN pip install -r requirements.txt --no-cache-dir

# Update the package lists for the base image.
RUN apt-get update -y

# Install Tesseract OCR engine and the English language pack.
RUN apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-eng

# Install poppler-utils for PDF processing (required by pdf2image).
RUN apt-get install -y --no-install-recommends poppler-utils

# If you need other Tesseract language packs, install them here.
# For example, for German:
# RUN apt-get install -y --no-install-recommends tesseract-ocr-deu

# Copy the rest of your application code into the container.
COPY . .

# Define the command to run your Flask application using Gunicorn.
# Adjust 'app:app' if your Flask app is defined differently.
CMD ["gunicorn", "app:app"]