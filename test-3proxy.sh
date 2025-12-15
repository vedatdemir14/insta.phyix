#!/bin/bash
# Test 3proxy connection

echo "🧪 Testing 3proxy..."

# Test 1: SSL bypass ile Bright Data test
echo "Test 1: Bright Data test (SSL bypass)..."
curl -x http://localhost:3128 -k -s https://geo.brdtest.com/welcome.txt?product=resi&method=native

echo ""
echo ""

# Test 2: Google test
echo "Test 2: Google test..."
curl -x http://localhost:3128 -s -o /dev/null -w "HTTP Status: %{http_code}\n" https://www.google.com

echo ""
echo ""

# Test 3: Service durumu
echo "Test 3: Service status..."
systemctl status 3proxy --no-pager -l | head -15

echo ""
echo ""

# Test 4: Port kontrolü
echo "Test 4: Port check..."
netstat -tuln | grep 3128 || ss -tuln | grep 3128

echo ""
echo ""

# Test 5: Log kontrolü
echo "Test 5: Recent logs..."
tail -10 /var/log/3proxy/3proxy.log 2>/dev/null || echo "No log file yet"

