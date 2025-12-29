#!/bin/bash
# Fix DNS resolution issue in Docker container

cd /opt/instagram-scraper

echo "🔍 Testing DNS resolution from host..."
nslookup rltkqtlinpsueyaervdv.supabase.co

echo ""
echo "🔍 Testing DNS resolution from container..."
docker compose exec backend nslookup rltkqtlinpsueyaervdv.supabase.co || echo "❌ DNS resolution failed in container"

echo ""
echo "🔍 Testing internet connectivity from container..."
docker compose exec backend ping -c 2 8.8.8.8 || echo "❌ No internet connectivity"

echo ""
echo "🔧 Fixing DNS in docker-compose.yml..."

# Backup
cp docker-compose.yml docker-compose.yml.backup

# Update docker-compose.yml to add DNS servers
cat > docker-compose.yml << 'EOF'
services:
  backend:
    image: vedatdemir14/instagram-scraper-backend:latest
    container_name: instagram-scraper-backend
    network_mode: host
    env_file:
      - .env
    dns:
      - 8.8.8.8
      - 8.8.4.4
      - 1.1.1.1
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
      - "3000:80"
    depends_on:
      - backend
    restart: unless-stopped
    networks:
      - app-network

networks:
  app-network:
    driver: bridge
EOF

echo "✅ docker-compose.yml updated with DNS servers"

echo ""
echo "🔄 Restarting containers..."
docker compose down
docker compose up -d

echo ""
echo "⏳ Waiting 10 seconds for containers to start..."
sleep 10

echo ""
echo "🧪 Testing DNS resolution from container again..."
docker compose exec backend nslookup rltkqtlinpsueyaervdv.supabase.co

echo ""
echo "📊 Checking backend logs..."
docker compose logs --tail=30 backend


