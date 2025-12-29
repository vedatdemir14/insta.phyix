#!/bin/bash

echo "🔒 Backend HTTPS Kurulumu (Hızlı)..."

VPS_IP="2.59.119.90"

# 1. SSL dizini oluştur
echo "📁 SSL dizini oluşturuluyor..."
mkdir -p /etc/nginx/ssl

# 2. Self-signed sertifika oluştur
echo "🔐 Self-signed SSL sertifikası oluşturuluyor..."
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/nginx/ssl/backend.key \
    -out /etc/nginx/ssl/backend.crt \
    -subj "/C=TR/ST=Istanbul/L=Istanbul/O=Instagram Scraper/CN=${VPS_IP}"

chmod 600 /etc/nginx/ssl/backend.key
chmod 644 /etc/nginx/ssl/backend.crt

# 3. Nginx kurulumu
echo "📦 Nginx kuruluyor..."
apt update
apt install -y nginx

# 4. Nginx yapılandırması
echo "📝 Nginx yapılandırması oluşturuluyor..."
cat > /etc/nginx/sites-available/instagram-backend << EOF
server {
    listen 443 ssl http2;
    server_name ${VPS_IP};

    ssl_certificate /etc/nginx/ssl/backend.crt;
    ssl_certificate_key /etc/nginx/ssl/backend.key;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # CORS headers
    add_header 'Access-Control-Allow-Origin' '*' always;
    add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS' always;
    add_header 'Access-Control-Allow-Headers' 'Authorization, Content-Type' always;

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

# HTTP'den HTTPS'e yönlendirme
server {
    listen 80;
    server_name ${VPS_IP};
    return 301 https://\$server_name\$request_uri;
}
EOF

# 5. Site'ı aktif et
echo "🔗 Site aktif ediliyor..."
ln -sf /etc/nginx/sites-available/instagram-backend /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# 6. Nginx test ve başlat
echo "🧪 Nginx test ediliyor..."
nginx -t && systemctl restart nginx && systemctl enable nginx

# 7. Firewall
echo "🔥 Firewall ayarları..."
ufw allow 443/tcp
ufw allow 80/tcp
ufw reload

echo ""
echo "✅ HTTPS kurulumu tamamlandı!"
echo ""
echo "🌐 Test URL'leri:"
echo "   https://${VPS_IP}/health"
echo "   https://${VPS_IP}/docs"
echo ""
echo "⚠️  Not: Self-signed sertifika kullanılıyor. Tarayıcı uyarı verecek."
echo "   'Advanced' > 'Proceed to site' ile devam edebilirsiniz."





