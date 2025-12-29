#!/bin/bash

echo "🔍 Docker Compose debug başlatılıyor..."

cd /opt/instagram-scraper

echo "📁 Mevcut dizin: $(pwd)"
echo ""

echo "📄 Dosya kontrolü:"
ls -la docker-compose.yml
echo ""

echo "🔍 Hangi docker-compose kullanılıyor:"
which docker-compose
echo ""

echo "📋 docker-compose komutunun tam yolu:"
type docker-compose
echo ""

echo "🔍 Docker Compose versiyonu:"
docker-compose version
echo ""

echo "📄 Dosya içeriği (ilk 10 satır):"
head -10 docker-compose.yml
echo ""

echo "🧪 Test: docker-compose config komutu"
docker-compose config 2>&1
echo ""

echo "🧪 Test: docker-compose -f $(pwd)/docker-compose.yml config"
docker-compose -f "$(pwd)/docker-compose.yml" config 2>&1
echo ""

echo "✅ Debug tamamlandı"





