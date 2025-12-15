#!/bin/bash

echo "🔍 Backend Erişim Testi..."

VPS_IP="2.59.119.90"
PORT="8000"

echo "📡 Backend URL: http://${VPS_IP}:${PORT}"
echo ""

# 1. Localhost testi
echo "🧪 Localhost Testi:"
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://localhost:${PORT}/health || echo "❌ Localhost'tan erişilemiyor"
echo ""

# 2. VPS IP'den test
echo "🧪 VPS IP'den Test (127.0.0.1):"
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://127.0.0.1:${PORT}/health || echo "❌ 127.0.0.1'den erişilemiyor"
echo ""

# 3. Dışarıdan test (Vercel'in göreceği gibi)
echo "🧪 Dışarıdan Test (Vercel'in göreceği gibi):"
curl -v http://${VPS_IP}:${PORT}/health 2>&1 | head -20
echo ""

# 4. Port dinleme kontrolü
echo "🔌 Port Dinleme Kontrolü:"
ss -tuln | grep :${PORT} || netstat -tuln 2>/dev/null | grep :${PORT} || echo "Port dinlenmiyor"
echo ""

# 5. Container durumu
echo "🐳 Container Durumu:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep backend || echo "Container çalışmıyor"
echo ""

# 6. Firewall kontrolü
echo "🔥 Firewall Kontrolü:"
ufw status | grep ${PORT} || echo "Port ${PORT} UFW'de açık değil"
echo ""

# 7. Auth endpoint testi
echo "🔐 Auth Endpoint Testi:"
curl -X POST http://${VPS_IP}:${PORT}/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test"}' \
  -v 2>&1 | head -20
echo ""

echo "✅ Test tamamlandı!"




