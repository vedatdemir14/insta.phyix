# Bright Data Proxy Kurulum Rehberi

## 🎯 Çözüm: 3proxy ile Proxy Chain

Chrome, proxy URL'inde username:password formatını desteklemediği için, VPS'te **3proxy** kurup authentication'ı orada handle edeceğiz.

## 📋 Kurulum Adımları

### 1. VPS'te 3proxy Kurulumu

VPS'e SSH ile bağlanın ve şu komutları çalıştırın:

```bash
# 3proxy'yi kur
apt-get update
apt-get install -y 3proxy

# 3proxy config dosyası oluştur
cat > /etc/3proxy/3proxy.cfg << 'EOF'
# 3proxy configuration for Bright Data proxy
daemon
maxconn 200
nserver 8.8.8.8
nserver 8.8.4.4

# Logging
log /var/log/3proxy/3proxy.log D
logformat "- %U %C:%c %R:%r %O %I %h %T"

# Bright Data proxy chain
# Format: parent 1000 http brd.superproxy.io 33335 brd-customer-hl_3f13e61d-zone-vps_proxy-country-tr vm3jw4lgmt92
parent 1000 http brd.superproxy.io 33335 brd-customer-hl_3f13e61d-zone-vps_proxy-country-tr vm3jw4lgmt92

# Local proxy server (Chrome buraya bağlanacak)
proxy -p3128
EOF

# Log dizini oluştur
mkdir -p /var/log/3proxy
chmod 755 /var/log/3proxy

# 3proxy'yi başlat
systemctl enable 3proxy
systemctl start 3proxy

# Durumu kontrol et
systemctl status 3proxy
```

### 2. Firewall Ayarları

```bash
# Port 3128'i aç (3proxy için)
ufw allow 3128/tcp
```

### 3. Test Etme

```bash
# VPS'te test
curl -x http://localhost:3128 https://geo.brdtest.com/welcome.txt?product=resi&method=native

# Dışarıdan test (opsiyonel)
curl -x http://2.59.119.90:3128 https://geo.brdtest.com/welcome.txt?product=resi&method=native
```

### 4. Frontend'de Kullanım

1. **Campaigns** → **Location Scraping**
2. **"Use My IP Address (via SOCKS5 Proxy)"** checkbox'ını işaretleyin
3. Proxy adresini girin:
   ```
   http://localhost:3128
   ```
   veya VPS dışından erişiyorsanız:
   ```
   http://2.59.119.90:3128
   ```

## 🔧 Alternatif: Docker Container'da 3proxy

Eğer Docker container içinde kullanmak istiyorsanız:

### Dockerfile'a 3proxy Ekleme

```dockerfile
# 3proxy kurulumu
RUN apt-get update && apt-get install -y 3proxy && \
    mkdir -p /var/log/3proxy && \
    chmod 755 /var/log/3proxy

# 3proxy config
COPY 3proxy.cfg /etc/3proxy/3proxy.cfg

# 3proxy'yi başlat (entrypoint script'inde)
```

### Docker Compose ile Ayrı Container

```yaml
services:
  proxy:
    image: 3proxy/3proxy:latest
    container_name: bright-data-proxy
    ports:
      - "3128:3128"
    volumes:
      - ./3proxy.cfg:/etc/3proxy/3proxy.cfg
    restart: unless-stopped
```

## 📝 3proxy Config Dosyası (Detaylı)

`/etc/3proxy/3proxy.cfg` dosyası:

```
# 3proxy configuration for Bright Data
daemon
maxconn 200
nserver 8.8.8.8
nserver 8.8.4.4

# Logging
log /var/log/3proxy/3proxy.log D
logformat "- %U %C:%c %R:%r %O %I %h %T"

# Bright Data proxy chain
# parent <timeout> <type> <host> <port> <username> <password>
parent 1000 http brd.superproxy.io 33335 brd-customer-hl_3f13e61d-zone-vps_proxy-country-tr vm3jw4lgmt92

# Local proxy server (Chrome buraya bağlanacak, authentication yok)
proxy -p3128 -n
```

## 🔍 Sorun Giderme

### "Connection refused" Hatası

```bash
# 3proxy'nin çalışıp çalışmadığını kontrol et
systemctl status 3proxy

# Port'un dinlendiğini kontrol et
netstat -tuln | grep 3128
# veya
ss -tuln | grep 3128

# Logları kontrol et
tail -f /var/log/3proxy/3proxy.log
```

### "Authentication failed" Hatası

```bash
# 3proxy config dosyasını kontrol et
cat /etc/3proxy/3proxy.cfg

# Bright Data credentials'ları doğru mu kontrol et
curl -i --proxy brd.superproxy.io:33335 --proxy-user brd-customer-hl_3f13e61d-zone-vps_proxy-country-tr:vm3jw4lgmt92 -k "https://geo.brdtest.com/welcome.txt?product=resi&method=native"
```

### 3proxy Yeniden Başlatma

```bash
systemctl restart 3proxy
```

## 💡 İpuçları

1. **3proxy loglarını takip edin** - Sorun giderme için önemli
2. **Firewall'u kontrol edin** - Port 3128 açık olmalı
3. **Bright Data credentials'ları güvenli tutun** - Config dosyasına sadece root erişebilmeli
4. **Rate limiting yapın** - Bright Data limitlerini aşmayın

## 🚀 Hızlı Başlangıç

```bash
# 1. 3proxy kur
apt-get install -y 3proxy

# 2. Config oluştur
cat > /etc/3proxy/3proxy.cfg << 'EOF'
daemon
maxconn 200
nserver 8.8.8.8
parent 1000 http brd.superproxy.io 33335 brd-customer-hl_3f13e61d-zone-vps_proxy-country-tr vm3jw4lgmt92
proxy -p3128 -n
EOF

# 3. Başlat
systemctl enable 3proxy
systemctl start 3proxy

# 4. Test et
curl -x http://localhost:3128 https://geo.brdtest.com/welcome.txt?product=resi&method=native
```

**Başarılı! 🎉**

