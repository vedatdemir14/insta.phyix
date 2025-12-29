#!/bin/bash
# Fix DNS resolution on VPS host

echo "🔍 Checking current DNS settings..."
cat /etc/resolv.conf

echo ""
echo "🔍 Testing DNS resolution..."
nslookup rltkqtlinpsueyaervdv.supabase.co

echo ""
echo "🔧 Fixing DNS settings..."

# Backup
cp /etc/resolv.conf /etc/resolv.conf.backup

# Add Google DNS servers
cat > /etc/resolv.conf << 'EOF'
nameserver 8.8.8.8
nameserver 8.8.4.4
nameserver 1.1.1.1
EOF

echo "✅ DNS settings updated"

echo ""
echo "🧪 Testing DNS resolution again..."
nslookup rltkqtlinpsueyaervdv.supabase.co

echo ""
echo "🧪 Testing with dig (if available)..."
dig rltkqtlinpsueyaervdv.supabase.co +short || echo "dig not available"

echo ""
echo "🔄 Restarting Docker containers..."
cd /opt/instagram-scraper
docker compose restart backend

echo ""
echo "⏳ Waiting 10 seconds..."
sleep 10

echo ""
echo "📊 Checking backend logs..."
docker compose logs --tail=30 backend


