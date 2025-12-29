#!/bin/bash
# Clean 3proxy installation from scratch

set -e

echo "🧹 Removing old 3proxy installation..."

# Stop and disable service
systemctl stop 3proxy 2>/dev/null || true
systemctl disable 3proxy 2>/dev/null || true

# Remove service file
rm -f /etc/systemd/system/3proxy.service

# Remove binary
rm -f /usr/local/bin/3proxy

# Remove config and logs
rm -rf /etc/3proxy
rm -rf /var/log/3proxy

echo "✅ Old installation removed"

echo ""
echo "📦 Installing 3proxy from source..."

# Install dependencies
apt-get update
apt-get install -y wget make gcc unzip

# Create directories
mkdir -p /etc/3proxy
mkdir -p /var/log/3proxy
chmod 755 /var/log/3proxy

# Download and build
cd /tmp
rm -rf 3proxy-master 3proxy-master.zip
wget -q https://github.com/z3APA3A/3proxy/archive/refs/heads/master.zip -O 3proxy-master.zip
unzip -q 3proxy-master.zip
cd 3proxy-master
make -f Makefile.Linux

# Install
cp bin/3proxy /usr/local/bin/
chmod +x /usr/local/bin/3proxy

echo "✅ 3proxy installed"

echo ""
echo "⚙️ Creating config file..."

# Create correct config with ACL
cat > /etc/3proxy/3proxy.cfg << 'EOF'
maxconn 200
nserver 8.8.8.8
nserver 8.8.4.4

# Logging
log /var/log/3proxy/3proxy.log D
logformat "- %U %C:%c %R:%r %O %I %h %T"

# ACL - must be before parent
allow * * *

# Bright Data proxy chain
parent 1000 http brd.superproxy.io 33335 brd-customer-hl_3f13e61d-zone-vps_proxy-country-tr vm3jw4lgmt92

# Local proxy server
proxy -p3128 -n
EOF

chmod 600 /etc/3proxy/3proxy.cfg

echo "✅ Config created"

echo ""
echo "⚙️ Creating systemd service..."

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

[Install]
WantedBy=multi-user.target
EOF

echo "✅ Service created"

echo ""
echo "🔄 Starting service..."

systemctl daemon-reload
systemctl enable 3proxy
systemctl start 3proxy

sleep 2

echo ""
echo "📊 Service status:"
systemctl status 3proxy --no-pager -l

echo ""
echo "🧪 Testing proxy..."
if curl -x http://localhost:3128 --max-time 10 -s https://geo.brdtest.com/welcome.txt?product=resi&method=native > /dev/null 2>&1; then
    echo "✅ Proxy test successful!"
    echo ""
    echo "🎉 3proxy is ready!"
    echo "📋 Use in frontend: http://localhost:3128"
else
    echo "⚠️ Proxy test failed. Check logs:"
    echo "   tail -f /var/log/3proxy/3proxy.log"
    echo "   journalctl -u 3proxy -n 20"
fi

# Cleanup
cd /
rm -rf /tmp/3proxy-master /tmp/3proxy-master.zip

echo ""
echo "✅ Installation complete!"


