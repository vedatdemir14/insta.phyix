# Kullanıcı IP'si ile Instagram Scraping Çözümü

## 🎯 Amaç
VPS'in kullanıcının IP adresini kullanarak Instagram'a bağlanması.

## ❌ Cloudflare WARP Neden Uygun Değil?
- WARP, VPS'in kendi IP'sini değiştirir
- Kullanıcının IP'sini kullanmaz
- Kullanıcının bilgisayarına bağlı değildir

## ✅ Çözüm: SSH SOCKS5 Tunnel

### Nasıl Çalışır?
1. Kullanıcı bilgisayarında SSH tunnel oluşturur
2. Bu tunnel, kullanıcının IP'sini kullanarak VPS'e SOCKS5 proxy sağlar
3. VPS, Selenium'u bu SOCKS5 proxy üzerinden çalıştırır
4. Instagram, kullanıcının IP'sini görür ✅

### Avantajları
- ✅ Kullanıcının gerçek IP'si kullanılır
- ✅ Güvenli (SSH şifreli)
- ✅ Kolay kurulum
- ✅ Ücretsiz

### Dezavantajları
- ⚠️ Kullanıcının bilgisayarı açık olmalı
- ⚠️ SSH bağlantısı aktif olmalı

---

## 📋 Kurulum Adımları

### 1. VPS'te SSH Erişimi Kontrolü

VPS'te SSH'nin çalıştığından emin olun:

```bash
# VPS'te
sudo systemctl status ssh
# veya
sudo systemctl status sshd
```

### 2. Kullanıcı Bilgisayarında SSH Tunnel Oluşturma

**Windows (PowerShell):**

```powershell
# SSH tunnel oluştur (arka planda çalışır)
ssh -N -D 1080 -f root@2.59.119.90

# Kontrol et
netstat -an | findstr 1080
```

**Mac/Linux:**

```bash
# SSH tunnel oluştur (arka planda çalışır)
ssh -N -D 1080 -f root@2.59.119.90

# Kontrol et
lsof -i :1080
```

**Not:** `-N` = komut çalıştırma, sadece tunnel
**Not:** `-D 1080` = SOCKS5 proxy port 1080'de
**Not:** `-f` = arka planda çalıştır

### 3. VPS'te Backend'i Güncelleme

Backend'e `user_proxy` parametresi ekleyeceğiz:

```python
# backend.py'de selenium_location_scraper fonksiyonuna:
user_proxy: Optional[str] = None  # Örn: "socks5://KULLANICI_IP:1080"
```

### 4. Frontend'den Proxy Bilgisi Gönderme

Kullanıcı bilgisayarından VPS'e proxy bilgisi göndermek için:

**Seçenek A: Manuel (Basit)**
- Kullanıcı kendi IP'sini ve proxy port'unu girer
- Frontend bunu backend'e gönderir

**Seçenek B: Otomatik (Gelişmiş)**
- Kullanıcı bilgisayarında bir script çalıştırır
- Script SSH tunnel oluşturur ve proxy bilgisini backend'e gönderir

---

## 🔧 Alternatif Çözümler

### Çözüm 2: Local SOCKS5 Proxy (Daha Basit)

Kullanıcı bilgisayarında bir SOCKS5 proxy çalıştırır:

**Windows:**
```powershell
# 3proxy veya benzeri bir tool kullan
# Veya browser extension (FoxyProxy)
```

**Mac/Linux:**
```bash
# SSH ile local SOCKS5
ssh -D 1080 -N root@2.59.119.90
```

### Çözüm 3: Browser Extension + WebRTC

Kullanıcı bir browser extension kullanarak proxy oluşturur:
- FoxyProxy
- Proxy SwitchyOmega
- Bu extension'lar SOCKS5 proxy sağlar

---

## 🚀 Önerilen Yaklaşım

**En Pratik:** SSH Reverse Tunnel

1. Kullanıcı bilgisayarında SSH tunnel oluşturur
2. Frontend'de "Use My IP" checkbox'ı işaretler
3. Frontend, kullanıcının IP'sini ve proxy port'unu backend'e gönderir
4. Backend, Selenium'u bu proxy üzerinden çalıştırır

**Kod Değişiklikleri:**
- ✅ Backend: `user_proxy` parametresi ekle
- ✅ Frontend: Proxy bilgisi gönderme
- ✅ Dokümantasyon: Kullanıcıya SSH tunnel kurulumu anlat

---

## 📝 Sonraki Adımlar

1. Backend'e `user_proxy` desteği ekle
2. Frontend'e proxy bilgisi girişi ekle
3. Kullanıcı dokümantasyonu hazırla
4. Test et



