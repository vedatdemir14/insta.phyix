# 🐳 Content Enrichment API - Docker Deployment

Bu proje, web scraping, keyword generation ve text linkification özelliklerine sahip bir Flask API'sidir.

## 🚀 Özellikler

- **Web Scraping**: Selenium ile next-button pagination scraping
- **Keyword Generation**: OpenRouter + Gemini ile AI keyword üretimi
- **Text Linkification**: Metinleri otomatik linkleme
- **Domain Kontrolü**: Aynı domain'i tekrar taramaz
- **İçindekiler Koruması**: Liste bölümlerini linklemez
- **Supabase Integration**: Database kayıt ve yönetim

## 🐳 Docker ile Çalıştırma

### 1. Docker Compose ile (Önerilen)

```bash
# Repository'yi klonla
git clone <your-repo-url>
cd Link

# Docker Compose ile çalıştır
docker-compose up -d

# Logları izle
docker-compose logs -f

# Durdur
docker-compose down
```

### 2. Docker Image ile

```bash
# Image'ı build et
docker build -t content-enrichment-api .

# Container'ı çalıştır
docker run -d \
  --name content-api \
  -p 5000:5000 \
  -e FLASK_ENV=production \
  content-enrichment-api

# Logları izle
docker logs -f content-api
```

## 🌐 API Endpoints

### Test
```bash
GET http://localhost:5000/test
```

### Scraping
```bash
# Normal scraping
GET http://localhost:5000/scrape?url=https://example.com

# Force scraping (domain kontrolünü atla)
GET http://localhost:5000/scrape?url=https://example.com&force=true
```

### Linkify
```bash
POST http://localhost:5000/linkify
Content-Type: application/json

{
  "text": "Kemoterapi, kanser tedavisinde kullanılan yöntemdir."
}
```

### Similar Titles
```bash
GET http://localhost:5000/similar-titles?query=kemoterapi&word_count=2000
```

## 🔧 Environment Variables

```bash
FLASK_ENV=production
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
OPENROUTER_API_KEY=your_openrouter_key
```

## 📊 Monitoring

### Health Check
```bash
curl http://localhost:5000/test
```

### Logs
```bash
# Docker Compose
docker-compose logs -f

# Docker
docker logs -f content-api
```

## 🚀 GitHub Actions

Bu proje GitHub Actions ile otomatik olarak Docker image'ı build edilir:

- **Push to main**: Otomatik build ve push
- **Pull Request**: Test build
- **Manual**: Workflow dispatch

### Image Registry

Image'lar GitHub Container Registry'de saklanır:
```
ghcr.io/username/repository:latest
ghcr.io/username/repository:main
```

## 🔒 Security

- Non-root user ile çalışır
- Health check ile monitoring
- Production logging
- Environment-based configuration

## 📝 Development

### Local Development
```bash
# Dependencies yükle
pip install -r requirements.txt

# Playwright browsers yükle
playwright install chromium

# Çalıştır
python api_güncel.py
```

### Docker Development
```bash
# Development build
docker build -t content-api-dev .

# Development run
docker run -p 5000:5000 content-api-dev
```

## 🐛 Troubleshooting

### Chrome/ChromeDriver Issues
```bash
# Chrome version kontrol
docker exec -it content-api google-chrome --version

# ChromeDriver version kontrol
docker exec -it content-api chromedriver --version
```

### Memory Issues
```bash
# Container resource kullanımı
docker stats content-api

# Memory limit artır
docker run --memory=2g content-api
```

## 📈 Performance

- Multi-threaded Flask
- Async keyword generation
- Connection pooling
- Caching mechanisms

## 🔄 Updates

```bash
# Image'ı güncelle
docker pull ghcr.io/username/repository:latest

# Container'ı yeniden başlat
docker-compose down
docker-compose up -d
```
