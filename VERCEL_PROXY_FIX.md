# Vercel Proxy 502 Hatası Düzeltme

## Durum
- ✅ Backend dışarıdan erişilebilir: `http://2.59.119.90:8000/health` çalışıyor
- ❌ Vercel proxy 502 hatası veriyor

## Sorun
Vercel'in `/api/*` proxy'si backend'e ulaşamıyor veya yanlış yapılandırılmış.

## Çözüm 1: vercel.json Kontrolü

`frontend/vercel.json` dosyasını kontrol edin:

```json
{
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "http://2.59.119.90:8000/:path*"
    },
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ]
}
```

**Önemli:** 
- `destination` URL'si `http://` ile başlamalı (HTTPS değil)
- IP adresi doğru olmalı: `2.59.119.90`
- Port belirtilmeli: `:8000`

## Çözüm 2: Vercel Proxy Testi

Vercel deployment URL'inizden test edin:

```
https://your-app.vercel.app/api/health
```

**Beklenen:** Backend health check response'u

**Eğer hala 502 alıyorsanız:**
- Vercel'in backend'e erişirken bir sorun var
- Vercel'in IP'leri backend firewall'unda engellenmiş olabilir

## Çözüm 3: CORS Ayarları

Backend'de (`api.py`) CORS ayarlarını kontrol edin:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://instagramphyix-*.vercel.app",
        "https://*.vercel.app",
        "*"  # Geçici olarak tüm origin'lere izin
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Çözüm 4: Vercel Environment Variable Kullan

Frontend'de direkt backend URL'ini kullanmak yerine, Vercel proxy kullanıldığından emin olun.

`frontend/src/services/api.ts` dosyasında:

```typescript
const getApiBaseUrl = () => {
  // Vercel'de her zaman /api proxy kullan
  if (typeof window !== 'undefined' && window.location.hostname.includes('vercel.app')) {
    return '/api'; // Vercel proxy kullan
  }
  // Local development için
  return process.env.REACT_APP_API_URL || 'http://localhost:8000';
};
```

Bu zaten doğru görünüyor.

## Çözüm 5: Vercel Deployment'ı Yeniden Yap

1. Vercel Dashboard → Deployments
2. Son deployment'ın yanındaki "..." menüsüne tıklayın
3. **Redeploy** seçin
4. Veya yeni bir commit push edin

## Çözüm 6: Backend Loglarını Kontrol Et

VPS'te backend loglarını kontrol edin:

```bash
cd /opt/instagram-scraper
docker compose logs -f backend
```

Login isteği geldiğinde loglarda ne görünüyor?

## Test Komutları

### Tarayıcı Console'da Test

```javascript
// Vercel proxy üzerinden test
fetch('/api/health')
  .then(r => r.json())
  .then(console.log)
  .catch(console.error)

// Direkt backend test
fetch('http://2.59.119.90:8000/health')
  .then(r => r.json())
  .then(console.log)
  .catch(console.error)
```

### cURL ile Test

```bash
# Vercel proxy test (Vercel URL'inizden)
curl https://your-app.vercel.app/api/health

# Direkt backend test
curl http://2.59.119.90:8000/health
```

## Muhtemel Sorunlar

1. **Vercel proxy timeout:** Backend yavaş yanıt veriyor olabilir
2. **Vercel IP'leri engellenmiş:** Backend firewall'u Vercel IP'lerini engelliyor olabilir
3. **vercel.json yanlış:** Destination URL yanlış yapılandırılmış
4. **CORS sorunu:** Backend CORS ayarları Vercel domain'ini içermiyor

## Hızlı Düzeltme

1. `frontend/vercel.json` dosyasını kontrol edin (yukarıdaki gibi olmalı)
2. GitHub'a push edin
3. Vercel'de yeni deployment yapın
4. Backend loglarını izleyin: `docker compose logs -f backend`
5. Tarayıcı console'da network tab'ı kontrol edin




