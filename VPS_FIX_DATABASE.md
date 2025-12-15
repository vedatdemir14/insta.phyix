# VPS Database Bağlantı Sorunu Çözümü

Backend container'ında Supabase bağlantısı kurulamıyor. Environment variable'ları kontrol edin.

## 🔍 Sorun Tespiti

VPS terminalinde şu komutları çalıştırın:

```bash
# 1. Container environment variable'larını kontrol et
docker exec instagram-scraper-backend env | grep SUPABASE

# 2. .env dosyasını kontrol et
cd /opt/instagram-scraper
cat .env

# 3. Container loglarını kontrol et
docker compose logs backend | grep -i "supabase\|database\|connected"
```

## 🔧 Çözüm 1: Environment Variable'ları Kontrol Et

```bash
cd /opt/instagram-scraper

# .env dosyasını kontrol et
cat .env

# Eğer dosya yoksa veya yanlışsa, yeniden oluştur
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

## 🔧 Çözüm 2: Container'ı Yeniden Başlat

```bash
cd /opt/instagram-scraper

# Container'ı durdur
docker compose down

# Container'ı yeniden başlat
docker compose up -d

# Logları kontrol et
docker compose logs -f backend
```

## 🔧 Çözüm 3: Docker Compose'da Environment Variable'ları Doğrudan Ayarla

`docker-compose.yml` dosyasını kontrol edin:

```bash
cd /opt/instagram-scraper
cat docker-compose.yml
```

Eğer environment variable'lar eksikse, şu şekilde güncelleyin:

```yaml
services:
  backend:
    image: vedatdemir14/instagram-scraper-backend:latest
    container_name: instagram-scraper-backend
    ports:
      - "8000:8000"
    environment:
      - SUPABASE_URL=https://rltkqtlinpsueyaervdv.supabase.co
      - SUPABASE_API_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJsdGtxdGxpbnBzdWV5YWVydmR2Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NzU3NTk4NSwiZXhwIjoyMDczMTUxOTg1fQ.doT1nxL0izQRpCqzAY-StRFrzqRRuRyiKhZDwKfk_fI
      - APIFY_API_TOKEN=apify_api_VeivXy54nUuP7jP3zdPStvnY1bdy6P12ohvn
      - OPENROUTER_API_KEY=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
      - UNIPILE_API_KEY=k8IpFvnp.1H5f5alAgW2gK5M+J4GvW2M1lavbPHdsZfUGXBbEF+U=
      - UNIPILE_BASE_URL=https://api21.unipile.com:15121
      - DEEPL_API_KEY=721f4e0a-7600-425a-9bd4-7c4282e7770c:fx
    restart: unless-stopped
    networks:
      - app-network
```

Sonra container'ı yeniden başlatın:

```bash
docker compose down
docker compose up -d
```

## 🔧 Çözüm 4: Supabase Bağlantısını Test Et

```bash
# Container içine gir
docker exec -it instagram-scraper-backend /bin/bash

# Python ile test et
python3 -c "
from supabase import create_client
import os
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_API_KEY')
print(f'URL: {url}')
print(f'Key: {key[:20]}...' if key else 'Key: None')
if url and key:
    try:
        supabase = create_client(url, key)
        result = supabase.table('scraping_sessions').select('id').limit(1).execute()
        print('✅ Supabase bağlantısı başarılı!')
    except Exception as e:
        print(f'❌ Hata: {e}')
"
```

## ✅ Kontrol Listesi

- [ ] .env dosyası mevcut ve doğru
- [ ] Docker Compose environment variable'ları ayarlı
- [ ] Container yeniden başlatıldı
- [ ] Supabase URL ve API key doğru
- [ ] Container loglarında "Supabase connected" mesajı var

## 🐛 Sorun Devam Ederse

1. Container loglarını detaylı kontrol edin:
```bash
docker compose logs backend | tail -50
```

2. Supabase dashboard'da API key'in aktif olduğundan emin olun

3. Network bağlantısını kontrol edin:
```bash
docker exec instagram-scraper-backend curl -I https://rltkqtlinpsueyaervdv.supabase.co
```






