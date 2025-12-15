# API Test Script
# Tests all endpoints locally

$baseUrl = "http://localhost:8000"

Write-Host "🧪 Testing Instagram Scraper API..." -ForegroundColor Cyan
Write-Host ""

# Test 1: Health Check
Write-Host "1️⃣ Testing Health Check..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/health" -Method Get
    Write-Host "   ✅ Health Check: $($response | ConvertTo-Json)" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Health Check failed: $_" -ForegroundColor Red
}

Write-Host ""

# Test 2: Root endpoint
Write-Host "2️⃣ Testing Root Endpoint..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/" -Method Get
    Write-Host "   ✅ Root: $($response | ConvertTo-Json)" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Root failed: $_" -ForegroundColor Red
}

Write-Host ""

# Test 3: Get Instagram Accounts
Write-Host "3️⃣ Testing Get Instagram Accounts..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/instagram-accounts" -Method Get
    Write-Host "   ✅ Instagram Accounts: Found $($response.data.Count) accounts" -ForegroundColor Green
    if ($response.data.Count -gt 0) {
        Write-Host "   📋 First account: $($response.data[0].username)" -ForegroundColor Cyan
    }
} catch {
    Write-Host "   ❌ Get Instagram Accounts failed: $_" -ForegroundColor Red
}

Write-Host ""

# Test 4: Get Leads
Write-Host "4️⃣ Testing Get Leads..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/leads" -Method Get
    Write-Host "   ✅ Leads: Found $($response.data.Count) leads" -ForegroundColor Green
    if ($response.data.Count -gt 0) {
        Write-Host "   📋 First lead: $($response.data[0].username)" -ForegroundColor Cyan
    }
} catch {
    Write-Host "   ❌ Get Leads failed: $_" -ForegroundColor Red
}

Write-Host ""

# Test 5: Get Sessions
Write-Host "5️⃣ Testing Get Sessions..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/leads/sessions" -Method Get
    Write-Host "   ✅ Sessions: Found $($response.data.Count) sessions" -ForegroundColor Green
    if ($response.data.Count -gt 0) {
        Write-Host "   📋 First session: $($response.data[0].name)" -ForegroundColor Cyan
    }
} catch {
    Write-Host "   ❌ Get Sessions failed: $_" -ForegroundColor Red
}

Write-Host ""

# Test 6: Dashboard Stats
Write-Host "6️⃣ Testing Dashboard Stats..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/dashboard/stats" -Method Get
    Write-Host "   ✅ Dashboard Stats: $($response | ConvertTo-Json -Depth 2)" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Dashboard Stats failed: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "✅ API Testing completed!" -ForegroundColor Green
Write-Host ""
Write-Host "📝 Note: If any test failed, make sure:" -ForegroundColor Yellow
Write-Host "   1. API is running (python api.py)" -ForegroundColor White
Write-Host "   2. API is accessible at http://localhost:8000" -ForegroundColor White
Write-Host "   3. No firewall is blocking the connection" -ForegroundColor White


