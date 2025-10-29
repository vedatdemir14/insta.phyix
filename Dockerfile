# Python 3.11 slim base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    && rm -rf /var/lib/apt/lists/*

build-and-push
buildx failed with: ERROR: failed to build: failed to solve: process "/bin/sh -c CHROME_VERSION=$(google-chrome --version | awk '{print $3}' | cut -d'.' -f1-3)     && CHROMEDRIVER_VERSION=$(curl -s \"https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION}\")     && wget -O /tmp/chromedriver.zip \"https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip\"     && unzip /tmp/chromedriver.zip -d /tmp/     && mv /tmp/chromedriver /usr/local/bin/chromedriver     && chmod +x /usr/local/bin/chromedriver     && rm /tmp/chromedriver.zip" did not complete successfully: exit code: 8

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/test || exit 1

# Run the application
CMD ["python", "api_güncel.py"]
