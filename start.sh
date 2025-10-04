#!/bin/bash

# Instagram Scraper API Startup Script

echo "🚀 Starting Instagram Scraper API..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "Please create .env file with required environment variables"
    exit 1
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Create logs directory
mkdir -p logs

# Start the application
echo "🌟 Starting FastAPI server..."
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
