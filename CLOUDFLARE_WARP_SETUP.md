# Cloudflare WARP + Zero Trust Kurulum Rehberi

## 📋 Genel Bakış

Instagram scraping için Cloudflare WARP kullanarak IP ban'larını bypass etmek için Cloudflare Zero Trust hesabı ve WARP client kurulumu gereklidir.

## 🔧 Cloudflare'de Yapılacaklar

### 1. Cloudflare Zero Trust Hesabı Oluşturma

1. **Cloudflare Zero Trust'a gidin:**
   - https://one.dash.cloudflare.com/ adresine gidin
   - Veya https://dash.cloudflare.com/ → "Zero Trust" sekmesine tıklayın

2. **Hesap oluşturun:**
   - "Sign up" veya "Get started" butonuna tıklayın
   - Email ile kayıt olun (ücretsiz plan mevcut)
   - Email doğrulaması yapın

3. **Organizasyon adı verin:**
   - Organizasyon adı girin (örn: "Instagram Scraper")
   - "Continue" butonuna tıklayın

### 2. WARP Client Kurulumu (VPS'te)

WARP client zaten Dockerfile'a eklendi, ancak VPS'te manuel kurulum için:

```bash
# Ubuntu/Debian için
curl -fsSL https://pkg.cloudflareclient.com/pubkey.gpg | sudo gpg --dearmor -o /usr/share/keyrings/cloudflare-warp-archive-keyring.gpg
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/cloudflare-warp-archive-keyring.gpg] https://pkg.cloudflareclient.com/ $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/cloudflare-client.list
sudo apt-get update
sudo apt-get install -y cloudflare-warp
```

### 3. WARP Kayıt ve Bağlantı

#### Seçenek A: WARP Free Mode (Önerilen - Basit)

WARP'ı ücretsiz modda kullanabilirsiniz (Zero Trust hesabı gerekmez):

```bash
# WARP'ı kaydet (ilk kurulum)
warp-cli register

# WARP'ı bağla
warp-cli connect

# Durumu kontrol et
warp-cli status
```

**Avantajlar:**
- ✅ Ücretsiz
- ✅ Hızlı kurulum
- ✅ IP değişimi sağlar
- ✅ SOCKS5 proxy: `127.0.0.1:40000`

**Dezavantajlar:**
- ⚠️ Cloudflare IP'leri kullanır (Instagram tarafından tespit edilebilir)
- ⚠️ Rate limiting olabilir

#### Seçenek B: Zero Trust Teams (Daha Güvenli)

Zero Trust Teams hesabı ile daha gelişmiş özellikler:

1. **Zero Trust Dashboard'a gidin:**
   - https://one.dash.cloudflare.com/ → "Networks" → "WARP Clients"

2. **WARP Client ekleyin:**
   - "Add a device" butonuna tıklayın
   - Device adı verin (örn: "VPS-Server")
   - "Create" butonuna tıklayın

3. **WARP Key alın:**
   - Oluşturulan device'ın yanındaki "..." menüsüne tıklayın
   - "Copy enrollment key" seçeneğini seçin
   - Key'i kopyalayın

4. **VPS'te WARP'ı kaydedin:**
   ```bash
   # Zero Trust Teams key ile kaydet
   warp-cli register --team-token YOUR_ENROLLMENT_KEY
   
   # WARP'ı bağla
   warp-cli connect
   
   # Durumu kontrol et
   warp-cli status
   ```

**Avantajlar:**
- ✅ Daha güvenli
- ✅ Policy kontrolü
- ✅ Log yönetimi
- ✅ Daha iyi IP rotasyonu

**Dezavantajlar:**
- ⚠️ Ücretsiz plan limitleri var
- ⚠️ Daha karmaşık kurulum

### 4. WARP Mode Ayarları

WARP'ın çalışma modunu ayarlayabilirsiniz:

```bash
# WARP mode'u kontrol et
warp-cli settings

# Mode seçenekleri:
# - warp (default): Tüm trafik WARP üzerinden
# - warp+doh: WARP + DNS over HTTPS
# - doh: Sadece DNS over HTTPS (proxy yok)

# Proxy mode için (scraping için gerekli):
warp-cli set-mode warp
```

### 5. SOCKS5 Proxy Ayarları

WARP SOCKS5 proxy'sini kontrol edin:

```bash
# Proxy durumunu kontrol et
warp-cli get-mode

# Proxy portunu kontrol et (varsayılan: 40000)
# Chrome driver zaten bu portu kullanıyor: socks5://127.0.0.1:40000
```

### 6. Zero Trust Teams Policy Ayarları (Opsiyonel)

Eğer Zero Trust Teams kullanıyorsanız:

1. **Policy oluşturun:**
   - Zero Trust Dashboard → "Policies" → "Gateway"
   - "Add a policy" butonuna tıklayın
   - Policy adı: "Instagram Scraping"
   - Action: "Allow"
   - Destination: `instagram.com`, `*.instagram.com`

2. **Device Groups (Opsiyonel):**
   - "My Team" → "Devices" → "Device Groups"
   - VPS'inizi bir grup'a ekleyin
   - Policy'yi bu gruba uygulayın

## 🐳 Docker Container İçinde WARP

### Container'a WARP Kurulumu

Container içinde WARP'ı başlatmak için:

```bash
# Container'a gir
docker exec -it instagram-scraper-backend bash

# WARP'ı kaydet (ilk kurulum)
warp-cli register

# Veya Zero Trust Teams key ile:
# warp-cli register --team-token YOUR_ENROLLMENT_KEY

# WARP'ı bağla
warp-cli connect

# Durumu kontrol et
warp-cli status
```

### Container Restart Sonrası

Container restart olduğunda WARP bağlantısı kopar. Otomatik bağlanması için:

1. **Init script kullanın** (zaten eklendi: `warp-init.sh`)
2. **Veya docker-compose.yml'de command ekleyin:**

```yaml
services:
  backend:
    # ... diğer ayarlar
    command: >
      sh -c "
        warp-cli register || true &&
        warp-cli connect &&
        uvicorn api:app --host 0.0.0.0 --port 8000
      "
```

## 🔍 WARP Durum Kontrolü

### WARP Bağlantı Durumu

```bash
# Durum kontrolü
warp-cli status

# Beklenen çıktı:
# Status update: Connected
# Success

# Veya:
# Status update: Disconnected
# Error: ...
```

### IP Değişimi Kontrolü

```bash
# WARP olmadan IP
curl https://api.ipify.org

# WARP ile IP (proxy üzerinden)
curl --socks5 127.0.0.1:40000 https://api.ipify.org

# IP'ler farklı olmalı
```

## ⚙️ Backend'de WARP Kullanımı

Backend kodunda WARP zaten entegre edildi:

1. **Frontend'den `use_warp: true` gönderildiğinde:**
   - Backend `_ensure_warp_running()` fonksiyonunu çağırır
   - WARP bağlı değilse bağlanmaya çalışır
   - Chrome driver WARP proxy ile başlatılır: `socks5://127.0.0.1:40000`

2. **WARP bağlantısı başarısız olursa:**
   - Sistem otomatik olarak direkt bağlantıya geçer
   - Kullanıcıya uyarı gösterilir

## 🚨 Sorun Giderme

### WARP Bağlanmıyor

```bash
# WARP servisini kontrol et
systemctl status warp-svc

# WARP servisini başlat
systemctl start warp-svc

# WARP'ı yeniden başlat
warp-cli disconnect
warp-cli connect
```

### SOCKS5 Proxy Çalışmıyor

```bash
# Proxy portunu kontrol et
netstat -tuln | grep 40000

# WARP mode'u kontrol et
warp-cli get-mode

# Proxy mode'a geç
warp-cli set-mode warp
```

### Docker Container İçinde WARP Çalışmıyor

```bash
# Container'ı privileged mode'da çalıştır (docker-compose.yml)
services:
  backend:
    privileged: true  # WARP için gerekli olabilir

# Veya host network kullan
services:
  backend:
    network_mode: "host"
```

## 📝 Özet Checklist

- [ ] Cloudflare Zero Trust hesabı oluştur (opsiyonel, free mode için gerekmez)
- [ ] VPS'te WARP client kurulumu (Dockerfile'da zaten var)
- [ ] WARP'ı kaydet: `warp-cli register`
- [ ] WARP'ı bağla: `warp-cli connect`
- [ ] Durumu kontrol et: `warp-cli status`
- [ ] IP değişimini test et
- [ ] Backend'i test et (frontend'den `use_warp: true` ile)

## 🔗 Yararlı Linkler

- Cloudflare Zero Trust: https://one.dash.cloudflare.com/
- WARP Client Docs: https://developers.cloudflare.com/warp-client/
- WARP Linux Installation: https://pkg.cloudflareclient.com/

## 💡 İpuçları

1. **Free Mode yeterli:** Instagram scraping için WARP free mode genellikle yeterlidir
2. **IP rotasyonu:** WARP IP'leri düzenli olarak değişir
3. **Rate limiting:** Instagram'dan rate limit alırsanız, WARP IP'leri değiştiği için sorun çözülebilir
4. **Monitoring:** Zero Trust Teams ile WARP kullanımını izleyebilirsiniz
5. **Backup plan:** WARP çalışmazsa sistem otomatik olarak direkt bağlantıya geçer





