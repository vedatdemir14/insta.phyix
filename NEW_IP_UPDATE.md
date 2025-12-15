# Yeni IP Adresi Güncelleme: 2.59.119.90

## ✅ Güncellenen Dosyalar

- VPS_DEPLOYMENT_GUIDE.md
- frontend/vercel.json
- BACKEND_TEST_URLS.md

## 🌐 Yeni Test URL'leri

### HTTP Test URL'leri

```
http://2.59.119.90:8000/health
http://2.59.119.90:8000/docs
http://2.59.119.90:8000/redoc
```

### HTTPS Test URL'leri (Nginx kurulumundan sonra)

```
https://2.59.119.90/health
https://2.59.119.90/docs
```

## 🔧 VPS'te Yapılacaklar

### 1. Nginx Konfigürasyonu Güncelleme (HTTPS için)

```bash
# Nginx konfigürasyonunu güncelle
sudo nano /etc/nginx/sites-available/instagram-backend

# server_name satırını güncelle:
# server_name 2.59.119.90;

# Nginx'i yeniden yükle
sudo nginx -t && sudo systemctl reload nginx
```

### 2. SSL Sertifikası (Self-signed için)

```bash
# SSL sertifikasını yeniden oluştur (CN'yi yeni IP ile)
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/nginx/ssl/backend.key \
    -out /etc/nginx/ssl/backend.crt \
    -subj "/C=TR/ST=Istanbul/L=Istanbul/O=Instagram Scraper/CN=2.59.119.90"
```

### 3. Vercel Environment Variable Güncelleme

Vercel Dashboard'da:
1. Projeniz > Settings > Environment Variables
2. `REACT_APP_API_URL` değişkenini güncelleyin:
   - Eski: `http://37.140.242.29:8000`
   - Yeni: `http://2.59.119.90:8000`
3. Yeni deployment yapın

### 4. Hostingdunyam Firewall

Hostingdunyam kontrol panelinde:
- Port 8000'in yeni IP için açık olduğundan emin olun
- Gerekirse destek ekibine yeni IP'yi bildirin

## 🧪 Test

```bash
# VPS'ten test
curl http://localhost:8000/health

# Dışarıdan test
curl http://2.59.119.90:8000/health
```

## 📝 Notlar

- Eski IP: 37.140.242.29
- Yeni IP: 2.59.119.90
- Tüm frontend ve backend konfigürasyonlarını güncelleyin
- Vercel deployment'ını yeniden yapın




