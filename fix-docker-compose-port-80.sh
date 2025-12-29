#!/bin/bash
# Fix port 80 conflict by changing frontend port

cd /opt/instagram-scraper

echo "🔧 Fixing port 80 conflict..."

# Check what's using port 80
echo "🔍 Checking port 80 usage..."
lsof -i :80 2>/dev/null || netstat -tuln | grep :80 || ss -tuln | grep :80

echo ""
echo "📝 Updating docker-compose.yml (frontend port: 80 -> 3000)..."

cat > docker-compose.yml << 'EOF'
services:
  backend:
    image: vedatdemir14/instagram-scraper-backend:latest
    container_name: instagram-scraper-backend
    network_mode: host
    env_file:
      - .env
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
      - "3000:80"  # Changed from 80:80 to 3000:80
    depends_on:
      - backend
    restart: unless-stopped
    networks:
      - app-network

networks:
  app-network:
    driver: bridge
EOF

echo "✅ docker-compose.yml updated (frontend now on port 3000)"
echo ""
echo "🔄 Restarting containers..."
docker compose down
docker compose up -d

echo ""
echo "✅ Done!"
echo "📋 Frontend is now accessible at: http://2.59.119.90:3000"
echo "📋 Backend can access 3proxy at: localhost:3128"


