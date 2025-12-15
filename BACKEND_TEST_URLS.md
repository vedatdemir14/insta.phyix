# Backend Test URL'leri

## 🌐 HTTP Test URL'leri (Şu An Kullanılabilir)

### Health Check
```
http://2.59.119.90:8000/health
```

### API Dokümantasyonu (Swagger UI)
```
http://2.59.119.90:8000/docs
```

### Alternatif API Dokümantasyonu (ReDoc)
```
http://2.59.119.90:8000/redoc
```

### API Root
```
http://2.59.119.90:8000/
```

## 🔒 HTTPS Kurulumu (Domain Gerekli)

HTTPS için domain gereklidir. Domain'iniz varsa:

### Adım 1: Domain'i VPS IP'ye Yönlendirin

DNS ayarlarınızda:
- **Type:** A Record
- **Name:** @ (veya subdomain)
- **Value:** 37.140.242.29
- **TTL:** 3600

### Adım 2: HTTPS Kurulumu

VPS'te şu komutları çalıştırın:

```bash
# Nginx ve Certbot kurulumu
sudo apt update
sudo apt install -y nginx certbot python3-certbot-nginx

# Nginx konfigürasyonu (domain'inizi yazın)
DOMAIN="yourdomain.com"
sudo tee /etc/nginx/sites-available/backend << EOF
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
sudo ln -sf /etc/nginx/sites-available/backend /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx

# SSL sertifikası al
sudo certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email your-email@example.com
```

### Adım 3: HTTPS Test URL'leri

Kurulumdan sonra:
```
https://yourdomain.com/health
https://yourdomain.com/docs
```

## 🧪 Hızlı Test

### Tarayıcıdan Test

1. **Health Check:**
   - URL: `http://37.140.242.29:8000/health`
   - Beklenen: `{"status":"healthy","backend_available":true}`

2. **API Dokümantasyonu:**
   - URL: `http://37.140.242.29:8000/docs`
   - Beklenen: Swagger UI arayüzü

### cURL ile Test

```bash
# Health check
curl http://37.140.242.29:8000/health

# API dokümantasyonu
curl http://37.140.242.29:8000/docs
```

## ⚠️ Önemli Notlar

- **HTTP (Port 8000):** Şu an kullanılabilir (firewall açıksa)
- **HTTPS:** Domain gereklidir, Let's Encrypt ile ücretsiz SSL
- **Port 80/443:** Nginx ile reverse proxy kullanılırsa standart portlar kullanılabilir
- **Firewall:** Port 8000'in açık olduğundan emin olun

## 🔧 Sorun Giderme

### Port 8000'e erişilemiyorsa:
1. Hostingdunyam firewall'unda port 8000'i açın
2. VPS'te: `sudo ufw allow 8000/tcp`
3. Container çalışıyor mu: `docker compose ps`

### HTTPS çalışmıyorsa:
1. Domain DNS ayarlarını kontrol edin
2. Nginx çalışıyor mu: `sudo systemctl status nginx`
3. SSL sertifikası: `sudo certbot certificates`

