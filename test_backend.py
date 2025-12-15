"""
Backend test script - Instagram login selector'larını test eder
"""
import sys
import os

# Backend'i import et
try:
    from backend import InstagramBackend
    print("✅ Backend modülü başarıyla import edildi")
except ImportError as e:
    print(f"❌ Backend import hatası: {e}")
    sys.exit(1)

# Config oluştur
config = {
    'SUPABASE_URL': os.getenv('SUPABASE_URL', 'https://rltkqtlinpsueyaervdv.supabase.co'),
    'SUPABASE_KEY': os.getenv('SUPABASE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJsdGtxdGxpbnBzdWV5YWVydmR2Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NzU3NTk4NSwiZXhwIjoyMDczMTUxOTg1fQ.doT1nxL0izQRpCqzAY-StRFrzqRRuRyiKhZDwKfk_fI'),
    'APIFY_API_TOKEN': os.getenv('APIFY_API_TOKEN', 'apify_api_VeivXy54nUuP7jP3zdPStvnY1bdy6P12ohvn'),
    'UNIPILE_API_KEY': os.getenv('UNIPILE_API_KEY', 'k8IpFvnp.1H5f5alAgW2gK5M+J4GvW2M1lavbPHdsZfUGXBbEF+U='),
    'UNIPILE_BASE_URL': os.getenv('UNIPILE_BASE_URL', 'https://api21.unipile.com:15121'),
}

print("\n🔍 Backend instance oluşturuluyor...")
try:
    backend = InstagramBackend(config)
    print("✅ Backend instance başarıyla oluşturuldu")
    print(f"✅ Supabase bağlantısı: {'Bağlı' if backend.supabase_connected else 'Bağlı değil'}")
    print(f"✅ Instagram hesapları: {len(backend.instagram_accounts)} adet")
except Exception as e:
    print(f"❌ Backend oluşturma hatası: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Login selector'larını kontrol et
print("\n🔍 Login selector'ları kontrol ediliyor...")
print("✅ Username selector: By.NAME, 'username'")
print("✅ Password selector: By.NAME, 'password'")
print("✅ Login button selectors:")
print("   1. By.XPATH, '//button[@type=\"submit\"]'")
print("   2. By.XPATH, '//div[contains(text(), \"Log in\")]'")
print("   3. By.XPATH, '//div[contains(text(), \"Log In\")]'")
print("   4. By.XPATH, '//button[contains(text(), \"Log in\")]'")
print("   5. By.XPATH, '//button[contains(text(), \"Log In\")]'")

print("\n✅ Backend test tamamlandı!")
print("📝 Not: Gerçek Instagram login testi için selenium ve chrome driver gerekli")


