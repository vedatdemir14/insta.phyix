#!/bin/bash

echo "🔒 Backend HTTPS Kurulumu Başlatılıyor..."

# 1. SSL dizini oluştur
echo "📁 SSL dizini oluşturuluyor..."
mkdir -p /etc/nginx/ssl

# 2. Self-signed sertifika oluştur
echo "🔐 Self-signed SSL sertifikası oluşturuluyor..."
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/nginx/ssl/backend.key \
    -out /etc/nginx/ssl/backend.crt \
    -subj "/C=TR/ST=Istanbul/L=Istanbul/O=Instagram Scraper/CN=37.140.242.29"

# Dosya izinlerini ayarla
chmod 600 /etc/nginx/ssl/backend.key
chmod 644 /etc/nginx/ssl/backend.crt

# 3. Nginx kurulumu
echo "📦 Nginx kuruluyor..."
apt update
apt install -y nginx

# 4. Nginx yapılandırması oluştur
echo "📝 Nginx yapılandırması oluşturuluyor..."
cat > /etc/nginx/sites-available/instagram-backend << 'EOF'
server {
    listen 443 ssl http2;
    server_name 37.140.242.29;

    ssl_certificate /etc/nginx/ssl/backend.crt;
    ssl_certificate_key /etc/nginx/ssl/backend.key;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # CORS headers
    add_header 'Access-Control-Allow-Origin' '*' always;
    add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS' always;
    add_header 'Access-Control-Allow-Headers' 'Authorization, Content-Type' always;

    # Backend'e proxy
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
        
        # Timeout ayarları
        proxy_connect_timeout 600;
        proxy_send_timeout 600;
        proxy_read_timeout 600;
    }

    # OPTIONS istekleri için
    if ($request_method = 'OPTIONS') {
        return 204;
    }
}

# HTTP'den HTTPS'e yönlendirme
server {
    listen 80;
    server_name 37.140.242.29;
    return 301 https://$server_name$request_uri;
}
EOF

# 5. Symlink oluştur
echo "🔗 Nginx symlink oluşturuluyor..."
ln -sf /etc/nginx/sites-available/instagram-backend /etc/nginx/sites-enabled/

# Default site'ı devre dışı bırak
rm -f /etc/nginx/sites-enabled/default

# 6. Nginx yapılandırmasını test et
echo "🧪 Nginx yapılandırması test ediliyor..."
nginx -t

if [ $? -eq 0 ]; then
    echo "✅ Nginx yapılandırması başarılı!"
    
    # 7. Nginx'i başlat
    echo "🚀 Nginx başlatılıyor..."
    systemctl restart nginx
    systemctl enable nginx
    
    # 8. Firewall ayarları
    echo "🔥 Firewall ayarları yapılıyor..."
    ufw allow 443/tcp
    ufw allow 80/tcp
    ufw reload
    
    echo ""
    echo "✅ HTTPS kurulumu tamamlandı!"
    echo ""
    echo "📋 Sonraki adımlar:"
    echo "1. Vercel Dashboard'da environment variable'ı güncelleyin:"
    echo "   REACT_APP_API_URL = https://37.140.242.29"
    echo ""
    echo "2. Test edin:"
    echo "   curl -k https://37.140.242.29/health"
    echo ""
    echo "⚠️  Not: Self-signed sertifika kullanıyorsunuz."
    echo "   Tarayıcıda 'Advanced' > 'Proceed to site' ile devam edebilirsiniz."
else
    echo "❌ Nginx yapılandırması hatası! Lütfen kontrol edin."
    exit 1
fi






