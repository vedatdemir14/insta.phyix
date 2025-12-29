#!/bin/bash
# Test Supabase connection and DNS

echo "🔍 Testing internet connectivity..."
ping -c 2 8.8.8.8

echo ""
echo "🔍 Testing DNS with different methods..."

# Try with dig
echo "Testing with dig:"
dig rltkqtlinpsueyaervdv.supabase.co +short || echo "dig failed"

# Try with host
echo ""
echo "Testing with host:"
host rltkqtlinpsueyaervdv.supabase.co || echo "host failed"

# Try with curl (bypasses DNS if IP is known)
echo ""
echo "Testing with curl (direct connection):"
curl -I https://rltkqtlinpsueyaervdv.supabase.co --max-time 5 || echo "curl failed"

# Try to get IP from different DNS servers
echo ""
echo "Testing with Google DNS (8.8.8.8):"
nslookup rltkqtlinpsueyaervdv.supabase.co 8.8.8.8

echo ""
echo "Testing with Cloudflare DNS (1.1.1.1):"
nslookup rltkqtlinpsueyaervdv.supabase.co 1.1.1.1

# Check if domain exists at all
echo ""
echo "Testing generic Supabase domain:"
nslookup supabase.co 8.8.8.8

# Check systemd-resolved status
echo ""
echo "Checking systemd-resolved status:"
resolvectl status

# Try to resolve from container
echo ""
echo "Testing from container:"
cd /opt/instagram-scraper
docker compose exec backend python3 -c "
import socket
try:
    ip = socket.gethostbyname('rltkqtlinpsueyaervdv.supabase.co')
    print(f'✅ DNS resolution successful: {ip}')
except Exception as e:
    print(f'❌ DNS resolution failed: {e}')
"


