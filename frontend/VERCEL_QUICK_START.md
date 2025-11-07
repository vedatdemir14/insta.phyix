# Vercel Deployment - Hızlı Başlangıç

## 🚀 Hızlı Deployment (5 Dakika)

### Adım 1: GitHub'a Push Edin

```bash
cd frontend
git add .
git commit -m "Prepare for Vercel deployment"
git push origin main
```

### Adım 2: Vercel'e Proje Ekleyin

1. [Vercel Dashboard](https://vercel.com/dashboard) → **Add New Project**
2. GitHub repository'nizi seçin
3. **Root Directory:** `frontend` seçin
4. **Framework Preset:** Create React App (otomatik algılanır)

### Adım 3: Environment Variable Ekleyin

**Settings > Environment Variables** bölümüne gidin ve ekleyin:

```
REACT_APP_API_URL = http://37.140.242.29:8000
```

**Önemli:** Production, Preview ve Development için ekleyin!

### Adım 4: Deploy

**Deploy** butonuna tıklayın. Vercel otomatik olarak:
- ✅ Dependencies yükler (`npm install`)
- ✅ Build yapar (`npm run build`)
- ✅ Deploy eder

### Adım 5: URL'i Alın

Deployment tamamlandıktan sonra size bir URL verilecek:
- Production: `your-app.vercel.app`
- Preview: Her commit için yeni URL

## 🔧 Backend CORS Ayarları

Backend'inizde (`api.py`) CORS ayarları zaten var, ancak Vercel URL'inizi eklemek isteyebilirsiniz:

```python
allow_origins=[
    "http://localhost:3000",
    "https://your-app.vercel.app",  # Vercel URL'inizi buraya ekleyin
    "https://*.vercel.app"  # Tüm Vercel preview URL'leri için
]
```

## 📝 Environment Variables

Vercel Dashboard'da şu environment variable'ı ayarlayın:

| Key | Value |
|-----|-------|
| `REACT_APP_API_URL` | `http://37.140.242.29:8000` |

## ✅ Kontrol Listesi

- [ ] GitHub'a push edildi
- [ ] Vercel'de proje oluşturuldu
- [ ] Root directory: `frontend` seçildi
- [ ] Environment variable eklendi: `REACT_APP_API_URL`
- [ ] Deploy başarılı
- [ ] Frontend backend'e bağlanabiliyor

## 🐛 Sorun Giderme

### Build Hatası
- `package-lock.json` dosyasını kontrol edin
- Vercel build loglarını inceleyin

### API Bağlantı Hatası
- Backend'in çalıştığından emin olun: `curl http://37.140.242.29:8000/health`
- Browser console'da CORS hatalarını kontrol edin
- Environment variable'ın doğru ayarlandığından emin olun

### 404 Hatası (Routing)
- `vercel.json` dosyasının doğru olduğundan emin olun
- React Router'ın `BrowserRouter` kullandığından emin olun

## 📚 Daha Fazla Bilgi

Detaylı rehber için: `VERCEL_DEPLOYMENT.md` dosyasına bakın.

