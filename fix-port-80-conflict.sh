#!/bin/bash
# Fix port 80 conflict

echo "🔍 Checking what's using port 80..."

# Check what's using port 80
lsof -i :80 2>/dev/null || netstat -tuln | grep :80 || ss -tuln | grep :80

echo ""
echo "🔍 Checking services..."
systemctl list-units --type=service --state=running | grep -E "(nginx|apache|httpd)"

echo ""
echo "💡 Options:"
echo "1. Stop the service using port 80"
echo "2. Change frontend port to 8080 or 3000"
echo ""
echo "Which option? (1 or 2)"


