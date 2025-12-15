#!/bin/bash
# VPS Supabase Connection Check Script

echo "🔍 Checking Supabase connection setup..."
echo ""

# Check if container is running
echo "1️⃣ Checking container status..."
docker ps | grep instagram-scraper-backend

echo ""
echo "2️⃣ Checking environment variables in container..."
docker exec instagram-scraper-backend env | grep -E "SUPABASE|DATABASE"

echo ""
echo "3️⃣ Checking container logs for Supabase connection..."
docker logs instagram-scraper-backend 2>&1 | grep -i -E "supabase|database|connected|DNS" | tail -20

echo ""
echo "4️⃣ Testing DNS resolution from container..."
docker exec instagram-scraper-backend nslookup rltkqtlinpsueyaervdv.supabase.co || echo "nslookup not available, trying ping..."
docker exec instagram-scraper-backend ping -c 2 rltkqtlinpsueyaervdv.supabase.co || echo "Ping test completed"

echo ""
echo "5️⃣ Checking .env file in project directory..."
if [ -f "/opt/instagram-scraper/.env" ]; then
    echo "✅ .env file exists"
    echo "📋 SUPABASE variables:"
    grep -E "SUPABASE" /opt/instagram-scraper/.env
else
    echo "❌ .env file not found at /opt/instagram-scraper/.env"
fi

echo ""
echo "✅ Check completed!"
echo ""
echo "📝 To fix:"
echo "   1. Make sure .env file has correct SUPABASE_URL and SUPABASE_API_KEY"
echo "   2. Restart container: docker compose restart backend"
echo "   3. Check logs: docker compose logs -f backend"

