#!/bin/bash

echo "🔧 Port erişimini geri yükleme..."

cd /opt/instagram-scraper

# 1. Container'ı durdur
echo "🛑 Container durduruluyor..."
docker compose down

# 2. docker-compose.yml'i kontrol et ve düzelt
echo "📝 docker-compose.yml kontrol ediliyor..."
if ! grep -q "0.0.0.0:8000:8000" docker-compose.yml; then
    echo "⚠️ Port mapping düzeltiliyor..."
    cat > docker-compose.yml << 'EOF'
services:
  backend:
    image: vedatdemir14/instagram-scraper-backend:latest
    container_name: instagram-scraper-backend
    ports:
      - "0.0.0.0:8000:8000"
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
else
    echo "✅ Port mapping zaten doğru"
fi

# 3. iptables kurallarını ekle
echo "🔥 iptables kuralları ekleniyor..."
iptables -I INPUT -p tcp --dport 8000 -j ACCEPT 2>/dev/null || echo "Kural zaten var veya eklenemedi"
iptables -I OUTPUT -p tcp --sport 8000 -j ACCEPT 2>/dev/null || echo "Kural zaten var veya eklenemedi"

# 4. UFW'yi aktif et ve port aç
echo "🛡️ UFW ayarları..."
ufw --force enable 2>/dev/null || echo "UFW zaten aktif"
ufw allow 8000/tcp 2>/dev/null || echo "Port zaten açık"

# 5. Container'ı başlat
echo "🚀 Container başlatılıyor..."
docker compose up -d

# 6. Bekle
echo "⏳ 5 saniye bekleniyor..."
sleep 5

# 7. Kontroller
echo ""
echo "📊 Durum Kontrolleri:"
echo "Container:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep backend
echo ""
echo "Port dinleme:"
ss -tuln | grep :8000
echo ""
echo "Localhost testi:"
curl -s http://localhost:8000/health && echo "" || echo "❌ Localhost'tan erişilemiyor"
echo ""

echo "✅ İşlem tamamlandı!"
echo ""
echo "⚠️ Eğer hala dışarıdan erişilemiyorsa:"
echo "   - Hostingdunyam firewall'unda port 8000'in açık olduğundan emin olun"
echo "   - Destek ekibine başvurun: VPS IP 37.140.242.29, Port 8000 TCP"





