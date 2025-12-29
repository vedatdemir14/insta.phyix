#!/bin/bash

echo "🔧 Backend-only docker-compose.yml oluşturuluyor..."

cd /opt/instagram-scraper

# Backend-only docker-compose.yml oluştur
cat > docker-compose.yml << 'EOF'
services:
  backend:
    image: vedatdemir14/instagram-scraper-backend:latest
    container_name: instagram-scraper-backend
    ports:
      - "8000:8000"
    env_file:
      - .env
    restart: unless-stopped
    networks:
      - app-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

networks:
  app-network:
    driver: bridge
EOF

echo "✅ Backend-only docker-compose.yml oluşturuldu"
echo ""
echo "📋 Dosya içeriği:"
cat docker-compose.yml
echo ""
echo "🚀 Container'ı başlatmak için:"
echo "   docker compose up -d"





