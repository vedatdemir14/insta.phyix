#!/bin/bash

echo "🔧 Dışarıdan erişim sorunu gideriliyor..."

# 1. iptables kontrolü
echo "🔍 iptables kuralları:"
iptables -L -n | grep 8000 || echo "iptables'da 8000 portu için özel kural yok"
echo ""

# 2. iptables INPUT chain kontrolü
echo "🔍 iptables INPUT chain:"
iptables -L INPUT -n -v | head -20
echo ""

# 3. iptables'ta port aç
echo "🔥 iptables'ta port 8000 açılıyor..."
iptables -I INPUT -p tcp --dport 8000 -j ACCEPT
iptables -I OUTPUT -p tcp --sport 8000 -j ACCEPT

# 4. iptables kurallarını kaydet (kalıcı yap)
if command -v iptables-save &> /dev/null; then
    echo "💾 iptables kuralları kaydediliyor..."
    iptables-save > /etc/iptables/rules.v4 2>/dev/null || \
    mkdir -p /etc/iptables && iptables-save > /etc/iptables/rules.v4
    echo "✅ Kurallar kaydedildi"
fi

# 5. UFW'yi aktif et ve port aç
echo "🔥 UFW aktif ediliyor ve port açılıyor..."
ufw --force enable
ufw allow 8000/tcp
ufw status
echo ""

# 6. Port kontrolü
echo "🔍 Port durumu:"
ss -tuln | grep :8000
echo ""

# 7. Container durumu
echo "🐳 Container durumu:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""

# 8. Backend log kontrolü
echo "📋 Son backend logları:"
docker compose logs --tail=10 backend
echo ""

echo "✅ İşlem tamamlandı!"
echo ""
echo "🧪 Test komutları:"
echo "   # VPS'ten test:"
echo "   curl http://localhost:8000/health"
echo ""
echo "   # Dışarıdan test (başka bir makineden):"
echo "   curl http://37.140.242.29:8000/health"
echo ""
echo "⚠️  Eğer hala çalışmıyorsa, VPS sağlayıcınızın firewall ayarlarını kontrol edin!"
echo "   (Örn: DigitalOcean, AWS, Azure, vb. kendi firewall'ları var)"





