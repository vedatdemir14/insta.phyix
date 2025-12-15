#!/bin/bash

echo "🔒 HTTPS Kurulumu Başlatılıyor..."

VPS_IP="37.140.242.29"
DOMAIN=""  # Domain'iniz varsa buraya yazın

# Domain kontrolü
if [ -z "$DOMAIN" ]; then
    echo "⚠️ Domain belirtilmedi, IP ile çalışacağız"
    echo "📝 Not: Let's Encrypt için domain gereklidir"
    echo ""
    echo "🌐 HTTP Test URL'leri:"
    echo "   http://${VPS_IP}:8000/health"
    echo "   http://${VPS_IP}:8000/docs"
    echo ""
    echo "🔒 HTTPS için domain gerekli. Domain'iniz varsa:"
    echo "   1. Domain'i VPS IP'ye yönlendirin (A record)"
    echo "   2. Bu script'i domain ile çalıştırın"
    exit 0
fi

echo "📋 Domain: $DOMAIN"
echo ""

# Nginx kurulumu
echo "📦 Nginx kuruluyor..."
apt update
apt install -y nginx certbot python3-certbot-nginx

# Nginx konfigürasyonu
echo "📝 Nginx konfigürasyonu oluşturuluyor..."
cat > /etc/nginx/sites-available/backend << EOF
server {
    listen 80;
    server_name $DOMAIN;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
    }
}
EOF

# Site'ı aktif et
ln -sf /etc/nginx/sites-available/backend /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Nginx'i test et ve yeniden yükle
nginx -t && systemctl reload nginx

# SSL sertifikası
echo "🔒 SSL sertifikası alınıyor..."
certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN

echo "✅ HTTPS kurulumu tamamlandı!"
echo ""
echo "🌐 Test URL'leri:"
echo "   https://$DOMAIN/health"
echo "   https://$DOMAIN/docs"




