# ⚡ Quick Start Guide

Recipe Parser API'yi 5 dakikada çalıştırın!

## 🚀 Hızlı Başlangıç (Docker ile)

### 1. Projeyi Klonla
```bash
git clone https://github.com/your-username/recipe_parser_api.git
cd recipe_parser_api
```

### 2. Environment Dosyasını Oluştur
```bash
cp .env.docker .env
```

### 3. Başlat!
```bash
# Makefile ile (önerilen)
make up

# veya Docker Compose ile
docker-compose up -d
```

### 4. Test Et
```bash
# Health check
curl http://localhost:8001/health

# Tarif parse et
curl -X POST http://localhost:8001/api/v1/parse-recipe \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.instagram.com/reel/DNX8U4tMR_P/"}'
```

### 5. Arayüzlere Eriş
- **API Docs**: http://localhost:8001/docs
- **n8n**: http://localhost:5678 (admin/changeme123)
- **MongoDB**: localhost:27017

---

## 📦 Kullanışlı Komutlar

```bash
# Logları izle
make logs

# Sadece API logları
make logs-api

# Servisleri yeniden başlat
make restart

# Durdur
make down

# Temizle (volume'lar dahil)
make clean

# MongoDB shell
make shell-mongodb

# Test
make test
```

---

## 🔧 Konfigürasyon

### OpenAI AI Parsing Aktif Et
`.env` dosyasını düzenle:
```bash
OPENAI_API_KEY=sk-your-api-key
ENABLE_AI_PARSING=true
```

Yeniden başlat:
```bash
make restart-api
```

### Proxy Ekle
```bash
PROXY_URL=http://your-proxy:8080
```

---

## 🌐 Production'a Deploy

Detaylı rehber için: [DEPLOYMENT.md](DEPLOYMENT.md)

Hızlı yol:
```bash
# Production modda başlat
make prod-up

# Logları izle
make prod-logs
```

---

## 📚 Daha Fazla Bilgi

- **Detaylı Dokümantasyon**: [README.md](README.md)
- **API Dokümantasyonu**: [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
- **Deployment Rehberi**: [DEPLOYMENT.md](DEPLOYMENT.md)

---

## ❓ Sorun mu Yaşıyorsun?

```bash
# Container'ları kontrol et
docker-compose ps

# Logları kontrol et
make logs

# Yeniden başlat
make restart

# Temizle ve yeniden başlat
make clean
make up
```

---

**🎉 Hazırsın! API çalışıyor!**
