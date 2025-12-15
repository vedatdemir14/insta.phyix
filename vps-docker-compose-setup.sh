#!/bin/bash

echo "🚀 Docker Compose kurulumu (docker compose plugin)"

cd /opt/instagram-scraper

# Docker Compose plugin versiyonunu kontrol et
echo "🔍 Docker Compose versiyonu:"
docker compose version

# docker-compose.yml dosyasını kontrol et
echo ""
echo "📄 Dosya kontrolü:"
if [ -f docker-compose.yml ]; then
    echo "✅ docker-compose.yml mevcut"
    ls -la docker-compose.yml
else
    echo "❌ docker-compose.yml bulunamadı, oluşturuluyor..."
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
    echo "✅ docker-compose.yml oluşturuldu"
fi

# Config testi
echo ""
echo "🧪 Config testi:"
docker compose config > /dev/null 2>&1 && echo "✅ Config doğru" || echo "❌ Config hatası"

echo ""
echo "✅ Hazır! Şimdi şu komutu çalıştırabilirsiniz:"
echo "   docker compose up -d"




