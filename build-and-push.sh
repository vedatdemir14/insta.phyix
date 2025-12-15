#!/bin/bash

# Docker Build and Push Script
# Usage: ./build-and-push.sh

DOCKER_USERNAME="vedatdemir14"
BACKEND_IMAGE_NAME="instagram-scraper-backend"
FRONTEND_IMAGE_NAME="instagram-scraper-frontend"
VERSION="latest"

echo "🐳 Building Docker images..."

# Build backend image
echo "📦 Building backend image..."
docker build -f Dockerfile.backend -t $DOCKER_USERNAME/$BACKEND_IMAGE_NAME:$VERSION .
if [ $? -ne 0 ]; then
    echo "❌ Backend build failed!"
    exit 1
fi

# Build frontend image
echo "📦 Building frontend image..."
docker build -f Dockerfile.frontend -t $DOCKER_USERNAME/$FRONTEND_IMAGE_NAME:$VERSION .
if [ $? -ne 0 ]; then
    echo "❌ Frontend build failed!"
    exit 1
fi

echo "✅ Images built successfully!"

# Login to Docker Hub
echo "🔐 Logging in to Docker Hub..."
docker login -u $DOCKER_USERNAME

if [ $? -ne 0 ]; then
    echo "❌ Docker login failed!"
    exit 1
fi

# Push backend image
echo "📤 Pushing backend image..."
docker push $DOCKER_USERNAME/$BACKEND_IMAGE_NAME:$VERSION
if [ $? -ne 0 ]; then
    echo "❌ Backend push failed!"
    exit 1
fi

# Push frontend image
echo "📤 Pushing frontend image..."
docker push $DOCKER_USERNAME/$FRONTEND_IMAGE_NAME:$VERSION
if [ $? -ne 0 ]; then
    echo "❌ Frontend push failed!"
    exit 1
fi

echo "✅ All images pushed successfully!"
echo "📋 Image names:"
echo "   - $DOCKER_USERNAME/$BACKEND_IMAGE_NAME:$VERSION"
echo "   - $DOCKER_USERNAME/$FRONTEND_IMAGE_NAME:$VERSION"

