# Windows Build Sorunu - Çözüm Rehberi

## ❌ Hata:
```
ERROR: failed to solve: failed to checksum file api.py: archive/tar: unknown file mode ?rwxr-xr-x
```

## 🔍 Sorunun Nedeni:
- OneDrive klasöründe dosyalar
- Türkçe karakterli klasör adları ("Masaüstü", "Yeni klasör")
- Windows dosya izin sistemi ile Docker'ın Linux izin sistemi arasındaki uyumsuzluk

## ✅ Çözümler (Tercih Sırasına Göre):

### Çözüm 1: Dosyaları OneDrive Dışına Taşıyın (ÖNERİLEN)

```powershell
# 1. Yeni bir klasör oluşturun (OneDrive dışında, Türkçe karakter yok)
mkdir C:\projects\instagram-scraper

# 2. Tüm dosyaları kopyalayın
xcopy "C:\Users\vedat\OneDrive\Masaüstü\Yeni klasör\*" C:\projects\instagram-scraper\ /E /I

# 3. Yeni klasöre geçin
cd C:\projects\instagram-scraper

# 4. Build yapın
docker build -f Dockerfile.backend -t vedatdemir14/instagram-scraper-backend:latest .
```

### Çözüm 2: Dockerfile'ı Güncelleme (Uygulandı)

Dockerfile.backend dosyası güncellendi. Şimdi tekrar deneyin:

```bash
docker build -f Dockerfile.backend -t vedatdemir14/instagram-scraper-backend:latest .
```

### Çözüm 3: WSL (Windows Subsystem for Linux) Kullanma

```powershell
# 1. WSL'i açın
wsl

# 2. Projeyi WSL içine kopyalayın
cp -r /mnt/c/Users/vedat/OneDrive/Masaüstü/"Yeni klasör" ~/instagram-scraper

# 3. WSL içinde build yapın
cd ~/instagram-scraper
docker build -f Dockerfile.backend -t vedatdemir14/instagram-scraper-backend:latest .
```

### Çözüm 4: Dosya İzinlerini Manuel Düzeltme

```powershell
# Tüm .py dosyalarının izinlerini düzeltin
icacls api.py /reset
icacls backend.py /reset
```

## 🚀 Hızlı Test

Dockerfile güncellemesinden sonra:

```bash
docker build -f Dockerfile.backend -t vedatdemir14/instagram-scraper-backend:latest .
```

Hala hata alırsanız, **Çözüm 1**'i uygulayın (dosyaları OneDrive dışına taşıyın).

## 📝 Not

OneDrive klasörleri Docker build sırasında sık sık sorun çıkarır çünkü:
- Dosyalar "cloud-first" olarak saklanır
- Dosya izinleri OneDrive tarafından yönetilir
- Türkçe karakterler bazı sistemlerde sorun çıkarabilir

**En iyi pratik:** Proje dosyalarını OneDrive dışında bir yerde tutun (örn: `C:\projects\`).

