# Move project to OneDrive-free location
# This script copies the project to C:\projects\instagram-scraper

Write-Host "📦 Copying project to OneDrive-free location..." -ForegroundColor Yellow

$sourcePath = "C:\Users\vedat\OneDrive\Masaüstü\Yeni klasör"
$destPath = "C:\projects\instagram-scraper"

# Create destination directory
New-Item -ItemType Directory -Path $destPath -Force | Out-Null

Write-Host "📋 Copying files from: $sourcePath" -ForegroundColor Cyan
Write-Host "📋 To: $destPath" -ForegroundColor Cyan

# Copy all files and folders
robocopy "$sourcePath" "$destPath" /E /COPYALL /R:1 /W:1 /NFL /NDL /NJH /NJS

if ($LASTEXITCODE -le 1) {
    Write-Host "✅ Files copied successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📝 Next steps:" -ForegroundColor Yellow
    Write-Host "   1. cd C:\projects\instagram-scraper" -ForegroundColor Cyan
    Write-Host "   2. docker build -f Dockerfile.backend -t vedatdemir14/instagram-scraper-backend:latest ." -ForegroundColor Cyan
    Write-Host "   3. docker build -f Dockerfile.frontend -t vedatdemir14/instagram-scraper-frontend:latest ." -ForegroundColor Cyan
} else {
    Write-Host "❌ Copy failed with exit code: $LASTEXITCODE" -ForegroundColor Red
    Write-Host "You may need to run PowerShell as Administrator" -ForegroundColor Yellow
}

