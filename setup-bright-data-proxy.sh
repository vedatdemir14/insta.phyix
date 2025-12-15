#!/bin/bash
# Bright Data Proxy Setup Script for VPS
# This script installs and configures 3proxy to work with Bright Data

set -e

echo "🚀 Setting up Bright Data proxy with 3proxy..."

# Bright Data credentials (replace with your actual credentials)
BRIGHT_DATA_HOST="brd.superproxy.io"
BRIGHT_DATA_PORT="33335"
BRIGHT_DATA_USER="brd-customer-hl_3f13e61d-zone-vps_proxy-country-tr"
BRIGHT_DATA_PASS="vm3jw4lgmt92"
LOCAL_PROXY_PORT="3128"

# Install 3proxy
echo "📦 Installing 3proxy..."
apt-get update
apt-get install -y 3proxy

# Create log directory
echo "📁 Creating log directory..."
mkdir -p /var/log/3proxy
chmod 755 /var/log/3proxy

# Create 3proxy config
echo "⚙️ Creating 3proxy configuration..."
cat > /etc/3proxy/3proxy.cfg << EOF
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
parent 1000 http ${BRIGHT_DATA_HOST} ${BRIGHT_DATA_PORT} ${BRIGHT_DATA_USER} ${BRIGHT_DATA_PASS}

# Local proxy server (Chrome buraya bağlanacak, authentication yok)
proxy -p${LOCAL_PROXY_PORT} -n
EOF

# Set proper permissions
chmod 600 /etc/3proxy/3proxy.cfg

# Enable and start 3proxy
echo "🔄 Starting 3proxy service..."
systemctl enable 3proxy
systemctl restart 3proxy

# Wait a moment for service to start
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
    ufw allow ${LOCAL_PROXY_PORT}/tcp
    echo "✅ Firewall rule added for port ${LOCAL_PROXY_PORT}"
fi

# Test proxy
echo "🧪 Testing proxy connection..."
if curl -x http://localhost:${LOCAL_PROXY_PORT} --max-time 10 -s https://geo.brdtest.com/welcome.txt?product=resi&method=native > /dev/null; then
    echo "✅ Proxy test successful!"
    echo ""
    echo "🎉 Bright Data proxy is ready!"
    echo ""
    echo "📋 Usage in frontend:"
    echo "   Proxy address: http://localhost:${LOCAL_PROXY_PORT}"
    echo "   Or from outside: http://$(curl -s ifconfig.me):${LOCAL_PROXY_PORT}"
    echo ""
    echo "📊 Check logs: tail -f /var/log/3proxy/3proxy.log"
    echo "🔄 Restart: systemctl restart 3proxy"
    echo "📈 Status: systemctl status 3proxy"
else
    echo "⚠️ Proxy test failed. Check configuration and Bright Data credentials."
    echo "📋 Check logs: tail -f /var/log/3proxy/3proxy.log"
    exit 1
fi

