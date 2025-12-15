#!/bin/bash

echo "🔧 Docker Compose dosyasını güncelliyor..."

cd /opt/instagram-scraper

# Docker Compose dosyasını env_file ile güncelle
cat > docker-compose.yml << 'EOF'
version: '3.8'

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

echo "✅ Docker Compose dosyası güncellendi!"
echo ""
echo "🔄 Container'ı yeniden başlatılıyor..."

# Container'ı yeniden başlat
docker compose down
docker compose up -d

echo ""
echo "⏳ 5 saniye bekleniyor..."
sleep 5

echo ""
echo "📊 Container logları:"
docker compose logs --tail=30 backend | grep -i "supabase\|connected\|database\|error" || docker compose logs --tail=30 backend

echo ""
echo "✅ İşlem tamamlandı!"
echo ""
echo "🔍 Environment variable'ları kontrol etmek için:"
echo "   docker exec instagram-scraper-backend env | grep SUPABASE"






