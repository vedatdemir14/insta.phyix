#!/bin/bash

# VPS Deployment Script
# Usage: ./deploy-vps.sh

VPS_IP="37.140.242.29"
VPS_USER="root"
VPS_PASSWORD="Phyix123"
DOCKER_USERNAME="vedatdemir14"
BACKEND_IMAGE_NAME="instagram-scraper-backend"
FRONTEND_IMAGE_NAME="instagram-scraper-frontend"
VERSION="latest"

echo "🚀 Deploying to VPS..."

# Create deployment script for VPS
cat > /tmp/vps-deploy.sh << 'DEPLOYSCRIPT'
#!/bin/bash

echo "🐳 Installing Docker if not installed..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    systemctl start docker
    systemctl enable docker
    rm get-docker.sh
fi

echo "🐳 Installing Docker Compose if not installed..."
if ! command -v docker-compose &> /dev/null; then
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

echo "📥 Pulling Docker images..."
docker pull vedatdemir14/instagram-scraper-backend:latest
docker pull vedatdemir14/instagram-scraper-frontend:latest

echo "🛑 Stopping existing containers..."
docker-compose down 2>/dev/null || true

echo "📝 Creating docker-compose.yml..."
mkdir -p /opt/instagram-scraper
cd /opt/instagram-scraper

cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  backend:
    image: vedatdemir14/instagram-scraper-backend:latest
    container_name: instagram-scraper-backend
    ports:
      - "8000:8000"
    environment:
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_API_KEY=${SUPABASE_API_KEY}
      - APIFY_API_TOKEN=${APIFY_API_TOKEN}
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
      - UNIPILE_API_KEY=${UNIPILE_API_KEY}
      - UNIPILE_BASE_URL=${UNIPILE_BASE_URL}
      - DEEPL_API_KEY=${DEEPL_API_KEY}
    restart: unless-stopped
    networks:
      - app-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    image: vedatdemir14/instagram-scraper-frontend:latest
    container_name: instagram-scraper-frontend
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: unless-stopped
    networks:
      - app-network

networks:
  app-network:
    driver: bridge
EOF

echo "📝 Creating .env file template..."
if [ ! -f .env ]; then
    cat > .env << 'ENVEOF'
SUPABASE_URL=https://rltkqtlinpsueyaervdv.supabase.co
SUPABASE_API_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJsdGtxdGxpbnBzdWV5YWVydmR2Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NzU3NTk4NSwiZXhwIjoyMDczMTUxOTg1fQ.doT1nxL0izQRpCqzAY-StRFrzqRRuRyiKhZDwKfk_fI
APIFY_API_TOKEN=apify_api_VeivXy54nUuP7jP3zdPStvnY1bdy6P12ohvn
OPENROUTER_API_KEY=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
UNIPILE_API_KEY=k8IpFvnp.1H5f5alAgW2gK5M+J4GvW2M1lavbPHdsZfUGXBbEF+U=
UNIPILE_BASE_URL=https://api21.unipile.com:15121
DEEPL_API_KEY=721f4e0a-7600-425a-9bd4-7c4282e7770c:fx
ENVEOF
    echo "⚠️  Please edit .env file with your actual credentials!"
else
    echo "✅ .env file already exists"
fi

echo "🚀 Starting containers..."
docker-compose up -d

echo "⏳ Waiting for services to start..."
sleep 10

echo "✅ Deployment completed!"
echo "📊 Container status:"
docker-compose ps

echo "🌐 Access your application at:"
echo "   - Frontend: http://${VPS_IP}"
echo "   - Backend API: http://${VPS_IP}:8000"
echo "   - Health check: http://${VPS_IP}:8000/health"
DEPLOYSCRIPT

# Use sshpass to copy and execute script on VPS
if ! command -v sshpass &> /dev/null; then
    echo "❌ sshpass not installed. Please install it first:"
    echo "   Ubuntu/Debian: sudo apt-get install sshpass"
    echo "   macOS: brew install sshpass"
    echo ""
    echo "Or run the script manually on VPS by copying /tmp/vps-deploy.sh"
    exit 1
fi

echo "📤 Copying deployment script to VPS..."
sshpass -p "$VPS_PASSWORD" scp -o StrictHostKeyChecking=no /tmp/vps-deploy.sh $VPS_USER@$VPS_IP:/tmp/vps-deploy.sh

echo "🔧 Executing deployment script on VPS..."
sshpass -p "$VPS_PASSWORD" ssh -o StrictHostKeyChecking=no $VPS_USER@$VPS_IP "chmod +x /tmp/vps-deploy.sh && /tmp/vps-deploy.sh"

echo "✅ Deployment completed!"
echo "🌐 Access your application at:"
echo "   - Frontend: http://$VPS_IP"
echo "   - Backend API: http://$VPS_IP:8000"
echo "   - Health check: http://$VPS_IP:8000/health"

# Cleanup
rm /tmp/vps-deploy.sh

