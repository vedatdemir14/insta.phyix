# Bright Data 3proxy Final Setup

## ✅ Durum
- 3proxy çalışıyor ✅
- Bright Data proxy bağlantısı başarılı ✅
- Türkiye IP'si alınıyor (Istanbul, Turk Telekom) ✅

## 🔧 Backend Container'dan 3proxy'ye Erişim

Backend Docker container'ın VPS host'undaki 3proxy'ye erişmesi için iki seçenek var:

### Seçenek 1: VPS IP'sini Kullan (ÖNERİLEN)

Frontend'de proxy adresi olarak VPS IP'sini kullanın:
```
http://2.59.119.90:3128
```

**Avantaj:** Basit, ekstra config gerekmez
**Dezavantaj:** Dışarıdan erişilebilir (firewall ile korunmalı)

### Seçenek 2: Docker Network Host Mode

`docker-compose.yml`'de backend service'ine `network_mode: host` ekleyin:

```yaml
services:
  backend:
    image: vedatdemir14/instagram-scraper-backend:latest
    network_mode: host  # Host network kullan
    # ports: kaldırılabilir (host mode'da gerek yok)
    environment:
      - SUPABASE_URL=${SUPABASE_URL}
      # ... diğer env'ler
```

**Avantaj:** Container host network'ü kullanır, `localhost:3128` çalışır
**Dezavantaj:** Port mapping değişir, network izolasyonu yok

## 📋 Frontend'de Kullanım

1. **Campaigns** → **Location Scraping**
2. **"Use Custom Proxy (Bright Data, Proxynetic, etc.)"** checkbox'ını işaretleyin
3. Proxy adresini girin:
   ```
   http://2.59.119.90:3128
   ```
4. Scraping'i başlatın

## 🔒 Güvenlik Notu

3proxy şu anda tüm IP'lerden erişilebilir. Sadece backend container'dan erişim için:

```bash
# 3proxy config'e IP kısıtlaması ekle
cat >> /etc/3proxy/3proxy.cfg << 'EOF'
# Sadece localhost ve Docker network'ten erişim
allow 127.0.0.1
allow 172.16.0.0/12
allow 10.0.0.0/8
EOF

systemctl restart 3proxy
```

## 🧪 Test

Backend container içinden test:

```bash
# Container'a gir
docker exec -it instagram-scraper-backend bash

# Test
curl -x http://2.59.119.90:3128 -k https://geo.brdtest.com/welcome.txt?product=resi&method=native
```

## ✅ Özet

1. ✅ 3proxy kuruldu ve çalışıyor
2. ✅ Bright Data bağlantısı başarılı
3. ✅ Frontend'de `http://2.59.119.90:3128` kullanın
4. ⚠️ İsteğe bağlı: Güvenlik için IP kısıtlaması ekleyin

**Hazır! 🎉**

