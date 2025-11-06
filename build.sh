#!/usr/bin/env bash

# Update the package lists
apt-get update -y

# Install Tesseract OCR engine


# Install English language pack (if needed)


# Install poppler-utils (for PDF processing with pdf2image)
apt-get install -y poppler-utils

# If you need other language packs for Tesseract, add them here:
# apt-get install -y tesseract-ocr-deu

# Finally, install your Python dependencies
pip install -r requirements.txt
