#!/bin/bash
# VPS Fix and View Logs Script

echo "🔧 Fixing docker-compose permissions..."
chmod +x /usr/local/bin/docker-compose

echo "📂 Checking project directory..."
if [ ! -d "/opt/instagram-scraper" ]; then
    echo "❌ Project directory not found at /opt/instagram-scraper"
    echo "📝 Creating directory..."
    mkdir -p /opt/instagram-scraper
    cd /opt/instagram-scraper
    echo "⚠️  You need to create docker-compose.yml file first!"
    exit 1
fi

cd /opt/instagram-scraper

echo "📋 Checking docker-compose.yml..."
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ docker-compose.yml not found!"
    echo "📝 Creating docker-compose.yml..."
    
    cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  backend:
    image: vedatdemir14/instagram-scraper-backend:latest
    container_name: instagram-scraper-backend
    ports:
      - "8000:8000"
    environment:
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_API_KEY=${SUPABASE_API_KEY}
      - APIFY_API_TOKEN=${APIFY_API_TOKEN}
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
      - UNIPILE_API_KEY=${UNIPILE_API_KEY}
      - UNIPILE_BASE_URL=${UNIPILE_BASE_URL}
      - DEEPL_API_KEY=${DEEPL_API_KEY}
    restart: unless-stopped
    networks:
      - app-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    image: vedatdemir14/instagram-scraper-frontend:latest
    container_name: instagram-scraper-frontend
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: unless-stopped
    networks:
      - app-network

networks:
  app-network:
    driver: bridge
EOF
    echo "✅ docker-compose.yml created"
fi

echo "📋 Checking .env file..."
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file..."
    cat > .env << 'ENVEOF'
SUPABASE_URL=https://rltkqtlinpsueyaervdv.supabase.co
SUPABASE_API_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJsdGtxdGxpbnBzdWV5YWVydmR2Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NzU3NTk4NSwiZXhwIjoyMDczMTUxOTg1fQ.doT1nxL0izQRpCqzAY-StRFrzqRRuRyiKhZDwKfk_fI
APIFY_API_TOKEN=apify_api_VeivXy54nUuP7jP3zdPStvnY1bdy6P12ohvn
OPENROUTER_API_KEY=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
UNIPILE_API_KEY=k8IpFvnp.1H5f5alAgW2gK5M+J4GvW2M1lavbPHdsZfUGXBbEF+U=
UNIPILE_BASE_URL=https://api21.unipile.com:15121
DEEPL_API_KEY=721f4e0a-7600-425a-9bd4-7c4282e7770c:fx
ENVEOF
    echo "✅ .env file created"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "📊 Container status:"
docker compose ps || docker-compose ps

echo ""
echo "📋 To view logs, run:"
echo "   docker compose logs -f backend"
echo "   OR"
echo "   docker logs instagram-scraper-backend -f"

