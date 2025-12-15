#!/bin/bash

echo "🔧 Docker daemon düzeltiliyor..."

# Snap ile kurulan Docker için servisi başlat
echo "🚀 Docker servisi başlatılıyor..."
snap start docker

# Servisi aktif et (otomatik başlatma için)
echo "✅ Docker servisi aktif ediliyor..."
snap enable docker

# Docker socket kontrolü
echo "🔍 Docker socket kontrol ediliyor..."
if [ -S /var/run/docker.sock ]; then
    echo "✅ Docker socket mevcut"
else
    echo "⚠️ Docker socket bulunamadı, alternatif yollar deneniyor..."
    # Snap Docker için socket yolu farklı olabilir
    if [ -S /run/snap.docker/docker.sock ]; then
        echo "✅ Snap Docker socket bulundu"
        export DOCKER_HOST=unix:///run/snap.docker/docker.sock
    fi
fi

# Docker versiyonunu kontrol et
echo "📊 Docker versiyonu kontrol ediliyor..."
docker --version

# Docker daemon durumunu kontrol et
echo "🔍 Docker daemon durumu:"
snap services docker

echo ""
echo "✅ İşlem tamamlandı!"
echo ""
echo "📝 Eğer hala çalışmıyorsa, şu komutları deneyin:"
echo "   sudo snap restart docker"
echo "   sudo systemctl restart snap.docker.dockerd.service"
echo ""
echo "🔍 Docker durumunu kontrol etmek için:"
echo "   docker ps"
echo "   snap services docker"




