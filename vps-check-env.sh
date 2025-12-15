#!/bin/bash

echo "🔍 Backend Container Environment Variables Kontrolü"
echo ""

# Container'a gir ve environment variable'ları kontrol et
echo "📋 Container environment variables:"
docker exec instagram-scraper-backend env | grep -E "(SUPABASE|APIFY|OPENROUTER|UNIPILE|DEEPL)" | sort

echo ""
echo "📁 .env dosyası kontrolü:"
cd /opt/instagram-scraper
if [ -f .env ]; then
    echo "✅ .env dosyası mevcut"
    echo "İçerik:"
    cat .env
else
    echo "❌ .env dosyası bulunamadı!"
fi

echo ""
echo "🐳 Docker Compose environment variables:"
docker compose config | grep -A 20 "environment:"

echo ""
echo "📊 Container logları (son 20 satır):"
docker compose logs --tail=20 backend






