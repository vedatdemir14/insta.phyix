# Docker Build and Push Script for Windows PowerShell
# Usage: .\build-and-push.ps1

$DOCKER_USERNAME = "vedatdemir14"
$BACKEND_IMAGE_NAME = "instagram-scraper-backend"
$FRONTEND_IMAGE_NAME = "instagram-scraper-frontend"
$VERSION = "latest"

Write-Host "🐳 Building Docker images..." -ForegroundColor Cyan

# Build backend image
Write-Host "📦 Building backend image..." -ForegroundColor Yellow
docker build -f Dockerfile.backend -t "$DOCKER_USERNAME/$BACKEND_IMAGE_NAME`:$VERSION" .
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Backend build failed!" -ForegroundColor Red
    exit 1
}

# Build frontend image
Write-Host "📦 Building frontend image..." -ForegroundColor Yellow
docker build -f Dockerfile.frontend -t "$DOCKER_USERNAME/$FRONTEND_IMAGE_NAME`:$VERSION" .
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Frontend build failed!" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Images built successfully!" -ForegroundColor Green

# Login to Docker Hub
Write-Host "🔐 Logging in to Docker Hub..." -ForegroundColor Cyan
docker login -u $DOCKER_USERNAME

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker login failed!" -ForegroundColor Red
    exit 1
}

# Push backend image
Write-Host "📤 Pushing backend image..." -ForegroundColor Yellow
docker push "$DOCKER_USERNAME/$BACKEND_IMAGE_NAME`:$VERSION"
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Backend push failed!" -ForegroundColor Red
    exit 1
}

# Push frontend image
Write-Host "📤 Pushing frontend image..." -ForegroundColor Yellow
docker push "$DOCKER_USERNAME/$FRONTEND_IMAGE_NAME`:$VERSION"
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Frontend push failed!" -ForegroundColor Red
    exit 1
}

Write-Host "✅ All images pushed successfully!" -ForegroundColor Green
Write-Host "📋 Image names:" -ForegroundColor Cyan
Write-Host "   - $DOCKER_USERNAME/$BACKEND_IMAGE_NAME`:$VERSION"
Write-Host "   - $DOCKER_USERNAME/$FRONTEND_IMAGE_NAME`:$VERSION"

