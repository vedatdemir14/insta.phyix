# VPS Docker Compose Path Fix

## Sorun
```
no configuration file provided: not found
```

## Çözüm

VPS'te doğru dizine gidin:

```bash
# Doğru dizine git
cd /opt/instagram-scraper

# Docker compose dosyasının var olduğunu kontrol et
ls -la docker-compose.yml

# Eğer yoksa, oluştur
cat > docker-compose.yml << 'EOF'
services:
  backend:
    image: vedatdemir14/instagram-scraper-backend:latest
    container_name: instagram-scraper-backend
    network_mode: host
    env_file:
      - .env
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    image: vedatdemir14/instagram-scraper-frontend:latest
    container_name: instagram-scraper-frontend
    ports:
      - "3000:80"
    depends_on:
      - backend
    restart: unless-stopped
    networks:
      - app-network

networks:
  app-network:
    driver: bridge
EOF

# Container'ları başlat
docker compose up -d

# Logları kontrol et
docker compose logs -f backend
```

## Hızlı Komutlar

```bash
# Dizine git
cd /opt/instagram-scraper

# Durumu kontrol et
docker compose ps

# Logları görüntüle
docker compose logs -f backend

# Yeniden başlat
docker compose restart backend
```


