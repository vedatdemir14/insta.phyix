#!/bin/bash

echo "🔧 Backend dışarıdan erişim düzeltiliyor..."

cd /opt/instagram-scraper

# 1. Container port mapping kontrolü
echo "🔍 Container port mapping kontrolü:"
docker ps --format "table {{.Names}}\t{{.Ports}}" | grep backend
echo ""

# 2. Docker compose dosyasını kontrol et
echo "📄 docker-compose.yml port ayarları:"
grep -A 2 "ports:" docker-compose.yml
echo ""

# 3. Container'ı durdur
echo "🛑 Container durduruluyor..."
docker compose down

# 4. docker-compose.yml'i güncelle (host binding ekle)
echo "📝 docker-compose.yml güncelleniyor..."
cat > docker-compose.yml << 'EOF'
services:
  backend:
    image: vedatdemir14/instagram-scraper-backend:latest
    container_name: instagram-scraper-backend
    ports:
      - "0.0.0.0:8000:8000"  # Tüm interface'lere bind
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

echo "✅ docker-compose.yml güncellendi"
echo ""

# 5. Container'ı başlat
echo "🚀 Container başlatılıyor..."
docker compose up -d

# 6. Port kontrolü
echo "⏳ 3 saniye bekleniyor..."
sleep 3

echo "🔍 Port kontrolü:"
netstat -tuln | grep :8000 || ss -tuln | grep :8000
echo ""

# 7. Firewall kontrolü ve açma
echo "🔥 Firewall kontrolü:"
if command -v ufw &> /dev/null; then
    echo "UFW bulundu"
    ufw status | grep 8000 || echo "Port 8000 açık değil, açılıyor..."
    ufw allow 8000/tcp
    echo "✅ Port 8000 açıldı"
elif command -v firewall-cmd &> /dev/null; then
    echo "Firewalld bulundu"
    firewall-cmd --list-ports | grep 8000 || echo "Port 8000 açık değil, açılıyor..."
    firewall-cmd --add-port=8000/tcp --permanent
    firewall-cmd --reload
    echo "✅ Port 8000 açıldı"
else
    echo "⚠️ Firewall yönetim aracı bulunamadı"
fi

echo ""
echo "✅ İşlem tamamlandı!"
echo ""
echo "🧪 Test:"
echo "   curl http://37.140.242.29:8000/health"





