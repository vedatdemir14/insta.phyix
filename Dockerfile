# ==========================
# Python 3.11 slim base
# ==========================
FROM python:3.11-slim

# ==========================
# Build args for multi-arch
# ==========================
ARG TARGETARCH

# ==========================
# Set working directory
# ==========================
WORKDIR /app

# ==========================
# Install system dependencies
# ==========================
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    unzip \
    jq \
    gnupg \
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
# Determine architecture
# ==========================
RUN case "$TARGETARCH" in \
        amd64) ARCH="linux64" ;; \
        arm64) ARCH="linux-arm64" ;; \
        *) echo "Unsupported architecture: $TARGETARCH" && exit 1 ;; \
    esac \
    && echo $ARCH > /tmp/arch.txt

# ==========================
# Download Chrome + Chromedriver
# ==========================
RUN CHROME_URL="https://storage.googleapis.com/chrome-for-testing-public" \
    && CHROME_VERSION=$(curl -sS https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json \
        | jq -r '.channels.Stable.version') \
    && echo "Installing Chrome version ${CHROME_VERSION}" \
    && curl -sSL "${CHROME_URL}/${CHROME_VERSION}/$(cat /tmp/arch.txt)/chrome-$(cat /tmp/arch.txt).zip" -o /tmp/chrome.zip \
    && curl -sSL "${CHROME_URL}/${CHROME_VERSION}/$(cat /tmp/arch.txt)/chromedriver-$(cat /tmp/arch.txt).zip" -o /tmp/chromedriver.zip

# ==========================
# Unzip and move binaries
# ==========================
RUN unzip /tmp/chrome.zip -d /opt/chrome-temp \
    && unzip /tmp/chromedriver.zip -d /opt/chromedriver-temp \
    && find /opt/chrome-temp -type f -name chrome -exec mv {} /opt/chrome \; \
    && find /opt/chromedriver-temp -type f -name chromedriver -exec mv {} /usr/local/bin/ \; \
    && chmod +x /usr/local/bin/chromedriver /opt/chrome \
    && rm -rf /tmp/* /opt/chrome-temp /opt/chromedriver-temp

# ==========================
# Copy requirements first for caching
# ==========================
COPY requirements.txt .

# ==========================
# Install Python dependencies
# ==========================
RUN pip install --no-cache-dir -r requirements.txt

# ==========================
# Install Playwright browsers
# ==========================
RUN pip install --no-cache-dir playwright \
    && playwright install chromium

# ==========================
# Copy application code
# ==========================
COPY . .

# ==========================
# Create non-root user
# ==========================
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# ==========================
# Expose port
# ==========================
EXPOSE 5000

# ==========================
# Healthcheck
# ==========================
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/test || exit 1

# ==========================
# Run application
# ==========================
CMD ["python", "api_güncel.py"]
