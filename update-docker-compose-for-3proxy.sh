#!/bin/bash
# Update docker-compose.yml to allow backend access to 3proxy

cd /opt/instagram-scraper

echo "🔧 Updating docker-compose.yml for 3proxy access..."

# Backup
cp docker-compose.yml docker-compose.yml.backup

# Update with host network mode (allows localhost:3128 access)
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  backend:
    image: vedatdemir14/instagram-scraper-backend:latest
    container_name: instagram-scraper-backend
    network_mode: host  # Host network allows access to localhost:3128 (3proxy)
    environment:
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_API_KEY=${SUPABASE_API_KEY}
      - APIFY_API_TOKEN=${APIFY_API_TOKEN}
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
      - UNIPILE_API_KEY=${UNIPILE_API_KEY}
      - UNIPILE_BASE_URL=${UNIPILE_BASE_URL}
      - DEEPL_API_KEY=${DEEPL_API_KEY}
    restart: unless-stopped
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

echo "✅ docker-compose.yml updated"
echo ""
echo "🔄 Restarting containers..."
docker compose down
docker compose up -d

echo ""
echo "✅ Done! Backend can now access 3proxy at localhost:3128"
echo "📋 In frontend, use: http://localhost:3128"

