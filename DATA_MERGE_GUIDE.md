# Veri Birleştirme Rehberi

Bu rehber, `instagram_profiles` ve `nationality_classifications` tablolarındaki verileri `leads` tablosunda birleştirme işlemini açıklar.

## 🎯 Amaç

Profile scraping sonuçları (`instagram_profiles`) ve nationality classification sonuçları (`nationality_classifications`) tablolarındaki verileri birleştirip `leads` tablosunda göstermek.

## 📊 Mevcut Tablo Yapısı

### `instagram_profiles` Tablosu
- `id` - Profil ID'si
- `username` - Instagram kullanıcı adı
- `full_name` - Tam isim
- `biography` - Bio bilgisi
- `followers_count` - Takipçi sayısı
- `following_count` - Takip edilen sayısı
- `posts_count` - Post sayısı
- `is_verified` - Doğrulanmış hesap
- `profile_pic_url` - Profil resmi URL'si
- `session_id` - Scraping oturumu

### `nationality_classifications` Tablosu
- `username` - Instagram kullanıcı adı
- `nationality` - Milliyet (TÜRK, YABANCI, vb.)
- `confidence` - Güven skoru

### `leads` Tablosu (Hedef)
- `id` - Lead ID'si
- `username` - Instagram kullanıcı adı
- `full_name` - Tam isim
- `bio` - Bio bilgisi (instagram_profiles.biography'den)
- `followers_count` - Takipçi sayısı
- `following_count` - Takip edilen sayısı
- `posts_count` - Post sayısı
- `is_verified` - Doğrulanmış hesap
- `profile_pic_url` - Profil resmi URL'si
- `nationality` - Milliyet (nationality_classifications'dan)
- `confidence` - Güven skoru
- `session_name` - Oturum adı

## 🔄 Veri Birleştirme Yöntemleri

### 1. Otomatik Birleştirme (Backend)
Backend başlatıldığında otomatik olarak veri birleştirme işlemi yapılır:

```python
# Backend başlatıldığında _load_data_from_supabase() çağrılır
# Bu fonksiyon _merge_profile_and_nationality_data() çağırır
```

### 2. Manuel Birleştirme (API)
API endpoint'i ile manuel olarak veri birleştirme:

```bash
POST /leads/merge-data
```

### 3. SQL ile Birleştirme
Supabase Dashboard > SQL Editor'de `merge_data_to_leads.sql` dosyasını çalıştırın.

## 🚀 Kullanım Adımları

### Adım 1: Backend'i Başlatın
```bash
python api.py
```

Backend başlatıldığında otomatik olarak veri birleştirme işlemi yapılacak.

### Adım 2: Frontend'de Veri Birleştirme
1. Leads sayfasına gidin
2. "Merge Data" butonuna tıklayın
3. İşlem tamamlandığında success mesajı göreceksiniz

### Adım 3: Sonuçları Kontrol Edin
- Leads tablosunda birleştirilmiş verileri görebilirsiniz
- Bio bilgileri nationality düzenleme modalında görüntülenir
- Nationality bilgileri doğru şekilde birleştirilir

## 🔍 Veri Birleştirme Mantığı

1. **Username Eşleştirme**: `instagram_profiles.username` = `nationality_classifications.username`
2. **Bio Bilgisi**: `instagram_profiles.biography` → `leads.bio`
3. **Nationality**: `nationality_classifications.nationality` → `leads.nationality`
4. **Confidence**: `nationality_classifications.confidence` → `leads.confidence`
5. **Session**: `instagram_profiles.session_id` → `leads.session_name`

## ⚠️ Önemli Notlar

### Duplicate Handling
- Aynı username'e sahip kayıtlar varsa, mevcut kayıt güncellenir
- Yeni kayıtlar eklenir

### Veri Eksikliği
- Nationality classification bulunamayan profiller için `nationality = 'UNKNOWN'`
- Bio bilgisi olmayan profiller için `bio = ''`

### Session Yönetimi
- Her session için ayrı lead kayıtları oluşturulur
- Session bilgileri `sessions` tablosunda güncellenir

## 🐛 Troubleshooting

### Veri Birleştirme Çalışmıyor
1. Supabase bağlantısını kontrol edin
2. Tabloların doğru oluşturulduğunu kontrol edin
3. Backend loglarını kontrol edin

### Bio Bilgileri Görünmüyor
1. `instagram_profiles` tablosunda `biography` sütununu kontrol edin
2. Veri birleştirme işlemini tekrar çalıştırın

### Nationality Bilgileri Eksik
1. `nationality_classifications` tablosunu kontrol edin
2. Username eşleştirmelerini kontrol edin

## 📈 Performans

- Veri birleştirme işlemi batch olarak yapılır
- Duplicate kontrolü yapılır
- Upsert (insert/update) kullanılır
- Index'ler performansı artırır

## 🔄 Güncelleme

Veri birleştirme işlemi:
- Backend başlatıldığında otomatik çalışır
- Manuel olarak API endpoint'i ile çalıştırılabilir
- Frontend'de "Merge Data" butonu ile çalıştırılabilir

## 📊 Sonuç

Başarılı veri birleştirme sonrasında:
- `leads` tablosunda tüm profil verileri
- Bio bilgileri nationality düzenleme modalında
- Nationality bilgileri doğru şekilde eşleştirilmiş
- Session bilgileri güncellenmiş

