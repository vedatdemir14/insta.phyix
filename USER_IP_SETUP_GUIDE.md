# Kullanıcı IP'si ile Instagram Scraping Kurulum Rehberi

## 🎯 Amaç
VPS'in **sizin bilgisayarınızın IP adresini** kullanarak Instagram'a bağlanması.

## ✅ Nasıl Çalışır?

1. **Sizin bilgisayarınızda** SSH tunnel oluşturursunuz
2. Bu tunnel, **sizin IP'nizi** kullanarak VPS'e SOCKS5 proxy sağlar
3. VPS, Instagram scraping'i bu proxy üzerinden yapar
4. Instagram, **sizin IP'nizi** görür ✅

---

## 📋 Adım Adım Kurulum

### 1. SSH Tunnel Oluşturma

#### Windows (PowerShell):

```powershell
# SSH tunnel oluştur (arka planda çalışır)
ssh -N -D 1080 -f root@2.59.119.90

# Kontrol et (tunnel çalışıyor mu?)
netstat -an | findstr 1080
```

**Not:** İlk kez bağlanıyorsanız, SSH key'i kabul etmeniz istenebilir. `yes` yazın.

#### Mac/Linux:

```bash
# SSH tunnel oluştur (arka planda çalışır)
ssh -N -D 1080 -f root@2.59.119.90

# Kontrol et (tunnel çalışıyor mu?)
lsof -i :1080
```

**Parametreler:**
- `-N`: Komut çalıştırma, sadece tunnel
- `-D 1080`: SOCKS5 proxy port 1080'de
- `-f`: Arka planda çalıştır

### 2. IP Adresinizi Öğrenme

Frontend'de otomatik olarak tespit edilir, ama manuel kontrol için:

**Windows:**
```powershell
# PowerShell'de
(Invoke-WebRequest -Uri "https://api.ipify.org").Content
```

**Mac/Linux:**
```bash
curl https://api.ipify.org
```

### 3. Frontend'de Proxy Bilgisi Girme

1. **Campaigns** sayfasına gidin
2. **Location Scraping** tab'ını seçin
3. **"Use My IP Address (via SOCKS5 Proxy)"** checkbox'ını işaretleyin
4. **SOCKS5 Proxy Address** alanına şunu girin:
   ```
   socks5://SİZİN_IP:1080
   ```
   Örnek: `socks5://123.45.67.89:1080`

### 4. Scraping Başlatma

1. Diğer form alanlarını doldurun (Instagram account, location URLs, vb.)
2. **"Start Location Scraping"** butonuna tıklayın
3. VPS, sizin IP'niz üzerinden Instagram'a bağlanacak ✅

---

## 🔧 Sorun Giderme

### Tunnel Çalışmıyor

**Kontrol:**
```bash
# Windows
netstat -an | findstr 1080

# Mac/Linux
lsof -i :1080
```

**Çözüm:**
- SSH bağlantısını kontrol edin: `ssh root@2.59.119.90`
- Port 1080 başka bir program tarafından kullanılıyor olabilir
- Farklı bir port deneyin: `ssh -N -D 1081 -f root@2.59.119.90`

### "Connection Refused" Hatası

**Neden:** VPS'te SSH servisi çalışmıyor veya firewall port 22'yi engelliyor.

**Çözüm:**
```bash
# VPS'te SSH kontrolü
sudo systemctl status ssh
# veya
sudo systemctl status sshd

# SSH'yi başlat
sudo systemctl start ssh
sudo systemctl enable ssh
```

### IP Değişti

**Neden:** Dinamik IP kullanıyorsunuz, IP değişti.

**Çözüm:**
1. Yeni IP'nizi öğrenin: `curl https://api.ipify.org`
2. Frontend'de proxy adresini güncelleyin: `socks5://YENİ_IP:1080`

### Tunnel Kapanıyor

**Neden:** SSH bağlantısı timeout oluyor.

**Çözüm:**
SSH config dosyasına ekleyin (`~/.ssh/config`):

```
Host vps
    HostName 2.59.119.90
    User root
    ServerAliveInterval 60
    ServerAliveCountMax 3
```

Sonra:
```bash
ssh -N -D 1080 -f vps
```

---

## ⚠️ Önemli Notlar

1. **Bilgisayarınız açık olmalı:** Tunnel, bilgisayarınızda çalışır
2. **SSH bağlantısı aktif olmalı:** Tunnel kapanırsa scraping çalışmaz
3. **IP değişirse güncelleyin:** Dinamik IP kullanıyorsanız
4. **Güvenlik:** SSH şifreli bağlantı kullanır, güvenlidir

---

## 🚀 Alternatif: Otomatik Tunnel Script

**Windows (PowerShell):**

```powershell
# tunnel.ps1
$tunnel = Get-Process | Where-Object {$_.ProcessName -eq "ssh" -and $_.CommandLine -like "*1080*"}
if ($tunnel) {
    Write-Host "Tunnel already running"
} else {
    ssh -N -D 1080 -f root@2.59.119.90
    Write-Host "Tunnel started"
}
```

**Mac/Linux:**

```bash
#!/bin/bash
# tunnel.sh
if lsof -i :1080 > /dev/null 2>&1; then
    echo "Tunnel already running"
else
    ssh -N -D 1080 -f root@2.59.119.90
    echo "Tunnel started"
fi
```

---

## ✅ Test

1. Tunnel'ı başlatın
2. Frontend'de "Use My IP" seçin
3. Proxy adresini girin
4. Scraping başlatın
5. Backend loglarında şunu görmelisiniz:
   ```
   🌐 Using user's SOCKS5 proxy: socks5://SİZİN_IP:1080
   ```

Başarılı! 🎉




