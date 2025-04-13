#!/usr/bin/env bash

# Update the package lists
apt-get update -y

# Install Tesseract OCR engine
apt-get install -y tesseract-ocr

# If your images contain English text (most likely), install the English language pack
apt-get install -y tesseract-ocr-eng

# If you need other language packs, add them here.
# For example, for German:
# apt-get install -y tesseract-ocr-deu

# Install any other system-level dependencies your project might need
# For example, if you use pdf2image, you'll need poppler-utils:
# apt-get install -y poppler-utils

# Finally, install your Python dependencies
pip install -r requirements.txt