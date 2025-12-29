#!/bin/bash

echo "🔧 Docker PATH düzeltiliyor..."

# Yeni Docker'ın nerede olduğunu bul
DOCKER_PATH=$(which docker 2>/dev/null || find /usr/bin -name docker 2>/dev/null | head -1)

if [ -z "$DOCKER_PATH" ]; then
    echo "🔍 Docker aranıyor..."
    DOCKER_PATH="/usr/bin/docker"
fi

echo "📍 Docker yolu: $DOCKER_PATH"

# Docker'ın gerçekten var olup olmadığını kontrol et
if [ -f "$DOCKER_PATH" ]; then
    echo "✅ Docker bulundu: $DOCKER_PATH"
    $DOCKER_PATH --version
else
    echo "❌ Docker bulunamadı, alternatif yollar deneniyor..."
    # Alternatif yollar
    for path in /usr/bin/docker /usr/local/bin/docker /snap/bin/docker; do
        if [ -f "$path" ]; then
            echo "✅ Docker bulundu: $path"
            $path --version
            break
        fi
    done
fi

# PATH'i güncelle (geçici)
export PATH="/usr/bin:/usr/local/bin:$PATH"

echo ""
echo "🔍 Güncellenmiş PATH: $PATH"
echo ""
echo "🧪 Docker testi:"
docker --version 2>&1 || echo "Hala çalışmıyor, yeni shell açın veya tam yol kullanın"

echo ""
echo "✅ PATH düzeltildi (geçici)"
echo ""
echo "📝 Kalıcı çözüm için:"
echo "   1. Yeni shell açın: bash"
echo "   2. Veya tam yol kullanın: /usr/bin/docker"
echo "   3. Veya PATH'i kalıcı yapın: echo 'export PATH=\"/usr/bin:/usr/local/bin:\$PATH\"' >> ~/.bashrc"





