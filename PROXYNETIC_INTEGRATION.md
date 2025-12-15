# Proxynetic Proxy Entegrasyonu

## 🎯 En İyi Seçenek: Rotating Residential Proxy

**Neden Rotating Residential?**
- ✅ **Gerçek ev IP'leri** - Instagram tarafından gerçek kullanıcı gibi görünür
- ✅ **Otomatik IP rotasyonu** - Her istekte farklı IP, ban riski düşük
- ✅ **Yüksek başarı oranı** - Instagram bot detection'ı geçer
- ✅ **Uygun fiyat** - 12₺/GB (kullanım bazlı)

## 📋 Proxynetic Proxy Formatı

Proxynetic genellikle şu formatları destekler:

### HTTP/HTTPS Proxy:
```
http://username:password@gate.proxynetic.com:8080
```

### SOCKS5 Proxy:
```
socks5://username:password@gate.proxynetic.com:1080
```

## 🔧 Backend Entegrasyonu

Backend zaten `user_proxy` parametresini destekliyor. Proxynetic proxy'yi şu şekilde kullanabilirsiniz:

### Frontend'de Kullanım:

1. **Campaigns** → **Location Scraping**
2. **"Use My IP Address (via SOCKS5 Proxy)"** checkbox'ını işaretleyin
3. Proxy adresini girin:
   ```
   socks5://username:password@gate.proxynetic.com:1080
   ```
   veya
   ```
   http://username:password@gate.proxynetic.com:8080
   ```

## ⚠️ Önemli Notlar

### Chrome Proxy Authentication Sorunu

Chrome, proxy authentication (username:password) için built-in destek sunmuyor. Bu yüzden:

**Çözüm 1: Proxy Extension Kullanımı (Önerilen)**

Selenium'da proxy authentication için extension kullanılabilir. Backend'e ekleyebiliriz.

**Çözüm 2: Proxy Without Auth**

Eğer Proxynetic IP whitelist desteği sunuyorsa, VPS IP'sini whitelist'e ekleyip authentication olmadan kullanabilirsiniz.

**Çözüm 3: Proxy Chain**

VPS'te bir proxy chain oluşturup, authentication'ı orada handle edebilirsiniz.

## 🚀 Hızlı Test

1. Proxynetic'ten **Rotating Residential** paketi alın
2. Proxy bilgilerinizi alın:
   - Username
   - Password
   - Endpoint (örn: `gate.proxynetic.com`)
   - Port (SOCKS5 için genellikle `1080`, HTTP için `8080`)
3. Frontend'de proxy adresini girin:
   ```
   socks5://username:password@gate.proxynetic.com:1080
   ```
4. Scraping'i başlatın
5. Backend loglarında kontrol edin:
   ```
   🌐 Using proxy: socks5://username:password@gate.proxynetic.com:1080
   ```

## 🔍 Proxy Tipleri Karşılaştırması

| Proxy Tipi | Fiyat | Instagram İçin | Önerilen |
|------------|-------|----------------|----------|
| **Rotating Residential** | 12₺/GB | ⭐⭐⭐⭐⭐ | ✅ **EN İYİ** |
| Residential Proxy | 19₺/IP | ⭐⭐⭐⭐ | ✅ İyi |
| Mobil Proxy | 12₺/GB | ⭐⭐⭐⭐ | ✅ İyi |
| Rotating Mobil | 14.41₺/GB | ⭐⭐⭐⭐ | ✅ İyi |
| Datacenter Proxy | 2₺/IP | ⭐⭐ | ❌ Ban riski yüksek |
| IPv6 Residential | 0,15₺/IP | ⭐⭐⭐ | ⚠️ IPv6 desteği gerekir |

## 💡 İpuçları

1. **Rotating Residential kullanın** - En güvenilir seçenek
2. **SOCKS5 tercih edin** - HTTP'den daha güvenilir
3. **Rate limiting yapın** - Çok hızlı istekler ban'a yol açabilir
4. **IP rotasyonunu kontrol edin** - Her istekte farklı IP kullanıldığını doğrulayın

## 🐛 Sorun Giderme

### "Proxy authentication failed" Hatası

**Neden:** Chrome, proxy authentication'ı built-in desteklemiyor.

**Çözüm:** Proxy extension kullanın veya IP whitelist yapın.

### "Connection refused" Hatası

**Neden:** Proxy endpoint'i yanlış veya port kapalı.

**Çözüm:** Proxynetic dashboard'dan doğru endpoint ve port'u kontrol edin.

### "IP rotation not working" Sorunu

**Neden:** Rotating proxy aktif değil veya yanlış yapılandırılmış.

**Çözüm:** Proxynetic dashboard'da rotating proxy'nin aktif olduğunu kontrol edin.


