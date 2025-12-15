# Hostingdunyam VPS Firewall Ayarları

## Port 8000 Açma - Hostingdunyam

Hostingdunyam VPS'inizde port 8000'i açmak için aşağıdaki adımları takip edin:

### Yöntem 1: Hostingdunyam Kontrol Paneli

1. **Hostingdunyam Müşteri Paneline Giriş Yapın**
   - https://www.hostingdunyam.com/ üzerinden giriş yapın
   - Müşteri panelinize giriş yapın

2. **VPS Yönetim Bölümüne Gidin**
   - "VPS Yönetimi" veya "Sunucu Yönetimi" bölümüne gidin
   - VPS'inizi seçin

3. **Firewall/Güvenlik Duvarı Ayarları**
   - "Firewall" veya "Güvenlik Duvarı" sekmesine gidin
   - "Port Yönetimi" veya "Port Açma" bölümüne gidin

4. **Port 8000'i Ekleyin**
   - **Port:** 8000
   - **Protokol:** TCP
   - **Yön:** Gelen (Inbound)
   - **Kaynak:** Tümü (0.0.0.0/0) veya belirli IP'ler
   - **Kaydet**

### Yöntem 2: Destek Talebi Açma

Eğer kontrol panelinde firewall ayarları yoksa:

1. **Hostingdunyam Destek Sistemine Giriş Yapın**
2. **Yeni Destek Talebi Oluşturun**
3. **Konu:** "VPS Firewall - Port 8000 Açma Talebi"
4. **Mesaj:**
   ```
   Merhaba,
   
   VPS IP: 37.140.242.29
   Port: 8000
   Protokol: TCP
   Yön: Gelen (Inbound)
   
   Backend API servisim için port 8000'in dışarıdan erişilebilir olması gerekiyor.
   Lütfen firewall'da bu portu açabilir misiniz?
   
   Teşekkürler.
   ```

### Yöntem 3: SSH Üzerinden Kontrol

VPS'inizde şu komutları çalıştırarak durumu kontrol edin:

```bash
# Firewall durumunu kontrol et
sudo ufw status verbose

# iptables kurallarını kontrol et
sudo iptables -L -n -v | grep 8000

# Port dinleme kontrolü
sudo ss -tuln | grep 8000
```

### Yöntem 4: Hostingdunyam Özel Panel (Varsa)

Bazı hostingdunyam VPS'lerde özel bir yönetim paneli olabilir:

1. VPS yönetim panelinize giriş yapın
2. "Network" veya "Ağ Ayarları" bölümüne gidin
3. "Firewall Rules" veya "Güvenlik Kuralları" sekmesine gidin
4. Port 8000 için yeni kural ekleyin

## Test

Firewall ayarlarını yaptıktan sonra:

```bash
# VPS'ten test
curl http://localhost:8000/health

# Dışarıdan test (başka bir makineden veya browser'dan)
curl http://37.140.242.29:8000/health

# Browser'dan test
http://37.140.242.29:8000/health
```

## Önemli Notlar

- Hostingdunyam bazı portları varsayılan olarak engelleyebilir
- Destek ekibinden port açma talebinde bulunmanız gerekebilir
- Port açma işlemi genellikle 1-2 saat içinde tamamlanır
- Güvenlik için sadece gerekli IP'lere izin vermek daha iyidir

## Alternatif: Destek İletişim

Eğer yukarıdaki yöntemler işe yaramazsa:

- **E-posta:** destek@hostingdunyam.com (veya size verilen destek e-postası)
- **Telefon:** Hostingdunyam destek hattı
- **Canlı Destek:** Müşteri panelinden canlı destek

Destek ekibine şu bilgileri verin:
- VPS IP: 37.140.242.29
- Port: 8000
- Protokol: TCP
- Amaç: Backend API servisi




