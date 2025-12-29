#!/bin/bash

echo "🔧 Docker Compose dosyası düzeltiliyor..."

cd /opt/instagram-scraper

# Mevcut dosyayı yedekle
if [ -f docker-compose.yml ]; then
    cp docker-compose.yml docker-compose.yml.backup
    echo "✅ Yedek oluşturuldu"
fi

# Dosyayı yeniden oluştur (UTF-8 encoding ile)
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

# Dosya formatını kontrol et
echo "📄 Dosya bilgisi:"
file docker-compose.yml

# Dosya boyutunu kontrol et
echo "📊 Dosya boyutu:"
wc -l docker-compose.yml

# YAML syntax kontrolü (eğer yq veya python varsa)
if command -v python3 &> /dev/null; then
    echo "🔍 YAML syntax kontrolü:"
    python3 -c "import yaml; yaml.safe_load(open('docker-compose.yml'))" && echo "✅ YAML syntax doğru" || echo "⚠️ YAML syntax hatası"
fi

echo ""
echo "✅ Dosya yeniden oluşturuldu"
echo ""
echo "🚀 Şimdi şu komutu deneyin:"
echo "   docker-compose -f docker-compose.yml up -d"
echo "   veya"
echo "   docker compose -f docker-compose.yml up -d"





