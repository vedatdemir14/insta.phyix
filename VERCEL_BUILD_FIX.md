# Vercel Build Hatası Düzeltme - FastAPI Hatası

## Sorun
Vercel hala FastAPI backend'i arıyor, React frontend'i build etmiyor.

## Çözüm 1: Root'a vercel.json Ekle (Önerilen)

Proje root'una (frontend klasörünün bir üstü) `vercel.json` dosyası ekleyin:

```json
{
  "buildCommand": "cd frontend && npm install && npm run build",
  "outputDirectory": "frontend/build",
  "framework": null,
  "installCommand": "cd frontend && npm install"
}
```

Bu dosyayı GitHub'a push edin.

## Çözüm 2: Vercel Dashboard'da Build Settings Override

1. Vercel Dashboard → Projeniz → **Settings** → **Build & Development Settings**

2. **Override** butonuna tıklayın ve şunları ayarlayın:
   - **Framework Preset:** Other (veya Create React App)
   - **Build Command:** `cd frontend && npm install && npm run build`
   - **Output Directory:** `frontend/build`
   - **Install Command:** `cd frontend && npm install`

3. **Save** butonuna tıklayın

4. Yeni deployment yapın

## Çözüm 3: Root Directory + Build Settings Kombinasyonu

1. **Settings** → **General** → **Root Directory:** `frontend`

2. **Settings** → **Build & Development Settings**:
   - **Build Command:** `npm run build` (root directory frontend olduğu için direkt çalışır)
   - **Output Directory:** `build`
   - **Install Command:** `npm install`

3. **Framework Preset:** Create React App

4. **Save** ve yeni deployment

## Çözüm 4: GitHub'da .vercelignore Ekle

Proje root'una `.vercelignore` dosyası ekleyin:

```
backend.py
api.py
*.py
requirements.txt
Dockerfile*
docker-compose.yml
__pycache__/
*.pyc
```

Bu, Vercel'in Python dosyalarını görmezden gelmesini sağlar.

## Kontrol Listesi

- [ ] Root directory: `frontend` (veya root'ta vercel.json ile build command)
- [ ] Build Command: `cd frontend && npm run build` veya `npm run build` (root directory frontend ise)
- [ ] Output Directory: `frontend/build` veya `build` (root directory frontend ise)
- [ ] Framework Preset: Create React App veya Other
- [ ] .vercelignore dosyası eklendi (opsiyonel)

## Test

Deployment tamamlandıktan sonra:
- Build loglarında `npm run build` görünmeli
- `Creating an optimized production build...` mesajı görünmeli
- FastAPI hatası görünmemeli





