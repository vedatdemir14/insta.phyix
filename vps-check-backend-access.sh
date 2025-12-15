#!/bin/bash

echo "🔍 Backend erişilebilirlik kontrolü..."

VPS_IP="37.140.242.29"
BACKEND_PORT="8000"

echo "📡 Backend URL: http://${VPS_IP}:${BACKEND_PORT}"
echo ""

# Health check
echo "🏥 Health check testi:"
curl -v http://${VPS_IP}:${BACKEND_PORT}/health 2>&1 | head -20
echo ""

# Port kontrolü
echo "🔌 Port kontrolü:"
netstat -tuln | grep :${BACKEND_PORT} || ss -tuln | grep :${BACKEND_PORT}
echo ""

# Firewall kontrolü
echo "🔥 Firewall kontrolü:"
if command -v ufw &> /dev/null; then
    ufw status | grep ${BACKEND_PORT} || echo "UFW aktif ama port açık değil"
elif command -v firewall-cmd &> /dev/null; then
    firewall-cmd --list-ports | grep ${BACKEND_PORT} || echo "Firewalld aktif ama port açık değil"
else
    echo "Firewall yönetim aracı bulunamadı"
fi
echo ""

# Docker container port mapping kontrolü
echo "🐳 Docker container port mapping:"
docker ps --format "table {{.Names}}\t{{.Ports}}" | grep backend
echo ""

echo "✅ Kontrol tamamlandı"
echo ""
echo "📝 Eğer port açık değilse:"
echo "   sudo ufw allow ${BACKEND_PORT}/tcp"
echo "   veya"
echo "   sudo firewall-cmd --add-port=${BACKEND_PORT}/tcp --permanent"
echo "   sudo firewall-cmd --reload"




