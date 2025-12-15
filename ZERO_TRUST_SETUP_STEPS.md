# Cloudflare Zero Trust - Adım Adım Kurulum

## ✅ Hesap Açtıktan Sonra Yapılacaklar

### 1. Dashboard'a Giriş Yapın

1. https://one.dash.cloudflare.com/ adresine gidin
2. Email ve şifrenizle giriş yapın
3. İlk girişte organizasyon adı istenebilir (örn: "Instagram Scraper")

### 2. WARP Client Ekleme

**WARP Clients menüsünü bulma:**

WARP Clients menüsü farklı yerlerde olabilir:

**Seçenek 1: Sol menüde direkt "WARP Clients" veya "My Team" → "Devices"**
- Sol menüde "WARP Clients" veya "My Team" seçeneğini arayın
- Veya direkt: https://one.dash.cloudflare.com/teams/warp-clients

**Seçenek 2: Settings altında**
- Sol menüden "Settings" → "WARP Clients" veya "Devices"

**Seçenek 3: Ana sayfadan**
- Dashboard ana sayfasında "Add WARP device" veya benzeri bir buton olabilir

**WARP Client ekleme:**

1. **"Add a device" veya "Add WARP device" butonuna tıklayın**
   - Sağ üst köşede veya sayfa ortasında bulunur

3. **Device bilgilerini girin:**
   - **Device name:** Örn: "VPS-Server" veya "Instagram-Scraper-VPS"
   - **Device type:** "Linux" seçin
   - **Enrollment method:** "Manual" seçin (önerilen)

4. **"Create" butonuna tıklayın**

5. **Enrollment Key'i kopyalayın:**
   - Oluşturulan device'ın yanında bir key göreceksiniz
   - **ÖNEMLİ:** Bu key'i kopyalayın ve güvenli bir yere kaydedin
   - Format: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` (UUID formatında)

### 3. VPS'te WARP'ı Kaydetme

VPS'inize SSH ile bağlanın ve şu komutları çalıştırın:

```bash
# Docker container'a gir
docker exec -it instagram-scraper-backend bash

# Zero Trust Teams key ile WARP'ı kaydet
warp-cli register --team-token YOUR_ENROLLMENT_KEY

# Örnek:
# warp-cli register --team-token a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

**Beklenen çıktı:**
```
Success
```

### 4. WARP'ı Bağlama

```bash
# WARP'ı bağla
warp-cli connect

# Beklenen çıktı:
# Success
```

### 5. WARP Durumunu Kontrol Etme

```bash
# Durumu kontrol et
warp-cli status

# Beklenen çıktı:
# Status update: Connected
# Success
```

Eğer "Connected" görüyorsanız, WARP başarıyla bağlandı! ✅

### 6. IP Değişimini Test Etme

WARP'ın çalıştığını doğrulamak için:

```bash
# WARP olmadan IP (container içinden)
curl https://api.ipify.org

# WARP ile IP (proxy üzerinden)
curl --socks5 127.0.0.1:40000 https://api.ipify.org
```

**İki IP farklı olmalı!** Eğer farklıysa, WARP başarıyla çalışıyor demektir.

### 7. Backend'de Test Etme

1. **Frontend'e gidin** (Vercel deployment)
2. **Campaigns sayfasına gidin**
3. **"Use Cloudflare WARP Proxy" checkbox'ının işaretli olduğundan emin olun**
4. **Location scraping başlatın**
5. **Backend loglarını kontrol edin:**

```bash
# Container loglarını izle
docker logs -f instagram-scraper-backend

# Şu mesajları görmelisiniz:
# 🌐 Using Cloudflare WARP proxy (SOCKS5://127.0.0.1:40000)
# ✅ Cloudflare WARP is already connected
```

## 🔧 Opsiyonel: Policy Ayarları

Instagram scraping için özel policy oluşturmak isterseniz:

### Policy Oluşturma

1. **Zero Trust Dashboard → "Policies" → "Gateway"**
2. **"Add a policy" butonuna tıklayın**
3. **Policy ayarları:**
   - **Policy name:** "Instagram Scraping"
   - **Action:** "Allow"
   - **Destination:** 
     - `instagram.com`
     - `*.instagram.com`
     - `*.cdninstagram.com`
   - **Protocol:** "All"
4. **"Save policy" butonuna tıklayın**

**Not:** Policy ayarları opsiyoneldir. WARP çalışması için gerekli değildir.

## 🐳 Container Restart Sonrası

Container restart olduğunda WARP bağlantısı kopar. Otomatik bağlanması için:

### Seçenek 1: Manuel Bağlama (Basit)

Container her restart olduğunda:

```bash
docker exec -it instagram-scraper-backend warp-cli connect
```

### Seçenek 2: Otomatik Bağlama (Önerilen)

`docker-compose.yml` dosyasını güncelleyin:

```yaml
services:
  backend:
    # ... mevcut ayarlar
    command: >
      sh -c "
        warp-cli register --team-token YOUR_ENROLLMENT_KEY || true &&
        warp-cli connect &&
        uvicorn api:app --host 0.0.0.0 --port 8000
      "
```

**Veya** bir init script kullanın (zaten `warp-init.sh` var, güncelleyin):

```bash
# warp-init.sh içine enrollment key ekleyin
warp-cli register --team-token YOUR_ENROLLMENT_KEY || true
warp-cli connect
```

## 🔍 Sorun Giderme

### WARP "Disconnected" Durumunda

```bash
# WARP'ı yeniden bağla
warp-cli disconnect
warp-cli connect

# Durumu kontrol et
warp-cli status
```

### Enrollment Key Hatalı

```bash
# WARP'ı sıfırla
warp-cli clear-keys

# Yeni key ile kaydet
warp-cli register --team-token YOUR_NEW_ENROLLMENT_KEY

# Bağlan
warp-cli connect
```

### SOCKS5 Proxy Çalışmıyor

```bash
# Proxy portunu kontrol et
netstat -tuln | grep 40000

# WARP mode'u kontrol et
warp-cli get-mode

# Proxy mode'a geç (eğer değilse)
warp-cli set-mode warp
```

### Container İçinde WARP Çalışmıyor

```bash
# Container'ı privileged mode'da çalıştır
# docker-compose.yml'de:
services:
  backend:
    privileged: true  # WARP için gerekli olabilir
```

## 📋 Hızlı Kontrol Listesi

- [ ] Zero Trust hesabı açıldı
- [ ] Dashboard'a giriş yapıldı
- [ ] WARP Client eklendi (device oluşturuldu)
- [ ] Enrollment key kopyalandı
- [ ] VPS'te WARP kaydedildi: `warp-cli register --team-token KEY`
- [ ] WARP bağlandı: `warp-cli connect`
- [ ] Durum kontrol edildi: `warp-cli status` → "Connected"
- [ ] IP değişimi test edildi
- [ ] Backend'de test edildi (frontend'den scraping başlatıldı)

## 🎯 Özet

**Zero Trust hesabı açtıktan sonra:**

1. ✅ Dashboard → Networks → WARP Clients
2. ✅ Add a device → Device name ver → Create
3. ✅ Enrollment key'i kopyala
4. ✅ VPS'te: `warp-cli register --team-token KEY`
5. ✅ VPS'te: `warp-cli connect`
6. ✅ Test et: `warp-cli status` → "Connected" olmalı

**Bu kadar!** Artık WARP Zero Trust Teams ile çalışıyor. 🎉

