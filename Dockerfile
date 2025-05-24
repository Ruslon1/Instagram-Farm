# Use a base Python image
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    libffi-dev \
    wget \
    unzip \
    firefox-esr \
    python3-tk \
    && apt-get clean

# Copy project files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# This Dockerfile doesn't define CMD since the docker-compose file handles commands
