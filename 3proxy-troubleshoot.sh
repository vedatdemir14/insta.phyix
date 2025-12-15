#!/bin/bash
# 3proxy Troubleshooting Script

echo "🔍 Checking 3proxy status..."
systemctl status 3proxy.service

echo ""
echo "📋 Checking logs..."
journalctl -xeu 3proxy.service -n 50 --no-pager

echo ""
echo "🔍 Checking if 3proxy binary exists..."
ls -la /usr/local/bin/3proxy

echo ""
echo "🔍 Checking config file..."
cat /etc/3proxy/3proxy.cfg

echo ""
echo "🧪 Testing 3proxy manually..."
/usr/local/bin/3proxy /etc/3proxy/3proxy.cfg

