# VPS Backend HTTPS Kurulumu

Backend'inize HTTPS eklemek için Nginx reverse proxy kullanacağız.

## Seçenek 1: Let's Encrypt ile Ücretsiz SSL (Önerilen)

### Adım 1: Certbot Kurulumu

```bash
# VPS'e bağlan
ssh root@37.140.242.29

# Certbot kur
apt update
apt install -y certbot python3-certbot-nginx

# Domain'iniz varsa (örn: api.yourdomain.com)
certbot --nginx -d api.yourdomain.com

# Sadece IP için self-signed sertifika (test için)
# Aşağıdaki Seçenek 2'ye bakın
```

### Adım 2: Nginx Kurulumu ve Yapılandırma

```bash
# Nginx kur
apt install -y nginx

# Nginx yapılandırma dosyası oluştur
cat > /etc/nginx/sites-available/instagram-backend << 'EOF'
server {
    listen 443 ssl http2;
    server_name 37.140.242.29;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

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

# Symlink oluştur
ln -s /etc/nginx/sites-available/instagram-backend /etc/nginx/sites-enabled/

# Nginx test et
nginx -t

# Nginx'i başlat
systemctl restart nginx
systemctl enable nginx
```

## Seçenek 2: Self-Signed Sertifika (Test için)

### Adım 1: Self-Signed Sertifika Oluştur

```bash
# SSL dizini oluştur
mkdir -p /etc/nginx/ssl

# Self-signed sertifika oluştur
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/nginx/ssl/backend.key \
    -out /etc/nginx/ssl/backend.crt \
    -subj "/C=TR/ST=Istanbul/L=Istanbul/O=Instagram Scraper/CN=37.140.242.29"
```

### Adım 2: Nginx Yapılandırması

```bash
# Nginx kur
apt install -y nginx

# Nginx yapılandırma dosyası oluştur
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

# Symlink oluştur
ln -s /etc/nginx/sites-available/instagram-backend /etc/nginx/sites-enabled/

# Default site'ı devre dışı bırak
rm /etc/nginx/sites-enabled/default

# Nginx test et
nginx -t

# Nginx'i başlat
systemctl restart nginx
systemctl enable nginx
```

### Adım 3: Firewall Ayarları

```bash
# Port 443'ü aç
ufw allow 443/tcp
ufw allow 80/tcp
ufw reload
```

### Adım 4: Frontend'de URL Güncelleme

Vercel Dashboard'da environment variable'ı güncelleyin:

```
REACT_APP_API_URL = https://37.140.242.29
```

**Not:** Self-signed sertifika kullanıyorsanız, tarayıcı uyarı verecek. "Advanced" > "Proceed to site" ile devam edebilirsiniz.

## Docker Compose ile Nginx

Alternatif olarak, Docker Compose'a Nginx servisi ekleyebilirsiniz:

```yaml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "443:443"
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - backend
    restart: unless-stopped

  backend:
    # ... mevcut backend ayarları
```

## Sorun Giderme

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

### SSL sertifika hatası
- Sertifika yolunu kontrol edin
- Dosya izinlerini kontrol edin: `chmod 600 /etc/nginx/ssl/*.key`






