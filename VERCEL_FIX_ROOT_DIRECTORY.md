# Vercel Root Directory Hatası Düzeltme

## Sorun
```
Error: No fastapi entrypoint found...
```

Vercel root directory olarak `frontend` klasörünü değil, proje root'unu seçmiş. Bu yüzden FastAPI backend'i arıyor.

## Çözüm: Vercel Proje Ayarlarını Güncelle

### Adım 1: Vercel Dashboard'a Gidin

1. [Vercel Dashboard](https://vercel.com/dashboard) → Projenize gidin
2. **Settings** sekmesine tıklayın
3. **General** bölümüne gidin

### Adım 2: Root Directory Ayarlayın

1. **Root Directory** bölümünü bulun
2. **Edit** butonuna tıklayın
3. **Root Directory** olarak `frontend` yazın
4. **Save** butonuna tıklayın

### Adım 3: Framework Preset Kontrolü

**General** bölümünde:
- **Framework Preset:** Create React App (otomatik algılanmalı)
- Eğer yanlışsa, **Override** ile **Create React App** seçin

### Adım 4: Build Settings Kontrolü

**Build & Development Settings** bölümünde:
- **Build Command:** `npm run build` (veya `cd frontend && npm run build` eğer root'tan çalışıyorsa)
- **Output Directory:** `build` (veya `frontend/build`)
- **Install Command:** `npm install` (veya `cd frontend && npm install`)

### Adım 5: Yeni Deployment Yapın

1. **Deployments** sekmesine gidin
2. **Redeploy** butonuna tıklayın
3. Veya yeni bir commit push edin

## Alternatif Çözüm: vercel.json'u Root'a Taşı

Eğer root directory'yi değiştiremiyorsanız:

1. `frontend/vercel.json` dosyasını root'a kopyalayın
2. Root'a `package.json` ekleyin (sadece build script için):

```json
{
  "scripts": {
    "build": "cd frontend && npm install && npm run build"
  }
}
```

3. Vercel ayarlarında:
   - **Root Directory:** (boş bırakın veya `.`)
   - **Build Command:** `npm run build`
   - **Output Directory:** `frontend/build`

## Kontrol Listesi

- [ ] Vercel Dashboard → Settings → Root Directory: `frontend`
- [ ] Framework Preset: Create React App
- [ ] Build Command: `npm run build`
- [ ] Output Directory: `build`
- [ ] Environment Variable: `REACT_APP_API_URL=http://2.59.119.90:8000`
- [ ] Yeni deployment yapıldı

## Test

Deployment tamamlandıktan sonra:
- Frontend URL'ine gidin
- Browser console'da hata olmamalı
- API istekleri `/api/*` üzerinden çalışmalı




