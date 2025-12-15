#!/bin/bash
# Debug 3proxy issues

echo "🔍 Checking 3proxy logs..."
tail -20 /var/log/3proxy/3proxy.log 2>/dev/null || echo "No log file found"

echo ""
echo "🔍 Checking journal logs..."
journalctl -u 3proxy -n 30 --no-pager

echo ""
echo "🔍 Checking if port 3128 is in use..."
netstat -tuln | grep 3128 || ss -tuln | grep 3128

echo ""
echo "🔍 Checking config file..."
cat /etc/3proxy/3proxy.cfg

echo ""
echo "🔍 Testing 3proxy manually (foreground)..."
/usr/local/bin/3proxy /etc/3proxy/3proxy.cfg

