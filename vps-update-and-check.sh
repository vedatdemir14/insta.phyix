#!/bin/bash

echo "🔄 Container güncelleniyor ve kontrol ediliyor..."

cd /opt/instagram-scraper

# Version uyarısını düzelt
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

# Container'ı yeniden başlat
echo "🛑 Container durduruluyor..."
docker compose down

echo "📥 Yeni image çekiliyor..."
docker pull vedatdemir14/instagram-scraper-backend:latest

echo "🚀 Container başlatılıyor..."
docker compose up -d

echo "⏳ 10 saniye bekleniyor (backend başlaması için)..."
sleep 10

echo ""
echo "📊 Container durumu:"
docker compose ps

echo ""
echo "📋 Son 50 satır log:"
docker compose logs --tail=50 backend

echo ""
echo "🔍 Chrome ve ChromeDriver kontrolü:"
docker exec instagram-scraper-backend google-chrome --version 2>/dev/null || echo "Chrome kontrol edilemedi"
docker exec instagram-scraper-backend chromedriver --version 2>/dev/null || echo "ChromeDriver kontrol edilemedi"

echo ""
echo "🏥 Health check:"
curl -s http://localhost:8000/health || echo "❌ Health check başarısız"






