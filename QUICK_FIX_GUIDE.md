# Hızlı Düzeltme Rehberi

## 🚨 Sorun
`leads` tablosunda `bio` sütunu bulunamıyor hatası alıyorsunuz.

## ✅ Çözüm

### Adım 1: Supabase Dashboard'da Tabloyu Düzeltin

1. **Supabase Dashboard**'a gidin
2. **SQL Editor**'e gidin
3. `quick_fix_leads.sql` dosyasındaki kodu çalıştırın:

```sql
-- Add bio column (as biography to match instagram_profiles table)
ALTER TABLE leads ADD COLUMN IF NOT EXISTS biography TEXT;

-- Add other missing columns
ALTER TABLE leads ADD COLUMN IF NOT EXISTS followers_count INTEGER DEFAULT 0;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS following_count INTEGER DEFAULT 0;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS posts_count INTEGER DEFAULT 0;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS is_verified BOOLEAN DEFAULT false;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS profile_pic_url TEXT;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS nationality VARCHAR(100);
ALTER TABLE leads ADD COLUMN IF NOT EXISTS confidence DECIMAL(5,2) DEFAULT 0.00;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS session_name VARCHAR(255);
ALTER TABLE leads ADD COLUMN IF NOT EXISTS scraped_at TIMESTAMP DEFAULT NOW();
ALTER TABLE leads ADD COLUMN IF NOT EXISTS last_updated TIMESTAMP DEFAULT NOW();
```

### Adım 2: Backend'i Yeniden Başlatın

```bash
python api.py
```

### Adım 3: Veri Birleştirme

Backend başlatıldığında otomatik olarak veri birleştirme çalışacak. Eğer çalışmazsa:

1. **Frontend'de "Merge Data" butonuna tıklayın**
2. Veya API endpoint'ini çağırın: `POST /leads/merge-data`

## 🔍 Kontrol

### Tablo Yapısını Kontrol Edin
```sql
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'leads' AND table_schema = 'public'
ORDER BY ordinal_position;
```

### Veri Birleştirme Sonucunu Kontrol Edin
```sql
SELECT COUNT(*) as total_leads FROM leads;
SELECT COUNT(*) as profiles_with_bio FROM leads WHERE biography IS NOT NULL AND biography != '';
SELECT COUNT(*) as profiles_with_nationality FROM leads WHERE nationality IS NOT NULL;
```

## 📊 Beklenen Sonuç

- ✅ `leads` tablosunda tüm gerekli sütunlar olacak
- ✅ `instagram_profiles` verileri `leads` tablosuna aktarılacak
- ✅ `nationality_classifications` verileri `leads` tablosuna aktarılacak
- ✅ Bio bilgileri `biography` sütununda görünecek
- ✅ Nationality bilgileri doğru şekilde eşleştirilecek

## 🐛 Hala Sorun Varsa

1. **Supabase Dashboard**'da `leads` tablosunu kontrol edin
2. **Backend loglarını** kontrol edin
3. **Network bağlantısını** kontrol edin
4. **Supabase API key'ini** kontrol edin

## 🎯 Sonuç

Bu düzeltme sonrasında:
- Veri birleştirme çalışacak
- Bio bilgileri görünecek
- Nationality düzenleme çalışacak
- Tüm veriler `leads` tablosunda birleşik olarak görünecek

