# Vercel Deployment Rehberi

Bu rehber, Instagram Scraper frontend uygulamasını Vercel'e deploy etmek için adım adım talimatlar içerir.

## Ön Gereksinimler

1. Vercel hesabı (ücretsiz hesap yeterli)
2. GitHub hesabı (veya GitLab/Bitbucket)
3. VPS'te çalışan backend (http://37.140.242.29:8000)

## Deployment Adımları

### 1. GitHub'a Push Edin

```bash
cd frontend
git add .
git commit -m "Prepare for Vercel deployment"
git push origin main
```

### 2. Vercel'e Proje Ekleyin

1. [Vercel Dashboard](https://vercel.com/dashboard) sayfasına gidin
2. "Add New Project" butonuna tıklayın
3. GitHub repository'nizi seçin
4. Root directory olarak `frontend` klasörünü seçin

### 3. Build Ayarları

Vercel otomatik olarak şu ayarları algılayacak:
- **Framework Preset:** Create React App
- **Build Command:** `npm run build`
- **Output Directory:** `build`
- **Install Command:** `npm install`

### 4. Environment Variables Ayarlayın

Vercel Dashboard'da projenizin **Settings > Environment Variables** bölümüne gidin ve şu değişkeni ekleyin:

```
REACT_APP_API_URL = http://37.140.242.29:8000
```

**Önemli:** 
- Environment variable'ı **Production**, **Preview** ve **Development** için ekleyin
- Değişken adı `REACT_APP_API_URL` olmalı (REACT_APP_ ile başlamalı)

### 5. Deploy

1. "Deploy" butonuna tıklayın
2. Vercel otomatik olarak build işlemini başlatacak
3. Build tamamlandıktan sonra size bir URL verecek (örn: `your-app.vercel.app`)

## CORS Ayarları

Backend'inizde CORS ayarlarının Vercel domain'inizi içermesi gerekiyor. Backend'inizde şu ayarları yapın:

```python
# backend.py veya api.py dosyasında
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://your-app.vercel.app",  # Vercel URL'inizi buraya ekleyin
        "https://*.vercel.app",  # Tüm Vercel preview URL'leri için
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Custom Domain (Opsiyonel)

1. Vercel Dashboard'da projenize gidin
2. **Settings > Domains** bölümüne gidin
3. Domain'inizi ekleyin ve DNS ayarlarını yapın

## Environment Variables Güncelleme

Backend URL'inizi değiştirmek isterseniz:

1. Vercel Dashboard > Projeniz > Settings > Environment Variables
2. `REACT_APP_API_URL` değişkenini güncelleyin
3. Yeni bir deployment tetikleyin (otomatik olarak yeni commit'lerde tetiklenir)

## Sorun Giderme

### Build Hatası

- `npm install` hataları: `package-lock.json` dosyasını kontrol edin
- TypeScript hataları: `tsconfig.json` ayarlarını kontrol edin

### API Bağlantı Hatası

- Backend'in çalıştığından emin olun: `curl http://37.140.242.29:8000/health`
- CORS ayarlarını kontrol edin
- Environment variable'ın doğru ayarlandığından emin olun

### 404 Hatası (Routing)

- `vercel.json` dosyasının doğru yapılandırıldığından emin olun
- React Router'ın `BrowserRouter` kullandığından emin olun

## Hızlı Komutlar

```bash
# Local build test
cd frontend
npm install
npm run build

# Vercel CLI ile deploy (opsiyonel)
npm i -g vercel
vercel login
vercel
```

## Destek

Sorun yaşarsanız:
1. Vercel build loglarını kontrol edin
2. Browser console'da hataları kontrol edin
3. Network tab'da API isteklerini kontrol edin

