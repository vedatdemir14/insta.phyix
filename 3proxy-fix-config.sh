#!/bin/bash
# Fix 3proxy config - remove daemon/nodaemon for systemd

cat > /etc/3proxy/3proxy.cfg << 'EOF'
# 3proxy configuration for Bright Data proxy
# No daemon mode needed - systemd handles it
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

chmod 600 /etc/3proxy/3proxy.cfg

echo "✅ Config updated. Restarting service..."
systemctl restart 3proxy
sleep 2
systemctl status 3proxy


