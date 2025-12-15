# Supabase Integration Setup Guide

Bu rehber, Instagram Scraper uygulamasında Supabase entegrasyonunu nasıl kuracağınızı açıklar.

## 1. Supabase Projesi Oluşturma

1. [Supabase](https://supabase.com) sitesine gidin
2. Yeni bir proje oluşturun
3. Proje ayarlarından `URL` ve `API Key` bilgilerini alın

## 2. Veritabanı Tablolarını Oluşturma

Supabase Dashboard > SQL Editor bölümüne gidin ve `supabase_schema.sql` dosyasındaki SQL kodlarını çalıştırın.

Bu komutlar şu tabloları oluşturacak:
- `instagram_accounts` - Instagram hesapları
- `leads` - Scraped Instagram profilleri (nationality ve bio bilgileri ile)
- `sessions` - Scraping oturumları
- `users` - Kullanıcı hesapları
- `message_templates` - Mesaj şablonları
- `campaigns` - Kampanya verileri

## 3. Environment Variables Ayarlama

Backend'de Supabase bağlantısı için gerekli environment variables:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_API_KEY=your-api-key
```

## 4. Özellikler

### ✅ Tamamlanan Özellikler

1. **Supabase Veritabanı Entegrasyonu**
   - Tüm veriler artık Supabase'de saklanıyor
   - Local storage yerine persistent database kullanımı

2. **Nationality Güncelleme**
   - Leads sayfasında nationality düzenleme butonu
   - Modal ile kolay düzenleme
   - Bio bilgilerini görüntüleme
   - Supabase'de gerçek zamanlı güncelleme

3. **Bio Bilgileri**
   - Profil bio bilgileri artık Supabase'den geliyor
   - Nationality düzenleme modalında bio görüntüleme

4. **Gelişmiş Veri Yapısı**
   - Comprehensive database schema
   - Proper indexing for performance
   - Row Level Security (RLS) enabled

## 5. API Endpoints

### Yeni Eklenen Endpoints

- `GET /leads` - Tüm leads'leri getir
- `GET /leads/sessions` - Tüm oturumları getir  
- `POST /leads/update-nationality` - Nationality güncelle

### Mevcut Endpoints (Supabase ile entegre)

- `POST /campaigns/nationality-classification` - Nationality classification
- `POST /campaigns/profile-scraping` - Profile scraping
- `GET /instagram-accounts` - Instagram hesapları
- `POST /instagram-accounts` - Yeni Instagram hesabı ekle

## 6. Frontend Güncellemeleri

### Leads Sayfası
- Nationality düzenleme butonu eklendi
- Bio bilgileri görüntüleme
- Gerçek zamanlı güncelleme
- Improved UX

### API Service
- `updateNationality()` fonksiyonu eklendi
- `getLeads()` ve `getSessions()` fonksiyonları eklendi

## 7. Kullanım

### Nationality Düzenleme
1. Leads sayfasına gidin
2. Düzenlemek istediğiniz lead'in nationality sütunundaki edit butonuna tıklayın
3. Modal açılacak, bio bilgilerini görecek ve yeni nationality girebileceksiniz
4. "Save" butonuna tıklayın

### Veri Görüntüleme
- Tüm veriler artık Supabase'den geliyor
- Bio bilgileri nationality düzenleme modalında görüntüleniyor
- Session filtreleme çalışıyor

## 8. Troubleshooting

### Supabase Bağlantı Sorunları
- Environment variables'ları kontrol edin
- Supabase proje URL ve API key'ini doğrulayın
- Network bağlantısını kontrol edin

### Nationality Güncelleme Sorunları
- Backend loglarını kontrol edin
- Supabase'de leads tablosunun doğru oluşturulduğunu kontrol edin
- RLS policies'lerin doğru ayarlandığını kontrol edin

## 9. Gelecek Geliştirmeler

- Real-time notifications
- Advanced filtering options
- Bulk nationality updates
- Export functionality improvements
- Analytics dashboard enhancements

## 10. Destek

Herhangi bir sorun yaşarsanız:
1. Backend loglarını kontrol edin
2. Supabase dashboard'da veri durumunu kontrol edin
3. Browser console'da hata mesajlarını kontrol edin

