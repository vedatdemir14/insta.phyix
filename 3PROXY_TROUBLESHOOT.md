# 3proxy Sorun Giderme

## 🔍 Hata Analizi

Service başlatılamıyor. Şu komutları çalıştırıp hata mesajını görelim:

```bash
# Service durumu
systemctl status 3proxy.service

# Detaylı loglar
journalctl -xeu 3proxy.service -n 50

# Config dosyasını kontrol et
cat /etc/3proxy/3proxy.cfg

# Binary'nin çalışıp çalışmadığını test et
/usr/local/bin/3proxy /etc/3proxy/3proxy.cfg
```

## 🔧 Olası Çözümler

### Çözüm 1: PID File Dizini Oluştur

```bash
mkdir -p /var/run
chmod 755 /var/run
```

### Çözüm 2: Service Tipini Değiştir

Eğer `forking` tipi çalışmıyorsa, `simple` tipine geçelim:

```bash
cat > /etc/systemd/system/3proxy.service << 'EOF'
[Unit]
Description=3proxy Proxy Server
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/3proxy /etc/3proxy/3proxy.cfg
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl restart 3proxy
```

### Çözüm 3: Config Dosyasını Düzelt

Config dosyasında `daemon` yerine `nodaemon` kullanabiliriz (systemd ile):

```bash
cat > /etc/3proxy/3proxy.cfg << 'EOF'
# 3proxy configuration for Bright Data proxy
# nodaemon mode for systemd
nodaemon
maxconn 200
nserver 8.8.8.8
nserver 8.8.4.4

# Logging
log /var/log/3proxy/3proxy.log D
logformat "- %U %C:%c %R:%r %O %I %h %T"

# Bright Data proxy chain
parent 1000 http brd.superproxy.io 33335 brd-customer-hl_3f13e61d-zone-vps_proxy-country-tr vm3jw4lgmt92

# Local proxy server
proxy -p3128 -n
EOF

systemctl restart 3proxy
```

### Çözüm 4: Manuel Test

```bash
# Config dosyasını manuel test et
/usr/local/bin/3proxy /etc/3proxy/3proxy.cfg

# Başka bir terminal'de test et
curl -x http://localhost:3128 https://google.com
```

## 📋 Hızlı Düzeltme (Tüm Çözümler)

```bash
# 1. PID dizini oluştur
mkdir -p /var/run
chmod 755 /var/run

# 2. Config'i nodaemon ile güncelle
cat > /etc/3proxy/3proxy.cfg << 'EOF'
nodaemon
maxconn 200
nserver 8.8.8.8
nserver 8.8.4.4
log /var/log/3proxy/3proxy.log D
logformat "- %U %C:%c %R:%r %O %I %h %T"
parent 1000 http brd.superproxy.io 33335 brd-customer-hl_3f13e61d-zone-vps_proxy-country-tr vm3jw4lgmt92
proxy -p3128 -n
EOF

# 3. Service'i simple tipine çevir
cat > /etc/systemd/system/3proxy.service << 'EOF'
[Unit]
Description=3proxy Proxy Server
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/3proxy /etc/3proxy/3proxy.cfg
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# 4. Yeniden başlat
systemctl daemon-reload
systemctl restart 3proxy
systemctl status 3proxy
```

