# 🚀 Hızlı Başlangıç - Docker Deployment

## 1️⃣ Docker Image'larını Build ve Push Et

### Windows PowerShell:
```powershell
# PowerShell script'ini çalıştır
.\build-and-push.ps1
```

### Linux/Mac:
```bash
# Bash script'ini çalıştır
chmod +x build-and-push.sh
./build-and-push.sh
```

Bu komut:
- Backend image'ı build eder
- Frontend image'ı build eder
- Docker Hub'a login olur
- Her iki image'ı push eder

## 2️⃣ VPS'e Deployment

### Manuel Deployment (Önerilen):

1. **VPS'e SSH ile bağlan:**
   ```bash
   ssh root@37.140.242.29
   # Şifre: C123kyX7oxuYBEVg
   ```

2. **Aşağıdaki komutları sırayla çalıştır:**

   ```bash
   # Docker yükle
   curl -fsSL https://get.docker.com -o get-docker.sh
   sh get-docker.sh
   systemctl start docker
   systemctl enable docker
   
   # Docker Compose yükle
   curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   chmod +x /usr/local/bin/docker-compose
   
   # Proje dizini oluştur
   mkdir -p /opt/instagram-scraper
   cd /opt/instagram-scraper
   
   # docker-compose.yml oluştur
   cat > docker-compose.yml << 'EOF'
   version: '3.8'
   
   services:
     backend:
       image: vedatdemir14/instagram-scraper-backend:latest
       container_name: instagram-scraper-backend
       ports:
         - "8000:8000"
       environment:
         - SUPABASE_URL=${SUPABASE_URL}
         - SUPABASE_API_KEY=${SUPABASE_API_KEY}
         - APIFY_API_TOKEN=${APIFY_API_TOKEN}
         - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
         - UNIPILE_API_KEY=${UNIPILE_API_KEY}
         - UNIPILE_BASE_URL=${UNIPILE_BASE_URL}
         - DEEPL_API_KEY=${DEEPL_API_KEY}
       restart: unless-stopped
       networks:
         - app-network
   
     frontend:
       image: vedatdemir14/instagram-scraper-frontend:latest
       container_name: instagram-scraper-frontend
       ports:
         - "80:80"
       depends_on:
         - backend
       restart: unless-stopped
       networks:
         - app-network
   
   networks:
     app-network:
       driver: bridge
   EOF
   
   # .env dosyası oluştur (API key'leri buraya yaz)
   cat > .env << 'EOF'
   SUPABASE_URL=https://rltkqtlinpsueyaervdv.supabase.co
   SUPABASE_API_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJsdGtxdGxpbnBzdWV5YWVydmR2Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NzU3NTk4NSwiZXhwIjoyMDczMTUxOTg1fQ.doT1nxL0izQRpCqzAY-StRFrzqRRuRyiKhZDwKfk_fI
   APIFY_API_TOKEN=apify_api_VeivXy54nUuP7jP3zdPStvnY1bdy6P12ohvn
   OPENROUTER_API_KEY=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
   UNIPILE_API_KEY=k8IpFvnp.1H5f5alAgW2gK5M+J4GvW2M1lavbPHdsZfUGXBbEF+U=
   UNIPILE_BASE_URL=https://api21.unipile.com:15121
   DEEPL_API_KEY=721f4e0a-7600-425a-9bd4-7c4282e7770c:fx
   EOF
   
   # Image'ları çek ve başlat
   docker-compose pull
   docker-compose up -d
   
   # Logları kontrol et
   docker-compose logs -f
   ```

## 3️⃣ Erişim

Deployment tamamlandıktan sonra:

- **Frontend:** http://37.140.242.29
- **Backend API:** http://37.140.242.29:8000
- **Health Check:** http://37.140.242.29:8000/health

## 🔧 Faydalı Komutlar

```bash
# Container durumunu kontrol et
docker-compose ps

# Logları görüntüle
docker-compose logs -f

# Container'ları yeniden başlat
docker-compose restart

# Container'ları durdur
docker-compose down

# Image'ları güncelle ve yeniden başlat
docker-compose pull
docker-compose up -d
```

## ❌ Sorun Giderme

### Container'lar çalışmıyor:
```bash
# Logları kontrol et
docker logs instagram-scraper-backend
docker logs instagram-scraper-frontend

# Container'ları yeniden başlat
docker-compose restart
```

### Port çakışması:
```bash
# 80 veya 8000 portunu kullanan process'i bul
netstat -tulpn | grep :80
netstat -tulpn | grep :8000

# Gerekirse docker-compose.yml'de port'u değiştir
```

