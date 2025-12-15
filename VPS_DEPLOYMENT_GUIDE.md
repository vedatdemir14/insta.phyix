# VPS Deployment Guide - Hızlı Başlangıç

## VPS Bilgileri
- **IP Adresi:** 2.59.119.90
- **Kullanıcı:** root
- **Şifre:** Phyix123

## Adım 1: VPS'e Bağlan

PowerShell'de şu komutu çalıştırın:

```powershell
ssh root@2.59.119.90
```

Şifre sorduğunda: `Phyix123` yazın

## Adım 2: Deployment Komutlarını Çalıştır

VPS'e bağlandıktan sonra, `VPS_DEPLOY_COMMANDS.txt` dosyasındaki komutları kopyalayıp yapıştırın.

Veya aşağıdaki komutları tek tek çalıştırın:

### 1. Docker Kurulumu

```bash
# Docker yükle
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
systemctl start docker
systemctl enable docker
rm get-docker.sh
```

### 2. Docker Compose Kurulumu

```bash
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
```

### 3. Docker Image'larını Çek

```bash
docker pull vedatdemir14/instagram-scraper-backend:latest
docker pull vedatdemir14/instagram-scraper-frontend:latest
```

### 4. Proje Dizini Oluştur

```bash
mkdir -p /opt/instagram-scraper
cd /opt/instagram-scraper
```

### 5. docker-compose.yml Oluştur

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
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

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

### 6. .env Dosyası Oluştur

```bash
cat > .env << 'ENVEOF'
SUPABASE_URL=https://rltkqtlinpsueyaervdv.supabase.co
SUPABASE_API_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJsdGtxdGxpbnBzdWV5YWVydmR2Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NzU3NTk4NSwiZXhwIjoyMDczMTUxOTg1fQ.doT1nxL0izQRpCqzAY-StRFrzqRRuRyiKhZDwKfk_fI
APIFY_API_TOKEN=apify_api_VeivXy54nUuP7jP3zdPStvnY1bdy6P12ohvn
OPENROUTER_API_KEY=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
UNIPILE_API_KEY=k8IpFvnp.1H5f5alAgW2gK5M+J4GvW2M1lavbPHdsZfUGXBbEF+U=
UNIPILE_BASE_URL=https://api21.unipile.com:15121
DEEPL_API_KEY=721f4e0a-7600-425a-9bd4-7c4282e7770c:fx
ENVEOF
```

### 7. Container'ları Başlat

```bash
docker-compose up -d
```

### 8. Durumu Kontrol Et

```bash
docker-compose ps
docker-compose logs -f
```

## Adım 3: Uygulamaya Erişim

Deployment tamamlandıktan sonra:

- **Frontend:** http://37.140.242.29
- **Backend API:** http://37.140.242.29:8000
- **Health Check:** http://37.140.242.29:8000/health

## Yönetim Komutları

### Container'ları Durdur
```bash
cd /opt/instagram-scraper
docker-compose down
```

### Container'ları Başlat
```bash
cd /opt/instagram-scraper
docker-compose up -d
```

### Logları Görüntüle
```bash
cd /opt/instagram-scraper
docker-compose logs -f
```

### Image'ları Güncelle
```bash
cd /opt/instagram-scraper
docker-compose pull
docker-compose up -d
```

### Container Durumunu Kontrol Et
```bash
docker ps
docker-compose ps
```

## Sorun Giderme

### Backend container çalışmıyor:
```bash
docker logs instagram-scraper-backend
docker restart instagram-scraper-backend
```

### Frontend container çalışmıyor:
```bash
docker logs instagram-scraper-frontend
docker restart instagram-scraper-frontend
```

### Port çakışması:
Eğer 80 veya 8000 portları kullanılıyorsa, `docker-compose.yml` dosyasında port mapping'i değiştirin.


