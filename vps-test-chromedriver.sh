#!/bin/bash

echo "🧪 ChromeDriver Test"
echo "===================="

# ChromeDriver versiyonunu kontrol et
echo "📋 ChromeDriver versiyonu:"
docker exec instagram-scraper-backend chromedriver --version

echo ""
echo "🧪 Python ile Selenium testi:"
docker exec instagram-scraper-backend python3 << 'PYTHON_EOF'
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

try:
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.binary_location = "/usr/bin/google-chrome"
    
    print("🚀 ChromeDriver başlatılıyor...")
    driver = webdriver.Chrome(options=options)
    
    print("🌐 Google'a gidiliyor...")
    driver.get("https://www.google.com")
    
    print("✅ ChromeDriver çalışıyor!")
    print(f"📄 Title: {driver.title}")
    
    driver.quit()
    print("✅ Test başarılı!")
except Exception as e:
    print(f"❌ Hata: {e}")
    import traceback
    traceback.print_exc()
PYTHON_EOF






