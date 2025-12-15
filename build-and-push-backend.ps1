# Build and Push Backend with Auto Cache Busting
# Usage: .\build-and-push-backend.ps1

$DOCKER_USERNAME = "vedatdemir14"
$BACKEND_IMAGE_NAME = "instagram-scraper-backend"
$VERSION = "latest"

# Generate cache bust value based on file modification times
$apiTime = (Get-Item "api.py").LastWriteTime.Ticks
$backendTime = (Get-Item "backend.py").LastWriteTime.Ticks
$cacheBust = [math]::Floor(($apiTime + $backendTime) / 1000000)

Write-Host "🔨 Building backend with cache bust: $cacheBust" -ForegroundColor Cyan
Write-Host "📋 Files:" -ForegroundColor Yellow
Write-Host "   api.py: $(Get-Item 'api.py').LastWriteTime" -ForegroundColor White
Write-Host "   backend.py: $(Get-Item 'backend.py').LastWriteTime" -ForegroundColor White

# Build with cache bust argument
docker build `
    --build-arg CACHE_BUST=$cacheBust `
    -f Dockerfile.backend `
    -t "$DOCKER_USERNAME/$BACKEND_IMAGE_NAME`:$VERSION" .

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Build failed!" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Build successful!" -ForegroundColor Green

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
    Write-Host "❌ Push failed!" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Image pushed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Next steps on VPS:" -ForegroundColor Cyan
Write-Host "   cd /opt/instagram-scraper" -ForegroundColor White
Write-Host "   docker compose pull backend" -ForegroundColor White
Write-Host "   docker compose down; docker compose up -d" -ForegroundColor White
Write-Host '   docker compose logs -f backend' -ForegroundColor White
