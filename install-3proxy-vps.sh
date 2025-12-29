#!/bin/bash
# 3proxy Installation Script for Ubuntu VPS
# This script installs 3proxy from source

set -e

echo "🚀 Installing 3proxy from source..."

# Install build dependencies
echo "📦 Installing build dependencies..."
apt-get update
apt-get install -y wget make gcc

# Create 3proxy directory
echo "📁 Creating 3proxy directories..."
mkdir -p /etc/3proxy
mkdir -p /var/log/3proxy
chmod 755 /var/log/3proxy

# Download 3proxy source
echo "⬇️ Downloading 3proxy source code..."
cd /tmp
wget -q https://github.com/z3APA3A/3proxy/archive/refs/heads/master.zip -O 3proxy-master.zip

# Install unzip if not present
apt-get install -y unzip

# Extract
unzip -q 3proxy-master.zip
cd 3proxy-master

# Build
echo "🔨 Building 3proxy..."
make -f Makefile.Linux

# Install
echo "📦 Installing 3proxy..."
cp bin/3proxy /usr/local/bin/
chmod +x /usr/local/bin/3proxy

# Create systemd service
echo "⚙️ Creating systemd service..."
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

# Create config file
echo "⚙️ Creating 3proxy configuration..."
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
# Format: parent <timeout> <type> <host> <port> <username> <password>
parent 1000 http brd.superproxy.io 33335 brd-customer-hl_3f13e61d-zone-vps_proxy-country-tr vm3jw4lgmt92

# Local proxy server (Chrome buraya bağlanacak, authentication yok)
proxy -p3128 -n
EOF

# Set permissions
chmod 600 /etc/3proxy/3proxy.cfg

# Reload systemd
systemctl daemon-reload

# Enable and start service
echo "🔄 Starting 3proxy service..."
systemctl enable 3proxy
systemctl start 3proxy

# Wait a moment
sleep 2

# Check status
if systemctl is-active --quiet 3proxy; then
    echo "✅ 3proxy is running"
else
    echo "❌ 3proxy failed to start. Check logs: journalctl -u 3proxy"
    exit 1
fi

# Configure firewall
echo "🔥 Configuring firewall..."
if command -v ufw &> /dev/null; then
    ufw allow 3128/tcp
    echo "✅ Firewall rule added for port 3128"
fi

# Test proxy
echo "🧪 Testing proxy connection..."
if curl -x http://localhost:3128 --max-time 10 -s https://geo.brdtest.com/welcome.txt?product=resi&method=native > /dev/null; then
    echo "✅ Proxy test successful!"
    echo ""
    echo "🎉 3proxy is ready!"
    echo ""
    echo "📋 Usage in frontend:"
    echo "   Proxy address: http://localhost:3128"
    echo "   Or from outside: http://2.59.119.90:3128"
    echo ""
    echo "📊 Check logs: tail -f /var/log/3proxy/3proxy.log"
    echo "🔄 Restart: systemctl restart 3proxy"
    echo "📈 Status: systemctl status 3proxy"
else
    echo "⚠️ Proxy test failed. Check configuration and Bright Data credentials."
    echo "📋 Check logs: tail -f /var/log/3proxy/3proxy.log"
    echo "📋 Check service: systemctl status 3proxy"
fi

# Cleanup
cd /
rm -rf /tmp/3proxy-master /tmp/3proxy-master.zip

echo ""
echo "✅ Installation complete!"


