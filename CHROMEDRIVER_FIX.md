# ChromeDriver Kurulumu - Build ve Deploy

Dockerfile'a Chrome ve ChromeDriver eklendi. Şimdi image'ı yeniden build edip push etmeniz gerekiyor.

## 🚀 Adımlar

### 1. Docker Image'ı Build Et ve Push Et

**Windows PowerShell'de:**

```powershell
# Proje root dizinine git
cd "C:\Yeni klasör"

# Build ve push script'ini çalıştır
.\build-and-push.ps1
```

**Veya manuel olarak:**

```powershell
# Docker Hub'a login
docker login -u vedatdemir14

# Backend image'ı build et
docker build -f Dockerfile.backend -t vedatdemir14/instagram-scraper-backend:latest .

# Image'ı push et
docker push vedatdemir14/instagram-scraper-backend:latest
```

### 2. VPS'te Image'ı Güncelle

VPS terminalinde (SSH bağlantısında):

```bash
cd /opt/instagram-scraper

# Mevcut container'ı durdur
docker compose down

# Yeni image'ı çek
docker pull vedatdemir14/instagram-scraper-backend:latest

# Container'ı yeniden başlat
docker compose up -d

# Logları kontrol et
docker compose logs -f backend
```

### 3. ChromeDriver'ı Test Et

```bash
# Container içine gir
docker exec -it instagram-scraper-backend /bin/bash

# Chrome versiyonunu kontrol et
google-chrome --version

# ChromeDriver versiyonunu kontrol et
chromedriver --version

# Python ile test
python3 -c "
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
driver = webdriver.Chrome(options=options)
print('✅ ChromeDriver çalışıyor!')
driver.quit()
"
```

## ✅ Kontrol Listesi

- [ ] Dockerfile.backend güncellendi
- [ ] Docker image build edildi
- [ ] Docker image push edildi
- [ ] VPS'te yeni image çekildi
- [ ] Container yeniden başlatıldı
- [ ] ChromeDriver test edildi

## 🐛 Sorun Giderme

### Build hatası
- Docker'ın yeterli disk alanı olduğundan emin olun
- Build loglarını kontrol edin

### ChromeDriver hatası devam ediyor
- Container loglarını kontrol edin: `docker compose logs backend`
- Chrome ve ChromeDriver versiyonlarını kontrol edin
- webdriver-manager'ın otomatik yüklemesini bekleyin (ilk çalıştırmada)

### Container başlamıyor
- Logları kontrol edin: `docker compose logs backend`
- Disk alanını kontrol edin: `df -h`
- Memory kullanımını kontrol edin: `free -h`






