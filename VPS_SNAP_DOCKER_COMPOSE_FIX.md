# Snap Docker Compose Sorunu Çözümü

## Sorun
```
open /var/lib/snapd/void/docker-compose.yml: no such file or directory
```

Snap ile kurulan Docker Compose, dosya yolunu bulamıyor çünkü snap izolasyonu nedeniyle farklı bir dosya sistemi kullanıyor.

## Çözüm: Standart Docker Compose Kurulumu

### Adım 1: Snap Docker Compose'u Kaldır

```bash
# Snap Docker Compose'u kontrol et
snap list | grep docker-compose

# Kaldır (eğer varsa)
snap remove docker-compose
```

### Adım 2: Standart Docker Compose Kur

```bash
# En son versiyonu indir
DOCKER_COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d\" -f4)
echo "Kurulacak versiyon: $DOCKER_COMPOSE_VERSION"

# Docker Compose'u indir
curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# Çalıştırılabilir yap
chmod +x /usr/local/bin/docker-compose

# Versiyon kontrolü
docker-compose version
```

### Adım 3: Docker Compose'u Kullan

```bash
cd /opt/instagram-scraper
docker-compose up -d
```

## Alternatif: Docker Compose Plugin (Docker CLI ile)

Eğer Docker CLI v2 kullanıyorsanız, `docker compose` (tire olmadan) komutu zaten mevcut olabilir:

```bash
# Docker Compose plugin kontrolü
docker compose version

# Eğer çalışıyorsa, direkt kullanın
cd /opt/instagram-scraper
docker compose up -d
```

## Hızlı Kurulum (Tek Komut)

```bash
# Snap Docker Compose'u kaldır ve standart versiyonu kur
snap remove docker-compose 2>/dev/null || true && \
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose && \
chmod +x /usr/local/bin/docker-compose && \
docker-compose version
```

## Sorun Giderme

### Hala çalışmıyorsa:

```bash
# Hangi docker-compose kullanılıyor?
which docker-compose

# PATH'i kontrol et
echo $PATH

# Manuel olarak tam yol ile çalıştır
/usr/local/bin/docker-compose up -d
```

### Permission hatası:

```bash
# Dosya izinlerini kontrol et
ls -la /usr/local/bin/docker-compose

# Gerekirse izinleri düzelt
chmod +x /usr/local/bin/docker-compose
```




