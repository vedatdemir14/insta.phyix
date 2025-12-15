#!/bin/bash

echo "📊 Backend Container Logları"
echo "=============================="
echo ""

cd /opt/instagram-scraper

# Tüm logları göster
echo "📋 Son 50 satır log:"
docker compose logs --tail=50 backend

echo ""
echo "=============================="
echo ""

# Environment variable kontrolü
echo "🔍 Environment Variables:"
docker exec instagram-scraper-backend env | grep -E "(SUPABASE|APIFY|OPENROUTER|UNIPILE|DEEPL)" | sort

echo ""
echo "=============================="
echo ""

# Container durumu
echo "📦 Container Durumu:"
docker compose ps

echo ""
echo "=============================="
echo ""

# Health check
echo "🏥 Health Check:"
curl -s http://localhost:8000/health || echo "❌ Health check başarısız"






