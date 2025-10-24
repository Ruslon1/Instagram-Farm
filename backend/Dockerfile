FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Browser environment (early for caching)
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROME_DRIVER=/usr/bin/chromedriver
ENV DISPLAY=:99
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
ENV PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1
ENV PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS=true

# Install system dependencies in one layer (rarely changes)
RUN apt-get update && apt-get install -y \
    wget curl unzip gnupg \
    postgresql-client \
    chromium chromium-driver \
    xvfb \
    # Minimal Playwright deps
    libnss3 libnspr4 libatk-bridge2.0-0 \
    libdrm2 libxkbcommon0 libxcomposite1 \
    libxdamage1 libxrandr2 libgbm1 \
    libxss1 libasound2 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

WORKDIR /app

# Copy requirements first (better caching)
COPY requirements.txt .

# Install Python packages (cached if requirements.txt unchanged)
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (cached separately)
RUN playwright install chromium --with-deps

# Create startup script
RUN echo '#!/bin/bash\nXvfb :99 -screen 0 1024x768x24 > /dev/null 2>&1 &\nexec "$@"' > /usr/local/bin/start-app.sh && \
    chmod +x /usr/local/bin/start-app.sh

# Copy application code LAST (changes most often)
COPY . .

# Create directories
RUN mkdir -p videos sessions logs static

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

ENTRYPOINT ["/usr/local/bin/start-app.sh"]
CMD ["python", "main.py"]