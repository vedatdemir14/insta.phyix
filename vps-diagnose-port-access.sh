#!/bin/bash

echo "🔍 Port erişim sorunu teşhisi..."

VPS_IP="37.140.242.29"
PORT="8000"

echo "📊 Sistem Bilgileri:"
echo "VPS IP: $VPS_IP"
echo "Port: $PORT"
echo ""

# 1. Container durumu
echo "🐳 Docker Container Durumu:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep backend
echo ""

# 2. Port dinleme kontrolü
echo "🔌 Port Dinleme Kontrolü:"
ss -tuln | grep :$PORT
netstat -tuln 2>/dev/null | grep :$PORT || echo "netstat bulunamadı"
echo ""

# 3. iptables kuralları
echo "🔥 iptables INPUT Kuralları:"
iptables -L INPUT -n -v | grep $PORT || echo "Port $PORT için kural bulunamadı"
echo ""

# 4. UFW durumu
echo "🛡️ UFW Durumu:"
ufw status | grep -E "(Status|$PORT)" || echo "UFW bilgisi alınamadı"
echo ""

# 5. Docker network kontrolü
echo "🌐 Docker Network Kontrolü:"
docker network inspect instagram-scraper_app-network 2>/dev/null | grep -A 5 "Containers" || echo "Network bilgisi alınamadı"
echo ""

# 6. Container port mapping detayı
echo "📋 Container Port Mapping Detayı:"
docker port instagram-scraper-backend 2>/dev/null || echo "Port mapping bilgisi alınamadı"
echo ""

# 7. Localhost testi
echo "🧪 Localhost Testi:"
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://localhost:$PORT/health || echo "❌ Localhost'tan erişilemiyor"
echo ""

# 8. VPS IP'den test
echo "🧪 VPS IP'den Test (127.0.0.1):"
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://127.0.0.1:$PORT/health || echo "❌ 127.0.0.1'den erişilemiyor"
echo ""

# 9. Tüm interface'lerden dinleme kontrolü
echo "🔍 Tüm Interface'lerden Dinleme:"
ss -tuln | grep ":$PORT" | grep "0.0.0.0" && echo "✅ 0.0.0.0'dan dinleniyor" || echo "⚠️ 0.0.0.0'dan dinlenmiyor"
echo ""

# 10. Docker compose dosyası kontrolü
echo "📄 docker-compose.yml Port Ayarları:"
grep -A 2 "ports:" /opt/instagram-scraper/docker-compose.yml 2>/dev/null || echo "docker-compose.yml bulunamadı"
echo ""

# 11. Son değişiklikler (isteğe bağlı)
echo "📝 Son Container Logları (hata varsa):"
docker compose logs --tail=5 backend 2>/dev/null | grep -i error || echo "Son loglarda hata yok"
echo ""

echo "✅ Teşhis tamamlandı!"
echo ""
echo "🔧 Önerilen Düzeltmeler:"
echo "1. Port mapping'i kontrol edin: docker-compose.yml'de '0.0.0.0:8000:8000' olmalı"
echo "2. iptables'ta port açık olmalı: sudo iptables -I INPUT -p tcp --dport 8000 -j ACCEPT"
echo "3. UFW aktif ve port açık olmalı: sudo ufw allow 8000/tcp"
echo "4. Container'ı yeniden başlatın: docker compose restart backend"
echo "5. Hostingdunyam firewall'unda port açık olmalı"





