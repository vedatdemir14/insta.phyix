# CORS Duplicate Header Hatası Düzeltme

## Sorun
```
The 'Access-Control-Allow-Origin' header contains multiple values 
'https://instagramphyix-1siicbjp8-vedats-projects-18cba7b3.vercel.app, *'
```

Hem Nginx hem de FastAPI CORS header'ları gönderiyor.

## Çözüm

### 1. Nginx'teki CORS Header'larını Kaldır

VPS'te şu komutu çalıştırın:

```bash
# Nginx yapılandırmasını güncelle
cat > /etc/nginx/sites-available/instagram-backend << 'EOF'
server {
    listen 443 ssl http2;
    server_name 2.59.119.90;

    ssl_certificate /etc/nginx/ssl/backend.crt;
    ssl_certificate_key /etc/nginx/ssl/backend.key;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # CORS header'larını kaldırdık - FastAPI zaten gönderiyor

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
```

### 2. Backend CORS Ayarlarını Güncelle

`api.py` dosyasında CORS ayarlarını güncelledim. Backend container'ını yeniden başlatın:

```bash
cd /opt/instagram-scraper
docker compose restart backend
```

Veya backend image'ını yeniden build edip push edin.

## Test

1. Nginx'i yeniden yükleyin
2. Backend container'ını yeniden başlatın
3. Tarayıcıda login'i tekrar deneyin

## Not

Artık sadece FastAPI CORS header'larını gönderecek, duplicate header hatası çözülmeli.





