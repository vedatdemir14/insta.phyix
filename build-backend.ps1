# Build Backend with Cache Busting
# Usage: .\build-backend.ps1

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
Write-Host ""
Write-Host "📤 To push:" -ForegroundColor Cyan
Write-Host "   docker push $DOCKER_USERNAME/$BACKEND_IMAGE_NAME`:$VERSION" -ForegroundColor White

