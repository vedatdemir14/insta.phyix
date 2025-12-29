#!/bin/bash
# Cloudflare WARP initialization script for Docker container

echo "🔧 Initializing Cloudflare WARP..."

# WARP servisini başlat (eğer systemd yoksa manuel başlat)
if command -v warp-svc &> /dev/null; then
    echo "📦 Starting WARP service..."
    warp-svc &
    sleep 5
    
    # WARP'ı kaydet (ilk kurulum için)
    if ! warp-cli status &> /dev/null; then
        echo "📝 Registering WARP..."
        warp-cli register
        sleep 2
    fi
    
    # WARP'ı bağla
    echo "🔗 Connecting to WARP..."
    warp-cli connect
    
    # Bağlantı durumunu kontrol et
    sleep 3
    if warp-cli status | grep -q "Connected"; then
        echo "✅ WARP connected successfully"
    else
        echo "⚠️ WARP connection failed, but continuing..."
    fi
else
    echo "⚠️ WARP not installed or not available"
fi

# Keep script running or exit
exec "$@"





