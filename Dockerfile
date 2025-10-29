# ==========================
# Python 3.11 slim base
# ==========================
FROM python:3.11-slim

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
# Copy requirements first for caching
# ==========================
COPY requirements.txt .

# ==========================
# Install Python dependencies
# ==========================
RUN pip install --no-cache-dir -r requirements.txt

# ==========================
# Install Playwright + Chromium
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
