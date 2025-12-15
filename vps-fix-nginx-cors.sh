#!/bin/bash

echo "🔧 Nginx CORS Düzeltmesi..."

# Nginx yapılandırmasını güncelle (CORS header'larını kaldır, FastAPI zaten gönderiyor)
cat > /etc/nginx/sites-available/instagram-backend << 'EOF'
server {
    listen 443 ssl http2;
    server_name 2.59.119.90;

    ssl_certificate /etc/nginx/ssl/backend.crt;
    ssl_certificate_key /etc/nginx/ssl/backend.key;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # CORS header'larını kaldırdık - FastAPI zaten gönderiyor
    # Duplicate header hatası önlemek için

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}

server {
    listen 80;
    server_name 2.59.119.90;
    return 301 https://$server_name$request_uri;
}
EOF

# Nginx'i test et ve yeniden yükle
nginx -t && systemctl reload nginx

echo "✅ Nginx CORS header'ları kaldırıldı"
echo "📝 CORS artık sadece FastAPI'den gelecek"




