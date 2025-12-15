# Docker Deployment Guide

Bu dokümanda projeyi Docker ile build edip VPS'e kurulum yapma adımları anlatılmaktadır.

## Gereksinimler

1. Docker Desktop (veya Linux'ta Docker Engine)
2. Docker Hub hesabı (vedatdemir14)
3. VPS erişim bilgileri

## Adım 1: Docker Image'larını Build Etme

### Windows PowerShell:
```powershell
# Build script'ini çalıştır
.\build-and-push.sh
```

### Manuel Build:
```bash
# Backend image build
docker build -f Dockerfile.backend -t vedatdemir14/instagram-scraper-backend:latest .

# Frontend image build
docker build -f Dockerfile.frontend -t vedatdemir14/instagram-scraper-frontend:latest .
```

## Adım 2: Docker Hub'a Push Etme

### Build script ile otomatik:
```bash
./build-and-push.sh
```

### Manuel push:
```bash
# Docker Hub'a login
docker login -u vedatdemir14

# Backend push
docker push vedatdemir14/instagram-scraper-backend:latest

# Frontend push
docker push vedatdemir14/instagram-scraper-frontend:latest
```

## Adım 3: VPS'e Deployment

### Otomatik Deployment (sshpass gereklidir):
```bash
# Windows'ta önce sshpass yükleyin veya manuel deployment yapın
./deploy-vps.sh
```

### Manuel Deployment:

1. **VPS'e bağlan:**
   ```bash
   ssh root@37.140.242.29
   # Şifre: C123kyX7oxuYBEVg
   ```

2. **Docker ve Docker Compose yükle:**
   ```bash
   # Docker yükle
   curl -fsSL https://get.docker.com -o get-docker.sh
   sh get-docker.sh
   systemctl start docker
   systemctl enable docker

   # Docker Compose yükle
   curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   chmod +x /usr/local/bin/docker-compose
   ```

3. **Proje dizinini oluştur:**
   ```bash
   mkdir -p /opt/instagram-scraper
   cd /opt/instagram-scraper
   ```

4. **docker-compose.yml oluştur:**
   ```bash
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
   ```

5. **.env dosyası oluştur:**
   ```bash
   cat > .env << 'EOF'
   SUPABASE_URL=https://rltkqtlinpsueyaervdv.supabase.co
   SUPABASE_API_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJsdGtxdGxpbnBzdWV5YWVydmR2Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NzU3NTk4NSwiZXhwIjoyMDczMTUxOTg1fQ.doT1nxL0izQRpCqzAY-StRFrzqRRuRyiKhZDwKfk_fI
   APIFY_API_TOKEN=apify_api_VeivXy54nUuP7jP3zdPStvnY1bdy6P12ohvn
   OPENROUTER_API_KEY=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
   UNIPILE_API_KEY=k8IpFvnp.1H5f5alAgW2gK5M+J4GvW2M1lavbPHdsZfUGXBbEF+U=
   UNIPILE_BASE_URL=https://api21.unipile.com:15121
   DEEPL_API_KEY=721f4e0a-7600-425a-9bd4-7c4282e7770c:fx
   EOF
   ```

6. **Image'ları çek ve başlat:**
   ```bash
   # Image'ları çek
   docker pull vedatdemir14/instagram-scraper-backend:latest
   docker pull vedatdemir14/instagram-scraper-frontend:latest

   # Container'ları başlat
   docker-compose up -d

   # Logları kontrol et
   docker-compose logs -f
   ```

## Erişim

Deployment tamamlandıktan sonra:

- **Frontend:** http://37.140.242.29
- **Backend API:** http://37.140.242.29:8000
- **Health Check:** http://37.140.242.29:8000/health

## Yönetim Komutları

```bash
# Container'ları durdur
docker-compose down

# Container'ları başlat
docker-compose up -d

# Logları görüntüle
docker-compose logs -f

# Container durumunu kontrol et
docker-compose ps

# Image'ları güncelle
docker-compose pull
docker-compose up -d
```

## Sorun Giderme

### Backend container çalışmıyor:
```bash
# Backend loglarını kontrol et
docker logs instagram-scraper-backend

# Container'ı yeniden başlat
docker restart instagram-scraper-backend
```

### Frontend container çalışmıyor:
```bash
# Frontend loglarını kontrol et
docker logs instagram-scraper-frontend

# Container'ı yeniden başlat
docker restart instagram-scraper-frontend
```

### Port çakışması:
Eğer 80 veya 8000 portları kullanılıyorsa, `docker-compose.yml` dosyasında port mapping'i değiştirin.

## Güncelleme

Yeni bir build'den sonra:

```bash
cd /opt/instagram-scraper
docker-compose pull
docker-compose up -d
```

