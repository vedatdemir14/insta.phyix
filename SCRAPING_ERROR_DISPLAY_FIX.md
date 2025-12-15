# VPS Scraping Hatalarını Frontend'de Gösterme

## Yapılan Değişiklikler

### 1. Backend - Instagram Selector Düzeltmesi

`backend.py` dosyasında username field selector'larına `aria-label` desteği eklendi:

```python
username_selectors = [
    # ... mevcut selector'lar ...
    (By.XPATH, "//input[@aria-label[contains(., 'kullanıcı adı') or contains(., 'username') or contains(., 'e-posta') or contains(., 'email') or contains(., 'Telefon')]]"),
    (By.CSS_SELECTOR, "input[aria-label*='kullanıcı adı'], input[aria-label*='username'], input[aria-label*='e-posta'], input[aria-label*='email'], input[aria-label*='Telefon']"),
]
```

### 2. Backend - Detaylı Hata Mesajları

`api.py` dosyasında hata mesajları artık detaylı dönüyor:

```python
except Exception as e:
    import traceback
    error_detail = str(e)
    error_traceback = traceback.format_exc()
    raise HTTPException(
        status_code=500, 
        detail={
            "error": error_detail,
            "traceback": error_traceback,
            "type": type(e).__name__
        }
    )
```

### 3. Frontend - Hata Mesajlarını Gösterme

`frontend/src/pages/Campaigns.tsx` dosyasında error handling güncellendi:

- Location scraping hataları artık detaylı gösteriliyor
- Profile scraping hataları artık detaylı gösteriliyor
- Hata mesajları 10 saniye gösteriliyor
- Traceback console'da loglanıyor

## Kullanım

Artık VPS'te scraping yaparken oluşan hatalar:

1. **Frontend'de detaylı mesaj olarak gösterilecek**
2. **Browser console'da traceback görünecek**
3. **10 saniye boyunca ekranda kalacak**

## Test

1. Location scraping yaparken hata oluşursa, frontend'de detaylı hata mesajı görünecek
2. Browser console'da (F12) full traceback görünecek
3. Hata mesajı 10 saniye gösterilecek

## Notlar

- Instagram selector'ları artık `aria-label` attribute'unu da kontrol ediyor
- Backend hataları artık detaylı olarak frontend'e dönüyor
- Frontend error handling iyileştirildi




