#!/bin/bash

echo "🔍 Dosya kontrolü ve yeniden oluşturma..."

cd /opt/instagram-scraper

echo "📁 Mevcut dizin: $(pwd)"
echo ""

echo "📄 Tüm dosyalar:"
ls -la
echo ""

echo "🔍 docker-compose.yml arama:"
find /opt -name "docker-compose.yml" 2>/dev/null
echo ""

echo "📝 Dosyayı yeniden oluşturuyor..."
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

echo "✅ Dosya oluşturuldu"
echo ""

echo "📄 Dosya kontrolü:"
ls -la docker-compose.yml
echo ""

echo "📋 Dosya içeriği (ilk 5 satır):"
head -5 docker-compose.yml
echo ""

echo "🧪 Docker Compose config testi:"
docker-compose config 2>&1 | head -20
echo ""

echo "✅ İşlem tamamlandı"




