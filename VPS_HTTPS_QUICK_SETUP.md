# VPS HTTPS Hızlı Kurulum

Backend'inize HTTPS eklemek için VPS'te şu komutları çalıştırın:

## 🚀 Tek Komutla Kurulum

VPS terminalinde (SSH bağlantısında) şu komutları çalıştırın:

```bash
# 1. SSL dizini oluştur
mkdir -p /etc/nginx/ssl

# 2. Self-signed sertifika oluştur
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/nginx/ssl/backend.key \
    -out /etc/nginx/ssl/backend.crt \
    -subj "/C=TR/ST=Istanbul/L=Istanbul/O=Instagram Scraper/CN=37.140.242.29"

# Dosya izinlerini ayarla
chmod 600 /etc/nginx/ssl/backend.key
chmod 644 /etc/nginx/ssl/backend.crt

# 3. Nginx kur
apt update
apt install -y nginx

# 4. Nginx yapılandırması oluştur
cat > /etc/nginx/sites-available/instagram-backend << 'EOF'
server {
    listen 443 ssl http2;
    server_name 37.140.242.29;

    ssl_certificate /etc/nginx/ssl/backend.crt;
    ssl_certificate_key /etc/nginx/ssl/backend.key;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

server {
    listen 80;
    server_name 37.140.242.29;
    return 301 https://$server_name$request_uri;
}
EOF

# 5. Symlink oluştur
ln -sf /etc/nginx/sites-available/instagram-backend /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# 6. Nginx test ve başlat
nginx -t
systemctl restart nginx
systemctl enable nginx

# 7. Firewall
ufw allow 443/tcp
ufw allow 80/tcp
ufw reload
```

## ✅ Test

```bash
# HTTPS test
curl -k https://37.140.242.29/health

# HTTP'den HTTPS'e yönlendirme test
curl -I http://37.140.242.29/health
```

## 🔧 Vercel'de Güncelleme

Vercel Dashboard'da:
1. Projeniz > Settings > Environment Variables
2. `REACT_APP_API_URL` değişkenini bulun
3. Değeri şu şekilde güncelleyin: `https://37.140.242.29`
4. Production, Preview ve Development için güncelleyin
5. Yeni deployment tetikleyin

## ⚠️ Notlar

- Self-signed sertifika kullanıyorsunuz (test için)
- Tarayıcıda "Advanced" > "Proceed to site" ile devam edebilirsiniz
- Production için Let's Encrypt kullanmanız önerilir (domain gerekli)

## 🐛 Sorun Giderme

### Nginx çalışmıyor
```bash
systemctl status nginx
nginx -t
journalctl -u nginx -f
```

### Port çakışması
```bash
netstat -tulpn | grep :443
netstat -tulpn | grep :80
```

### Backend'e erişilemiyor
```bash
# Backend'in çalıştığından emin olun
docker compose ps
curl http://localhost:8000/health
```






