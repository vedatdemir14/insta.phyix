#!/bin/bash

echo "🔧 ChromeDriver Kurulumu (Düzeltilmiş)"
echo "========================================"

# Container içinde ChromeDriver'ı kur
docker exec instagram-scraper-backend bash -c "
    echo '📦 Chrome versiyonunu alıyorum...'
    CHROME_VERSION=\$(google-chrome --version | grep -oP '\d+\.\d+\.\d+\.\d+' | head -1)
    CHROME_MAJOR=\$(echo \$CHROME_VERSION | cut -d. -f1)
    echo \"Chrome version: \$CHROME_VERSION\"
    echo \"Chrome major: \$CHROME_MAJOR\"
    
    echo ''
    echo '📥 ChromeDriver versiyonunu alıyorum...'
    # Chrome for Testing API'den versiyonu al
    CHROMEDRIVER_VERSION=\$(curl -s 'https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions.json' | python3 -c 'import sys, json; data=json.load(sys.stdin); print(data[\"channels\"][\"Stable\"][\"version\"])' 2>/dev/null)
    
    if [ -z \"\$CHROMEDRIVER_VERSION\" ]; then
        echo '⚠️ JSON parse başarısız, alternatif yöntem deniyorum...'
        # Alternatif: Chrome major versiyonunu kullan
        CHROMEDRIVER_VERSION=\$(curl -s \"https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_\${CHROME_MAJOR}\" 2>/dev/null)
    fi
    
    if [ -z \"\$CHROMEDRIVER_VERSION\" ]; then
        echo '⚠️ Versiyon bulunamadı, en son stable versiyonu kullanıyorum...'
        CHROMEDRIVER_VERSION=\$(curl -s 'https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions.json' | grep -o '\"version\": \"[0-9.]*\"' | head -1 | cut -d'\"' -f4)
    fi
    
    echo \"ChromeDriver version: \$CHROMEDRIVER_VERSION\"
    
    if [ -z \"\$CHROMEDRIVER_VERSION\" ]; then
        echo '❌ ChromeDriver versiyonu bulunamadı!'
        exit 1
    fi
    
    echo ''
    echo '📥 ChromeDriver indiriliyor...'
    cd /tmp
    wget -O chromedriver.zip \"https://storage.googleapis.com/chrome-for-testing-public/\${CHROMEDRIVER_VERSION}/linux64/chromedriver-linux64.zip\" 2>&1
    
    if [ ! -f chromedriver.zip ] || [ \$(stat -c%s chromedriver.zip 2>/dev/null || echo 0) -lt 1000 ]; then
        echo '❌ ChromeDriver indirme başarısız!'
        exit 1
    fi
    
    echo ''
    echo '📦 ChromeDriver kuruluyor...'
    unzip -j chromedriver.zip 'chromedriver-linux64/chromedriver' -d /usr/local/bin/ 2>&1
    chmod +x /usr/local/bin/chromedriver
    ln -sf /usr/local/bin/chromedriver /usr/bin/chromedriver
    rm -f chromedriver.zip
    
    echo ''
    echo '✅ ChromeDriver kuruldu!'
    chromedriver --version
"

echo ""
echo "🧪 Test:"
docker exec instagram-scraper-backend chromedriver --version || echo "❌ ChromeDriver hala bulunamadı"






