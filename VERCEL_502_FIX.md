# Vercel 502 Bad Gateway Hatası Düzeltme

## Sorun
```
POST https://instagramphyix-6wux7amjn-vedats-projects-18cba7b3.vercel.app/api/auth/login 502 (Bad Gateway)
```

Vercel frontend'den backend'e ulaşamıyor.

## Kontrol Listesi

### 1. Backend Çalışıyor mu?

VPS'te test edin:

```bash
# VPS'ten
curl http://localhost:8000/health

# Dışarıdan (tarayıcıdan veya başka bir makineden)
curl http://2.59.119.90:8000/health
```

**Beklenen:** `{"status":"healthy","backend_available":true}`

### 2. Port 8000 Dışarıdan Erişilebilir mi?

```bash
# VPS'te port kontrolü
ss -tuln | grep 8000

# Dışarıdan test (tarayıcıdan)
http://2.59.119.90:8000/health
```

**Beklenen:** Port dinleniyor ve dışarıdan erişilebiliyor olmalı

### 3. Hostingdunyam Firewall

Hostingdunyam kontrol panelinde:
- Port 8000'in **yeni IP (2.59.119.90)** için açık olduğundan emin olun
- Destek ekibine yeni IP'yi bildirin ve port 8000'i açmalarını isteyin

### 4. Vercel Proxy Ayarları

`frontend/vercel.json` dosyası doğru mu kontrol edin:

```json
{
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "http://2.59.119.90:8000/:path*"
    }
  ]
}
```

**Önemli:** Yeni IP (2.59.119.90) kullanılmalı!

### 5. Backend CORS Ayarları

Backend'de (`api.py`) CORS ayarları Vercel domain'ini içermeli:

```python
allow_origins=[
    "http://localhost:3000",
    "https://instagramphyix-*.vercel.app",
    "https://*.vercel.app",
    "*"  # Geçici olarak tüm origin'lere izin
]
```

## Adım Adım Çözüm

### Adım 1: Backend'i Test Edin

VPS'te:

```bash
cd /opt/instagram-scraper

# Container çalışıyor mu?
docker compose ps

# Logları kontrol et
docker compose logs --tail=20 backend

# Health check
curl http://localhost:8000/health
```

### Adım 2: Dışarıdan Erişimi Test Edin

Tarayıcıdan veya başka bir makineden:

```
http://2.59.119.90:8000/health
http://2.59.119.90:8000/docs
```

**Eğer erişilemiyorsa:**
- Hostingdunyam firewall'unda port 8000'i açın
- VPS'te: `sudo ufw allow 8000/tcp`

### Adım 3: Vercel Proxy'yi Test Edin

Vercel deployment'ınızın URL'inden:

```
https://your-app.vercel.app/api/health
```

**Beklenen:** Backend health check response'u

### Adım 4: Backend CORS'u Güncelleyin

Backend'de (`api.py`) CORS ayarlarını güncelleyin ve container'ı yeniden başlatın:

```bash
# VPS'te
cd /opt/instagram-scraper
docker compose restart backend
```

## Hızlı Test Komutları

```bash
# VPS'te
curl http://localhost:8000/health
curl http://2.59.119.90:8000/health
curl -X POST http://2.59.119.90:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test"}'

# Dışarıdan (tarayıcı console'da)
fetch('http://2.59.119.90:8000/health').then(r => r.json()).then(console.log)
```

## Sorun Giderme

### Backend çalışmıyor:
```bash
cd /opt/instagram-scraper
docker compose restart backend
docker compose logs backend
```

### Port 8000'e erişilemiyor:
1. Hostingdunyam firewall'unda port 8000'i açın
2. VPS'te: `sudo ufw allow 8000/tcp`
3. Container port mapping: `0.0.0.0:8000:8000`

### Vercel proxy çalışmıyor:
1. `frontend/vercel.json` dosyasını kontrol edin
2. Yeni IP (2.59.119.90) kullanıldığından emin olun
3. Vercel'de yeni deployment yapın





