# ==========================
# Base Image
# ==========================
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# ==========================
# Install System Dependencies
# ==========================
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    fonts-liberation \
    libnss3 \
    libatk-bridge2.0-0 \
    libxkbcommon0 \
    libgbm1 \
    libasound2 \
    libxshmfence1 \
    libxrandr2 \
    libxdamage1 \
    libxcomposite1 \
    libxfixes3 \
    libpango-1.0-0 \
    libgtk-3-0 \
    && rm -rf /var/lib/apt/lists/*

# ==========================
# Install Chrome for Testing + matching ChromeDriver
# ==========================
RUN CHROME_URL="https://storage.googleapis.com/chrome-for-testing-public" \
    && CHROME_VERSION=$(curl -sS https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json \
        | grep -oP '(?<="Stable":{"version":")[^"]*') \
    && echo "Installing Chrome ${CHROME_VERSION}" \
    && curl -sSL "${CHROME_URL}/${CHROME_VERSION}/linux64/chrome-linux64.zip" -o /tmp/chrome.zip \
    && curl -sSL "${CHROME_URL}/${CHROME_VERSION}/linux64/chromedriver-linux64.zip" -o /tmp/chromedriver.zip \
    && unzip /tmp/chrome.zip -d /opt/ \
    && unzip /tmp/chromedriver.zip -d /opt/ \
    && mv /opt/chrome-linux64 /opt/chrome \
    && mv /opt/chromedriver-linux64/chromedriver /usr/local/bin/ \
    && chmod +x /usr/local/bin/chromedriver \
    && rm -rf /tmp/*.zip

# Add Chrome to PATH
ENV PATH="/opt/chrome:${PATH}"
ENV CHROME_BIN="/opt/chrome/chrome"

# ==========================
# Copy and Install Python Dependencies
# ==========================
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ==========================
# Install Playwright Chromium
# ==========================
RUN playwright install chromium

# ==========================
# Copy Application Code
# ==========================
COPY . .

# ==========================
# Create Non-root User
# ==========================
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# ==========================
# Expose and Healthcheck
# ==========================
EXPOSE 5000
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/test || exit 1

# ==========================
# Run the Flask App
# ==========================
CMD ["python", "api_güncel.py"]
