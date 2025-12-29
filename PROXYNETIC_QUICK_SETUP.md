# Proxynetic Hızlı Kurulum Rehberi

## 🎯 En İyi Seçenek: Rotating Residential Proxy (12₺/GB)

**Neden?**
- ✅ Gerçek ev IP'leri (Instagram tarafından gerçek kullanıcı gibi görünür)
- ✅ Otomatik IP rotasyonu (her istekte farklı IP)
- ✅ Ban riski düşük
- ✅ Uygun fiyat

## 📋 Hızlı Kurulum (3 Adım)

### 1. Proxynetic'te IP Whitelist Yapın (ÖNERİLEN)

**Neden?** Chrome, proxy URL'inde username:password formatını desteklemiyor.

**Nasıl?**
1. Proxynetic dashboard'a gidin
2. **Settings** → **IP Whitelist** bölümüne gidin
3. VPS IP'nizi ekleyin: `2.59.119.90`
4. Kaydedin

**Avantaj:**
- ✅ Authentication gerekmez
- ✅ Basit kullanım
- ✅ Daha güvenli

### 2. Proxy Bilgilerinizi Alın

Proxynetic dashboard'dan:
- **Endpoint**: `gate.proxynetic.com` (veya size verilen)
- **Port**: SOCKS5 için genellikle `1080`, HTTP için `8080`
- **Username**: (whitelist kullanıyorsanız gerekmez)
- **Password**: (whitelist kullanıyorsanız gerekmez)

### 3. Frontend'de Kullanın

1. **Campaigns** → **Location Scraping**
2. **"Use My IP Address (via SOCKS5 Proxy)"** checkbox'ını işaretleyin
3. Proxy adresini girin:
   ```
   socks5://gate.proxynetic.com:1080
   ```
   (IP whitelist kullanıyorsanız username:password gerekmez)

4. Scraping'i başlatın

## 🔧 Alternatif: Username:Password ile Kullanım

Eğer IP whitelist yapamıyorsanız:

### Seçenek 1: Proxy Extension (Gelişmiş)

Backend'de proxy extension kullanılabilir (proxy_auth_extension klasöründe).

### Seçenek 2: VPS'te Proxy Chain

VPS'te 3proxy gibi bir proxy server çalıştırıp authentication'ı orada handle edebilirsiniz.

### Seçenek 3: Manuel Authentication

Proxy URL'inde username:password formatını kullanın, backend otomatik olarak uyarı verecek ve IP whitelist önerecek.

## 📊 Proxy Tipleri Karşılaştırması

| Proxy Tipi | Fiyat | Instagram İçin | Önerilen |
|------------|-------|----------------|----------|
| **Rotating Residential** | 12₺/GB | ⭐⭐⭐⭐⭐ | ✅ **EN İYİ** |
| Residential Proxy | 19₺/IP | ⭐⭐⭐⭐ | ✅ İyi |
| Mobil Proxy | 12₺/GB | ⭐⭐⭐⭐ | ✅ İyi |
| Rotating Mobil | 14.41₺/GB | ⭐⭐⭐⭐ | ✅ İyi |
| Datacenter Proxy | 2₺/IP | ⭐⭐ | ❌ Ban riski yüksek |
| IPv6 Residential | 0,15₺/IP | ⭐⭐⭐ | ⚠️ IPv6 desteği gerekir |

## ✅ Test

1. Proxynetic'te IP whitelist yapın (VPS IP: `2.59.119.90`)
2. Proxy adresini frontend'e girin: `socks5://gate.proxynetic.com:1080`
3. Scraping'i başlatın
4. Backend loglarında kontrol edin:
   ```
   🌐 Using proxy: socks5://gate.proxynetic.com:1080
   ```

## 🐛 Sorun Giderme

### "Proxy authentication failed"

**Çözüm:** IP whitelist yapın veya proxy extension kullanın.

### "Connection refused"

**Çözüm:** Proxynetic dashboard'dan doğru endpoint ve port'u kontrol edin.

### "IP rotation not working"

**Çözüm:** Rotating Residential paketinin aktif olduğunu kontrol edin.

## 💡 İpuçları

1. **IP Whitelist kullanın** - En basit ve güvenli yöntem
2. **Rotating Residential seçin** - En güvenilir seçenek
3. **SOCKS5 tercih edin** - HTTP'den daha güvenilir
4. **Rate limiting yapın** - Çok hızlı istekler ban'a yol açabilir

**Başarılı! 🎉**



