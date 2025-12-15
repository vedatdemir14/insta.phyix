#!/bin/bash

echo "🚀 Backend Deployment Başlatılıyor..."

# 1. Docker kurulumunu kontrol et
if ! command -v docker &> /dev/null; then
    echo "📦 Docker kuruluyor..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    systemctl start docker
    systemctl enable docker
    rm get-docker.sh
    echo "✅ Docker kuruldu"
else
    echo "✅ Docker zaten kurulu"
fi

# 2. Docker Compose kurulumunu kontrol et
if ! command -v docker-compose &> /dev/null; then
    echo "📦 Docker Compose kuruluyor..."
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    echo "✅ Docker Compose kuruldu"
else
    echo "✅ Docker Compose zaten kurulu"
fi

# 3. Mevcut container'ları durdur
echo "🛑 Mevcut container'lar durduruluyor..."
cd /opt/instagram-scraper 2>/dev/null || true
docker-compose down 2>/dev/null || true

# 4. Proje dizini oluştur
echo "📁 Proje dizini oluşturuluyor..."
mkdir -p /opt/instagram-scraper
cd /opt/instagram-scraper

# 5. Backend için docker-compose.yml oluştur (sadece backend)
echo "📝 docker-compose.yml oluşturuluyor..."
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  backend:
    image: vedatdemir14/instagram-scraper-backend:latest
    container_name: instagram-scraper-backend
    ports:
      - "8000:8000"
    environment:
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_API_KEY=${SUPABASE_API_KEY}
      - APIFY_API_TOKEN=${APIFY_API_TOKEN}
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
      - UNIPILE_API_KEY=${UNIPILE_API_KEY}
      - UNIPILE_BASE_URL=${UNIPILE_BASE_URL}
      - DEEPL_API_KEY=${DEEPL_API_KEY}
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

# 6. .env dosyası oluştur
echo "📝 .env dosyası oluşturuluyor..."
cat > .env << 'ENVEOF'
SUPABASE_URL=https://rltkqtlinpsueyaervdv.supabase.co
SUPABASE_API_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJsdGtxdGxpbnBzdWV5YWVydmR2Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NzU3NTk4NSwiZXhwIjoyMDczMTUxOTg1fQ.doT1nxL0izQRpCqzAY-StRFrzqRRuRyiKhZDwKfk_fI
APIFY_API_TOKEN=apify_api_VeivXy54nUuP7jP3zdPStvnY1bdy6P12ohvn
OPENROUTER_API_KEY=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
UNIPILE_API_KEY=k8IpFvnp.1H5f5alAgW2gK5M+J4GvW2M1lavbPHdsZfUGXBbEF+U=
UNIPILE_BASE_URL=https://api21.unipile.com:15121
DEEPL_API_KEY=721f4e0a-7600-425a-9bd4-7c4282e7770c:fx
ENVEOF

# 7. Docker image'ını çek
echo "📥 Backend Docker image'ı çekiliyor..."
docker pull vedatdemir14/instagram-scraper-backend:latest

# 8. Container'ı başlat
echo "🚀 Backend container'ı başlatılıyor..."
docker-compose up -d

# 9. Biraz bekle
echo "⏳ Servislerin başlaması bekleniyor..."
sleep 10

# 10. Durumu kontrol et
echo "📊 Container durumu:"
docker-compose ps

echo ""
echo "✅ Backend deployment tamamlandı!"
echo "🌐 Backend API: http://37.140.242.29:8000"
echo "🏥 Health check: http://37.140.242.29:8000/health"
echo ""
echo "📋 Logları görmek için: docker-compose logs -f"


