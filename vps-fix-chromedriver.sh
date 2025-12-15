#!/bin/bash

echo "🔧 ChromeDriver Kurulumu ve Backend Kontrolü"
echo "=============================================="

cd /opt/instagram-scraper

# 1. Backend loglarını kontrol et
echo ""
echo "📊 Backend Logları (son 50 satır):"
docker compose logs --tail=50 backend

echo ""
echo "=============================================="
echo ""

# 2. Container durumunu kontrol et
echo "📦 Container Durumu:"
docker compose ps

echo ""
echo "=============================================="
echo ""

# 3. Container içinde ChromeDriver'ı manuel kur
echo "🔧 ChromeDriver'ı manuel kuruyor..."
docker exec instagram-scraper-backend bash -c "
    # Chrome versiyonunu al
    CHROME_VERSION=\$(google-chrome --version | grep -oP '\d+\.\d+\.\d+\.\d+' | head -1)
    CHROME_MAJOR=\$(echo \$CHROME_VERSION | cut -d. -f1)
    echo \"Chrome version: \$CHROME_VERSION\"
    echo \"Chrome major: \$CHROME_MAJOR\"
    
    # ChromeDriver versiyonunu al
    CHROMEDRIVER_VERSION=\$(curl -s 'https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions.json' | grep -o '\"version\": \"[^\"]*\"' | head -1 | cut -d'\"' -f4)
    echo \"ChromeDriver version: \$CHROMEDRIVER_VERSION\"
    
    # ChromeDriver'ı indir ve kur
    cd /tmp
    wget -O chromedriver.zip \"https://storage.googleapis.com/chrome-for-testing-public/\${CHROMEDRIVER_VERSION}/linux64/chromedriver-linux64.zip\"
    unzip -j chromedriver.zip 'chromedriver-linux64/chromedriver' -d /usr/local/bin/
    chmod +x /usr/local/bin/chromedriver
    ln -sf /usr/local/bin/chromedriver /usr/bin/chromedriver
    rm chromedriver.zip
    
    # Test et
    chromedriver --version
"

echo ""
echo "=============================================="
echo ""

# 4. ChromeDriver test
echo "🧪 ChromeDriver Test:"
docker exec instagram-scraper-backend chromedriver --version || echo "❌ ChromeDriver hala bulunamadı"

echo ""
echo "✅ İşlem tamamlandı!"






