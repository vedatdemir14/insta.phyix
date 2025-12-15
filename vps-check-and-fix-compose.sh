#!/bin/bash

echo "🔍 Docker Compose dosyası kontrol ediliyor..."

# Mevcut dizini kontrol et
echo "📁 Mevcut dizin: $(pwd)"

# Dosyaların varlığını kontrol et
echo "📄 Dosya kontrolü:"
ls -la docker-compose.yml 2>/dev/null && echo "✅ docker-compose.yml mevcut" || echo "❌ docker-compose.yml bulunamadı"
ls -la .env 2>/dev/null && echo "✅ .env mevcut" || echo "❌ .env bulunamadı"

# Docker compose versiyonunu kontrol et
echo ""
echo "🐳 Docker Compose versiyonu:"
docker compose version 2>/dev/null || docker-compose version 2>/dev/null || echo "❌ Docker Compose bulunamadı"

# Dosya içeriğini göster
if [ -f docker-compose.yml ]; then
    echo ""
    echo "📋 docker-compose.yml içeriği:"
    cat docker-compose.yml
else
    echo ""
    echo "⚠️ docker-compose.yml dosyası bulunamadı, yeniden oluşturuluyor..."
    # Dosyayı yeniden oluştur
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

# Dosya izinlerini kontrol et
echo ""
echo "🔐 Dosya izinleri:"
ls -la docker-compose.yml .env 2>/dev/null

echo ""
echo "✅ Kontrol tamamlandı!"




