FROM python:3.11-slim-buster
ENV DEBIAN_FRONTEND=noninteractive 
WORKDIR /app 
# Update and upgrade system packages *before* copying requirements 
RUN apt-get update -y && apt-get upgrade -y 
# Install PostgreSQL client development libraries (if needed) 
RUN apt-get install -y libpq-dev 
# Copy requirements *after* installing system deps 
COPY requirements.txt . 
# Install Python dependencies 
RUN pip install -r requirements.txt --no-cache-dir COPY . . 
CMD ["gunicorn", "app:app"]
