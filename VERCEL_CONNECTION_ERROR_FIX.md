# Vercel ROUTER_EXTERNAL_TARGET_CONNECTION_ERROR Düzeltme

## Sorun
```
502: BAD GATEWAY
Code: ROUTER_EXTERNAL_TARGET_CONNECTION_ERROR
```

Vercel'in backend'e (2.59.119.90:8000) bağlanamıyor.

## Olası Nedenler

1. **Backend firewall Vercel IP'lerini engelliyor**
2. **Backend yalnızca belirli IP'lere izin veriyor**
3. **Vercel proxy timeout oluyor**
4. **Backend çok yavaş yanıt veriyor**

## Çözüm 1: Backend Loglarını Kontrol Et

VPS'te backend loglarını izleyin:

```bash
cd /opt/instagram-scraper
docker compose logs -f backend
```

Vercel'den istek geldiğinde loglarda ne görünüyor?
- İstek geliyor mu?
- Hata var mı?
- Timeout oluyor mu?

## Çözüm 2: Backend Firewall Kontrolü

Vercel'in IP'leri backend'e erişebilmeli. Hostingdunyam firewall'unda:
- Port 8000 tüm IP'lere açık olmalı (0.0.0.0/0)
- Vercel IP'leri özel olarak engellenmemeli

## Çözüm 3: Alternatif - Direkt Backend Bağlantısı

Vercel proxy yerine, frontend'in direkt backend'e bağlanmasını sağlayın:

### frontend/src/services/api.ts güncelle:

```typescript
const getApiBaseUrl = () => {
  // Vercel'de direkt backend URL kullan (proxy yerine)
  if (typeof window !== 'undefined' && window.location.hostname.includes('vercel.app')) {
    return 'http://2.59.119.90:8000'; // Direkt backend URL
  }
  // Local development için
  return process.env.REACT_APP_API_URL || 'http://localhost:8000';
};
```

**Not:** Bu durumda CORS ayarlarının doğru olduğundan emin olun.

## Çözüm 4: Backend CORS Güncelleme

Backend'de (`api.py`) CORS ayarlarını güncelleyin:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://instagramphyix-*.vercel.app",
        "https://*.vercel.app",
        "*"  # Tüm origin'lere izin
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Container'ı yeniden başlatın:
```bash
cd /opt/instagram-scraper
docker compose restart backend
```

## Çözüm 5: Vercel Proxy Timeout Artırma

`frontend/vercel.json` dosyasına timeout ekleyin:

```json
{
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "http://2.59.119.90:8000/:path*"
    }
  ],
  "functions": {
    "app/api/**/*.js": {
      "maxDuration": 30
    }
  }
}
```

## Test

### 1. Backend Loglarını İzle

```bash
cd /opt/instagram-scraper
docker compose logs -f backend
```

### 2. Vercel'den Test

Tarayıcı console'da:
```javascript
// Proxy üzerinden
fetch('/api/health').then(r => r.json()).then(console.log)

// Direkt backend
fetch('http://2.59.119.90:8000/health').then(r => r.json()).then(console.log)
```

### 3. cURL ile Test

```bash
# Vercel proxy simülasyonu
curl -v http://2.59.119.90:8000/health
```

## Önerilen Çözüm

**En hızlı çözüm:** Frontend'in direkt backend'e bağlanmasını sağlayın (Çözüm 3). Vercel proxy sorunlu görünüyor.

1. `frontend/src/services/api.ts` dosyasını güncelleyin
2. GitHub'a push edin
3. Vercel'de yeni deployment yapın
4. CORS ayarlarının doğru olduğundan emin olun





