# Docker Build Sorun Giderme Rehberi

## Yaygın Hatalar ve Çözümleri

### 1. ❌ "Cannot find package.json" hatası

**Çözüm:** 
```bash
# Önce proje dizininde olduğunuzdan emin olun
cd "c:\Users\vedat\OneDrive\Masaüstü\Yeni klasör"

# Frontend Dockerfile'ı kontrol edin
```

### 2. ❌ "npm ci failed" hatası

**Çözüm:** 
`npm ci` yerine `npm install` kullanın. Dockerfile güncellendi.

### 3. ❌ "Docker Desktop is not running" hatası

**Çözüm:**
1. Docker Desktop'ı açın
2. "Docker Desktop is running" mesajını bekleyin
3. Terminal'de test edin:
   ```bash
   docker ps
   ```

### 4. ❌ Backend build hatası - "Module not found"

**Çözüm:**
- `backend.py` dosyasının mevcut olduğundan emin olun
- `requirements.txt` dosyasını kontrol edin

### 5. ❌ Frontend build hatası - "Cannot find module"

**Çözüm:**
- `frontend/package.json` dosyasının mevcut olduğundan emin olun
- Build context'in doğru olduğundan emin olun (proje root'unda olmalısınız)

### 6. ❌ Port çakışması hatası

**Çözüm:**
```bash
# Port'u kullanan process'i bul
netstat -ano | findstr :8000
netstat -ano | findstr :80

# Gerekirse docker-compose.yml'de port'u değiştirin
```

## Adım Adım Build Kontrol Listesi

### Backend Build:
```bash
# 1. Proje dizininde olduğunuzdan emin olun
pwd

# 2. Gerekli dosyaların olduğunu kontrol edin
dir Dockerfile.backend
dir requirements.txt
dir api.py
dir backend.py

# 3. Build'i çalıştırın
docker build -f Dockerfile.backend -t vedatdemir14/instagram-scraper-backend:latest .

# 4. Hata mesajını tam olarak kopyalayın
```

### Frontend Build:
```bash
# 1. Proje dizininde olduğunuzdan emin olun
pwd

# 2. Gerekli dosyaların olduğunu kontrol edin
dir Dockerfile.frontend
dir frontend\package.json
dir nginx-frontend.conf

# 3. Build'i çalıştırın
docker build -f Dockerfile.frontend -t vedatdemir14/instagram-scraper-frontend:latest .

# 4. Hata mesajını tam olarak kopyalayın
```

## Manuel Build Testleri

### Test 1: Docker çalışıyor mu?
```bash
docker --version
docker ps
```

### Test 2: Dosyalar doğru yerde mi?
```bash
# Backend dosyaları
dir api.py backend.py requirements.txt

# Frontend dosyaları  
dir frontend\package.json
dir frontend\src
```

### Test 3: Minimal Build Test
```bash
# Sadece backend'i test edin
docker build -f Dockerfile.backend -t test-backend:latest . --no-cache
```

## Yardım İçin Gerekli Bilgiler

Bir hata aldığınızda şu bilgileri paylaşın:

1. **Tam hata mesajı** (terminal çıktısının tamamı)
2. **Hangi adımda hata aldınız?** (Backend build mi, Frontend build mi?)
3. **Docker Desktop çalışıyor mu?** (`docker ps` komutunun çıktısı)
4. **Proje dizininde misiniz?** (`pwd` veya `cd` komutunun çıktısı)

## Hızlı Çözümler

### Her şeyi sıfırdan başlatmak için:
```bash
# Docker cache'i temizle
docker system prune -a

# Yeniden build et
docker build -f Dockerfile.backend -t vedatdemir14/instagram-scraper-backend:latest . --no-cache
docker build -f Dockerfile.frontend -t vedatdemir14/instagram-scraper-frontend:latest . --no-cache
```

### Build'i adım adım test etmek için:
```bash
# Backend için her adımı ayrı test edin
docker build -f Dockerfile.backend -t test:latest . --progress=plain
```

