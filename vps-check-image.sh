#!/bin/bash
# Check if container is using latest image

echo "🔍 Checking Docker image and container status..."
echo ""

echo "1️⃣ Current running container image:"
docker inspect instagram-scraper-backend --format='{{.Config.Image}}' 2>/dev/null || echo "Container not found"

echo ""
echo "2️⃣ Image digest in container:"
docker inspect instagram-scraper-backend --format='{{.Image}}' 2>/dev/null || echo "Container not found"

echo ""
echo "3️⃣ Latest image digest from registry:"
docker pull vedatdemir14/instagram-scraper-backend:latest 2>&1 | grep -i digest || echo "Could not get digest"

echo ""
echo "4️⃣ Local image details:"
docker images vedatdemir14/instagram-scraper-backend:latest

echo ""
echo "5️⃣ Container creation time:"
docker inspect instagram-scraper-backend --format='{{.Created}}' 2>/dev/null || echo "Container not found"

echo ""
echo "📝 To update:"
echo "   docker compose pull backend"
echo "   docker compose down"
echo "   docker compose up -d"

