# Fix file permissions for Docker build
# Run this script in PowerShell as Administrator

Write-Host "🔧 Fixing file permissions..." -ForegroundColor Yellow

# Fix Python files
if (Test-Path "api.py") {
    icacls "api.py" /reset
    attrib -R "api.py"
    Write-Host "✅ Fixed api.py" -ForegroundColor Green
}

if (Test-Path "backend.py") {
    icacls "backend.py" /reset
    attrib -R "backend.py"
    Write-Host "✅ Fixed backend.py" -ForegroundColor Green
}

if (Test-Path "requirements.txt") {
    icacls "requirements.txt" /reset
    attrib -R "requirements.txt"
    Write-Host "✅ Fixed requirements.txt" -ForegroundColor Green
}

# Fix frontend files
if (Test-Path "frontend") {
    Get-ChildItem -Path "frontend" -Recurse -File | ForEach-Object {
        icacls $_.FullName /reset | Out-Null
        attrib -R $_.FullName
    }
    Write-Host "✅ Fixed frontend files" -ForegroundColor Green
}

Write-Host "✅ All permissions fixed!" -ForegroundColor Green
Write-Host "Now try: docker build -f Dockerfile.backend -t vedatdemir14/instagram-scraper-backend:latest ." -ForegroundColor Cyan

