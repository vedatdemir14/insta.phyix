# 3proxy Final Fix

## 🔍 Sorun

3proxy service sürekli restart oluyor. Muhtemelen:
1. Config hatası
2. Log dosyası yazma izni yok
3. Port zaten kullanılıyor
4. 3proxy binary hatası

## 📋 Debug Adımları

```bash
# 1. Logları kontrol et
tail -20 /var/log/3proxy/3proxy.log
journalctl -u 3proxy -n 30

# 2. Port kontrolü
netstat -tuln | grep 3128
# veya
ss -tuln | grep 3128

# 3. Manuel test (foreground'da çalıştır)
/usr/local/bin/3proxy /etc/3proxy/3proxy.cfg
```

## 🔧 Çözüm 1: Log Dizini İzinleri

```bash
# Log dizini izinlerini düzelt
chmod 755 /var/log/3proxy
chown root:root /var/log/3proxy

# Config dosyası izinleri
chmod 600 /etc/3proxy/3proxy.cfg
chown root:root /etc/3proxy/3proxy.cfg
```

## 🔧 Çözüm 2: Config Dosyasını Basitleştir

```bash
cat > /etc/3proxy/3proxy.cfg << 'EOF'
maxconn 200
nserver 8.8.8.8
log /var/log/3proxy/3proxy.log D
parent 1000 http brd.superproxy.io 33335 brd-customer-hl_3f13e61d-zone-vps_proxy-country-tr vm3jw4lgmt92
proxy -p3128 -n
EOF

systemctl restart 3proxy
```

## 🔧 Çözüm 3: Manuel Çalıştırma (Test)

```bash
# Service'i durdur
systemctl stop 3proxy

# Manuel olarak foreground'da çalıştır
/usr/local/bin/3proxy /etc/3proxy/3proxy.cfg

# Başka bir terminal'de test et
curl -x http://localhost:3128 https://google.com
```

## 🔧 Çözüm 4: Systemd Service'i Düzelt

```bash
cat > /etc/systemd/system/3proxy.service << 'EOF'
[Unit]
Description=3proxy Proxy Server
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/3proxy /etc/3proxy/3proxy.cfg
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal
User=root
WorkingDirectory=/etc/3proxy

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl restart 3proxy
```

## 🔧 Çözüm 5: Alternatif - Squid Proxy Kullan

Eğer 3proxy çalışmıyorsa, Squid kullanabiliriz:

```bash
apt-get install -y squid

cat > /etc/squid/squid.conf << 'EOF'
http_port 3128
cache deny all
http_access allow all

# Bright Data proxy chain
cache_peer brd.superproxy.io parent 33335 0 no-query default login=brd-customer-hl_3f13e61d-zone-vps_proxy-country-tr:vm3jw4lgmt92
never_direct allow all
EOF

systemctl restart squid
```

