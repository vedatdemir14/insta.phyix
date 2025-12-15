# VPS Docker Daemon Sorunu Çözümü

## Sorun
```
Cannot connect to the Docker daemon at unix:///var/run/docker.sock. 
Is the docker daemon running?
```

## Çözüm Adımları

### 1. Docker Servisini Başlat

Snap ile kurulan Docker için:

```bash
# Docker servisini başlat
snap start docker

# Servisi aktif et (otomatik başlatma için)
snap enable docker

# Servis durumunu kontrol et
snap services docker
```

### 2. Alternatif: Systemd ile Başlat

Eğer snap komutları çalışmazsa:

```bash
# Systemd servisini başlat
sudo systemctl start snap.docker.dockerd.service

# Otomatik başlatma için aktif et
sudo systemctl enable snap.docker.dockerd.service

# Durumu kontrol et
sudo systemctl status snap.docker.dockerd.service
```

### 3. Docker Socket Kontrolü

Snap Docker bazen farklı socket yolu kullanır:

```bash
# Socket'i kontrol et
ls -la /var/run/docker.sock
ls -la /run/snap.docker/docker.sock

# Eğer snap socket kullanılıyorsa
export DOCKER_HOST=unix:///run/snap.docker/docker.sock
```

### 4. Docker Versiyonunu Kontrol Et

```bash
docker --version
docker ps
```

### 5. Eğer Hala Çalışmıyorsa: Docker'ı Yeniden Kur

Snap Docker yerine standart Docker kurulumu önerilir:

```bash
# Snap Docker'ı kaldır
snap remove docker

# Standart Docker kurulumu
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Docker servisini başlat
sudo systemctl start docker
sudo systemctl enable docker

# Docker Compose kur
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

## Hızlı Çözüm (Tek Komut)

```bash
snap start docker && snap enable docker && docker ps
```

## Sorun Giderme

### Docker servisi başlamıyor:
```bash
# Logları kontrol et
sudo journalctl -u snap.docker.dockerd.service -n 50

# Snap servislerini listele
snap services
```

### Permission hatası:
```bash
# Kullanıcıyı docker grubuna ekle
sudo usermod -aG docker $USER
# Yeni oturum açmanız gerekebilir
```

### Socket bulunamıyor:
```bash
# Socket dosyasını kontrol et
sudo find / -name docker.sock 2>/dev/null

# Snap Docker için socket yolu
ls -la /run/snap.docker/
```




