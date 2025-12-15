# Proxynetic Residential Proxy Kurulum Rehberi

## 🎯 En İyi Seçenek: Rotating Residential Proxy

**Neden?**
- ✅ **Gerçek ev IP'leri** - Instagram tarafından gerçek kullanıcı gibi görünür
- ✅ **Otomatik IP rotasyonu** - Her istekte farklı IP, ban riski düşük
- ✅ **Yüksek başarı oranı** - Instagram bot detection'ı geçer
- ✅ **Uygun fiyat** - 12₺/GB (kullanım bazlı)

## 📋 Proxynetic Kurulum Adımları

### 1. Proxynetic Hesabı Oluşturma

1. https://proxynetic.com adresine gidin
2. Hesap oluşturun
3. **Rotating Residential Proxy** paketini satın alın
4. Dashboard'dan proxy bilgilerinizi alın:
   - **Username**: `your_username`
   - **Password**: `your_password`
   - **Endpoint**: `gate.proxynetic.com` (veya size verilen endpoint)
   - **Port**: Genellikle `8080` veya `1080` (SOCKS5 için)

### 2. Proxy Formatı

Proxynetic genellikle şu formatları destekler:

**HTTP/HTTPS:**
```
http://username:password@gate.proxynetic.com:8080
```

**SOCKS5:**
```
socks5://username:password@gate.proxynetic.com:1080
```

### 3. VPS'te Backend'e Proxy Ekleme

Frontend'den proxy bilgilerini gönderin:

1. **Campaigns** → **Location Scraping**
2. **"Use Proxynetic Residential Proxy"** checkbox'ını işaretleyin
3. Proxy bilgilerini girin:
   - **Proxy Type**: SOCKS5 veya HTTP
   - **Proxy Address**: `gate.proxynetic.com:1080`
   - **Username**: Proxynetic kullanıcı adınız
   - **Password**: Proxynetic şifreniz

### 4. Test Etme

1. Scraping başlatın
2. Backend loglarında şunu görmelisiniz:
   ```
   🌐 Using Proxynetic Residential Proxy: socks5://gate.proxynetic.com:1080
   ✅ Proxy connection successful
   ```

---

## 🔧 Proxy Tipleri Karşılaştırması

### ✅ Rotating Residential (ÖNERİLEN)
- **Fiyat**: 12₺/GB
- **Avantaj**: Otomatik IP rotasyonu, gerçek ev IP'leri
- **Instagram için**: ⭐⭐⭐⭐⭐ (Mükemmel)

### Residential Proxy
- **Fiyat**: 19₺/IP
- **Avantaj**: Sabit IP, gerçek ev IP'leri
- **Instagram için**: ⭐⭐⭐⭐ (İyi, ama rotasyon yok)

### Mobil Proxy
- **Fiyat**: 12₺/GB
- **Avantaj**: Mobil operatör IP'leri
- **Instagram için**: ⭐⭐⭐⭐ (İyi)

### Rotating Mobil
- **Fiyat**: 14.41₺/GB
- **Avantaj**: Otomatik mobil IP rotasyonu
- **Instagram için**: ⭐⭐⭐⭐ (İyi)

### ❌ Datacenter Proxy (ÖNERİLMEZ)
- **Fiyat**: 2₺/IP
- **Dezavantaj**: Instagram tarafından kolayca tespit edilir
- **Instagram için**: ⭐⭐ (Kötü - ban riski yüksek)

### IPv6 Residential
- **Fiyat**: 0,15₺/IP
- **Avantaj**: Ucuz, IPv6 desteği
- **Instagram için**: ⭐⭐⭐ (Orta - IPv6 desteği gerekir)

---

## 💡 İpuçları

1. **Rotating Residential kullanın** - En güvenilir seçenek
2. **SOCKS5 tercih edin** - HTTP'den daha güvenilir
3. **Rate limiting yapın** - Çok hızlı istekler ban'a yol açabilir
4. **IP rotasyonunu kontrol edin** - Her istekte farklı IP kullanıldığını doğrulayın

---

## 🚀 Hızlı Başlangıç

1. Proxynetic'te **Rotating Residential** paketi alın
2. Proxy bilgilerinizi alın (username, password, endpoint, port)
3. Frontend'de proxy bilgilerini girin
4. Scraping'i başlatın
5. Backend loglarında proxy kullanımını kontrol edin

**Başarılı! 🎉**


