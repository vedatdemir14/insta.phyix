# Bright Data 3proxy Kurulum Rehberi (Ubuntu VPS)

## 🎯 Sorun

Ubuntu repo'larında 3proxy yok, kaynak kodundan derlememiz gerekiyor.

## 📋 Kurulum (VPS'te Çalıştırın)

### Yöntem 1: Otomatik Script (ÖNERİLEN)

```bash
# Script'i VPS'e kopyalayın ve çalıştırın
chmod +x install-3proxy-vps.sh
./install-3proxy-vps.sh
```

### Yöntem 2: Manuel Kurulum

```bash
# 1. Build dependencies kur
apt-get update
apt-get install -y wget make gcc unzip

# 2. Dizinleri oluştur
mkdir -p /etc/3proxy
mkdir -p /var/log/3proxy
chmod 755 /var/log/3proxy

# 3. 3proxy kaynak kodunu indir
cd /tmp
wget https://github.com/z3APA3A/3proxy/archive/refs/heads/master.zip -O 3proxy-master.zip
unzip 3proxy-master.zip
cd 3proxy-master

# 4. Derle
make -f Makefile.Linux

# 5. Kur
cp bin/3proxy /usr/local/bin/
chmod +x /usr/local/bin/3proxy

# 6. Config dosyası oluştur
cat > /etc/3proxy/3proxy.cfg << 'EOF'
daemon
maxconn 200
nserver 8.8.8.8
nserver 8.8.4.4

# Logging
log /var/log/3proxy/3proxy.log D
logformat "- %U %C:%c %R:%r %O %I %h %T"

# Bright Data proxy chain
parent 1000 http brd.superproxy.io 33335 brd-customer-hl_3f13e61d-zone-vps_proxy-country-tr vm3jw4lgmt92

# Local proxy server (Chrome buraya bağlanacak, authentication yok)
proxy -p3128 -n
EOF

chmod 600 /etc/3proxy/3proxy.cfg

# 7. Systemd service oluştur
cat > /etc/systemd/system/3proxy.service << 'EOF'
[Unit]
Description=3proxy Proxy Server
After=network.target

[Service]
Type=forking
ExecStart=/usr/local/bin/3proxy /etc/3proxy/3proxy.cfg
PIDFile=/var/run/3proxy.pid
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# 8. Service'i başlat
systemctl daemon-reload
systemctl enable 3proxy
systemctl start 3proxy

# 9. Firewall
ufw allow 3128/tcp

# 10. Test
curl -x http://localhost:3128 https://geo.brdtest.com/welcome.txt?product=resi&method=native
```

## 🔍 Sorun Giderme

### "make: command not found"

```bash
apt-get install -y make gcc
```

### "wget: command not found"

```bash
apt-get install -y wget
```

### "3proxy failed to start"

```bash
# Logları kontrol et
journalctl -u 3proxy -n 50

# Config dosyasını kontrol et
cat /etc/3proxy/3proxy.cfg

# Manuel test
/usr/local/bin/3proxy /etc/3proxy/3proxy.cfg
```

### "Connection refused"

```bash
# Port'un dinlendiğini kontrol et
netstat -tuln | grep 3128
# veya
ss -tuln | grep 3128

# Service durumu
systemctl status 3proxy
```

## 📊 Yönetim Komutları

```bash
# Service durumu
systemctl status 3proxy

# Logları görüntüle
tail -f /var/log/3proxy/3proxy.log

# Yeniden başlat
systemctl restart 3proxy

# Durdur
systemctl stop 3proxy

# Başlat
systemctl start 3proxy
```

## ✅ Test

```bash
# Local test
curl -x http://localhost:3128 https://geo.brdtest.com/welcome.txt?product=resi&method=native

# Dışarıdan test (başka bir makineden)
curl -x http://2.59.119.90:3128 https://geo.brdtest.com/welcome.txt?product=resi&method=native
```

## 🚀 Frontend'de Kullanım

1. **Campaigns** → **Location Scraping**
2. **"Use Custom Proxy (Bright Data, Proxynetic, etc.)"** checkbox'ını işaretleyin
3. Proxy adresini girin:
   ```
   http://localhost:3128
   ```
   (Backend container içinden) veya
   ```
   http://2.59.119.90:3128
   ```
   (Dışarıdan erişiyorsanız)

4. Scraping'i başlatın

**Başarılı! 🎉**

