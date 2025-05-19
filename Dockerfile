FROM python:3.9-slim

# Install necessary system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    chromium-driver \
    && apt-get clean

# Set environment variables
ENV TELEGRAM_TOKEN=8145955981:AAEjOnSHc5dtbA9gunPe7f8pP9AAE4LyZYM
ENV TELEGRAM_CHAT_ID=709786113

ENV DB_NAME=insta
ENV DB_USER=postgres
ENV DB_PASSWORD=123
ENV DB_HOST=localhost
ENV DB_PORT=5432

# Create working directory
WORKDIR /app

# Copy the requirements file and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Run the application
CMD ["python", "main.py"]
