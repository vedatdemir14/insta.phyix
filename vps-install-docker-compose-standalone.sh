#!/bin/bash

echo "🔧 Standart Docker Compose kurulumu başlatılıyor..."

# Snap Docker Compose'u kaldır (eğer varsa)
if command -v docker-compose &> /dev/null && snap list docker-compose &> /dev/null; then
    echo "🗑️ Snap Docker Compose kaldırılıyor..."
    snap remove docker-compose 2>/dev/null || true
fi

# Standart Docker Compose kurulumu
echo "📥 Docker Compose indiriliyor..."
DOCKER_COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d\" -f4)
DOCKER_COMPOSE_VERSION=${DOCKER_COMPOSE_VERSION:-v2.24.0}

echo "📦 Docker Compose versiyonu: $DOCKER_COMPOSE_VERSION"

# Docker Compose'u indir ve kur
curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# Çalıştırılabilir yap
chmod +x /usr/local/bin/docker-compose

# Alternatif olarak docker compose plugin olarak da kurulabilir
# Ama önce mevcut docker-compose'un çalışıp çalışmadığını kontrol et

echo "✅ Docker Compose kuruldu"
echo ""
echo "🔍 Versiyon kontrolü:"
/usr/local/bin/docker-compose version

echo ""
echo "✅ Kurulum tamamlandı!"
echo ""
echo "📝 Artık şu komutları kullanabilirsiniz:"
echo "   docker-compose up -d"
echo "   veya"
echo "   /usr/local/bin/docker-compose up -d"





