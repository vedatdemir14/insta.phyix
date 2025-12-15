#!/bin/bash

echo "🔧 Standart Docker kurulumu (Snap'ten kurtulma)..."

# Snap Docker'ı kaldır
echo "🗑️ Snap Docker kaldırılıyor..."
snap remove docker 2>/dev/null || true

# Standart Docker kurulumu
echo "📥 Standart Docker kuruluyor..."
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
rm get-docker.sh

# Docker servisini başlat
echo "🚀 Docker servisi başlatılıyor..."
systemctl start docker
systemctl enable docker

# Docker Compose plugin zaten Docker ile birlikte geliyor
echo "✅ Docker kuruldu"

# Test
echo ""
echo "🔍 Docker versiyonu:"
docker --version

echo ""
echo "🔍 Docker Compose versiyonu:"
docker compose version

echo ""
echo "✅ Kurulum tamamlandı!"
echo ""
echo "📝 Şimdi şu komutları çalıştırabilirsiniz:"
echo "   cd /opt/instagram-scraper"
echo "   docker compose up -d"




