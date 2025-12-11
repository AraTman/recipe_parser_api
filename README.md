# 🍳 Recipe Parser API v3.0

Instagram, TikTok ve YouTube Shorts'tan yemek tariflerini otomatik çıkaran production-ready REST API.

## ✨ Özellikler (v3.0)

- 🤖 **Google AI (Gemini) Parsing:** Akıllı tarif çıkarma ve düzenleme
- 🌍 **Çok Dilli Destek:** 11 farklı dilde tarif çevirisi (TR, EN, DE, FR, ES, IT, AR, RU, ZH, JA, KO)
- ✅ **MongoDB Cache:** Dil bazlı cache sistemi
- 📊 **Cache İstatistikleri:** Toplam tarif ve erişim sayısı takibi
- 🚀 **Async Architecture:** Daha hızlı ve ölçeklenebilir
- 🔒 **Proxy Support:** Rate limit ve engelleri aşmak için proxy desteği
- 🎯 **Akıllı Parsing:** AI ile malzeme standartlaştırma ve adım düzenleme

## 🚀 Hızlı Başlangıç

### 1. Kurulum

```bash
# Virtual environment oluştur (önerilen)
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# Requirements'ı kur
pip install -r requirements.txt

# MongoDB kur (opsiyonel - cache için)
# macOS: brew install mongodb-community
# Ubuntu: sudo apt install mongodb
# Docker: docker run -d -p 27017:27017 mongo

# .env dosyası oluştur
cp .env.docker .env
# .env dosyasını düzenle (MongoDB URL, Google AI API key)
nano .env
# GOOGLE_AI_API_KEY=your_key_here ekle
```

### 2. API'yi Başlat

```bash
python3 recipe_api_production.py
```

API şu adreste çalışacak: `http://localhost:8001`

### 3. Test Et

```bash
# Türkçe tarif (varsayılan)
curl -X POST http://localhost:8001/api/v1/parse-recipe \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.instagram.com/reel/DRmSj6qjexh/"}'

# İngilizce tarif
curl -X POST http://localhost:8001/api/v1/parse-recipe \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.instagram.com/reel/DRmSj6qjexh/", "language": "en"}'

# Almanca tarif
curl -X POST http://localhost:8001/api/v1/parse-recipe \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.instagram.com/reel/DRmSj6qjexh/", "language": "de"}'

# Cache istatistikleri
curl http://localhost:8001/api/v1/cache/stats
```

## 📖 Dokümantasyon

- **API Docs:** http://localhost:8001/docs
- **ReDoc:** http://localhost:8001/redoc
- **Detaylı Dokümantasyon:** [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
- **Mobil App Konsepti:** [mobile_app_concept.md](mobile_app_concept.md)

## 🌐 Desteklenen Platformlar

- ✅ **Instagram** (Reels, Posts, IGTV)
- ✅ **TikTok** (Videos)
- ✅ **YouTube** (Shorts, Videos)

## 🌍 Desteklenen Diller

| Kod | Dil | Örnek |
|-----|-----|-------|
| `tr` | Türkçe | Varsayılan |
| `en` | English | "Carrot Cake" |
| `de` | Deutsch | "Karottenkuchen" |
| `fr` | Français | "Gâteau aux carottes" |
| `es` | Español | "Pastel de zanahoria" |
| `it` | Italiano | "Torta di carote" |
| `ar` | العربية | "كعكة الجزر" |
| `ru` | Русский | "Морковный пирог" |
| `zh` | 中文 | "胡萝卜蛋糕" |
| `ja` | 日本語 | "キャロットケーキ" |
| `ko` | 한국어 | "당근 케이크" |

## 📡 API Endpoints

### Parse Recipe (Çok Dilli)
```http
POST /api/v1/parse-recipe
Content-Type: application/json

{
  "url": "https://www.instagram.com/reel/ABC123/",
  "language": "en"
}
```

### Health Check
```http
GET /health
```

### Supported Platforms
```http
GET /api/v1/supported-platforms
```

## 📊 Response Format

### Türkçe Tarif (language: "tr")
```json
{
  "success": true,
  "recipe": {
    "title": "Kıbrıs Köftesi",
    "description": "Patates ve kıyma ile hazırlanan geleneksel Kıbrıs köftesi...",
    "ingredients": [
      {"item": "Patates", "amount": "1", "unit": "kg"},
      {"item": "Kıyma", "amount": "250", "unit": "g"}
    ],
    "steps": [
      {"order": 1, "text": "Patatesleri soyun ve rendeleyin..."}
    ],
    "total_duration": "45 dakika",
    "prep_time": "20 dakika",
    "cook_time": "25 dakika",
    "difficulty": "Kolay",
    "servings": "4 kişilik",
    "tips": ["Köfte harcı ıslaksa galeta unu ekleyin"]
  },
  "parsed_with_ai": true,
  "message": "Tarif başarıyla çıkarıldı (AI ile, dil: tr)"
}
```

### İngilizce Tarif (language: "en")
```json
{
  "success": true,
  "recipe": {
    "title": "Cyprus Meatballs",
    "description": "Traditional Cyprus meatballs made with potatoes and ground beef...",
    "ingredients": [
      {"item": "Potatoes", "amount": "1", "unit": "kg"},
      {"item": "Ground beef", "amount": "250", "unit": "g"}
    ],
    "steps": [
      {"order": 1, "text": "Peel and grate the potatoes..."}
    ],
    "difficulty": "Easy",
    "servings": "4 servings",
    "tips": ["Add breadcrumbs if mixture is too wet"]
  },
  "parsed_with_ai": true,
  "message": "Tarif başarıyla çıkarıldı (AI ile, dil: en)"
}
```

### Cache Stats Response

```json
{
  "total_recipes": 150,
  "total_accesses": 1250,
  "cache_enabled": true,
  "ai_enabled": true
}
```

## 🔧 Konfigürasyon

### Environment Variables

```bash
# .env dosyası oluştur (.env.example'ı kopyala)
cp .env.example .env
```

**.env içeriği:**
```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8001
LOG_LEVEL=INFO

# MongoDB Configuration (cache için)
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=recipe_parser

# Google AI Configuration (AI parsing ve çeviri için)
GOOGLE_AI_API_KEY=your_google_ai_api_key_here
USE_AI_PARSING=true

# Proxy Configuration (opsiyonel - rate limit/block aşmak için)
PROXY_URL=http://proxy.example.com:8080
# veya authentication ile: http://user:pass@proxy.example.com:8080
```

### MongoDB Olmadan Çalıştırma

MongoDB kurulu değilse, API cache olmadan çalışır. Her istek yeniden parse edilir.

### Proxy Kullanımı

Instagram/TikTok/YouTube rate limit veya IP block yaşıyorsanız:

1. `.env` dosyasına proxy ekleyin:
```bash
PROXY_URL=http://your-proxy-server:port
```

2. API'yi yeniden başlatın - tüm scraper'lar otomatik olarak proxy kullanacak

**Desteklenen Proxy Formatları:**
- `http://host:port`
- `http://username:password@host:port`
- `https://host:port`

**Ücretsiz Proxy Servisleri:**
- [Bright Data](https://brightdata.com) (ücretli ama güvenilir)
- [ScraperAPI](https://scraperapi.com) (Instagram için önerilir)
- [Proxy-Cheap](https://proxy-cheap.com) (uygun fiyatlı)

## 📱 Mobil App Entegrasyonu

### React Native Örneği

```javascript
const parseRecipe = async (url) => {
  const response = await fetch('http://your-server:8001/api/v1/parse-recipe', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url })
  });
  
  const data = await response.json();
  return data.recipe;
};
```

### Flutter Örneği

```dart
Future<Recipe> parseRecipe(String url) async {
  final response = await http.post(
    Uri.parse('http://your-server:8001/api/v1/parse-recipe'),
    headers: {'Content-Type': 'application/json'},
    body: jsonEncode({'url': url}),
  );
  
  return Recipe.fromJson(jsonDecode(response.body)['recipe']);
}
```

## 🚀 Production Deployment

### Docker

```bash
# Build
docker build -t recipe-parser-api .

# Run
docker run -p 8001:8001 recipe-parser-api
```

### Heroku

```bash
heroku create recipe-parser-api
git push heroku main
```

## 📝 Proje Yapısı

```
recipe_parser_api/
├── recipe_api_production.py    # Ana API dosyası
├── requirements.txt             # Python dependencies
├── test_production_api.py       # Test script
├── API_DOCUMENTATION.md         # Detaylı dokümantasyon
├── mobile_app_concept.md        # Mobil app konsepti
└── README.md                    # Bu dosya
```

## 🐛 Troubleshooting

### Port zaten kullanımda

```bash
# Port'u kullanan process'i bul ve kapat
lsof -ti:8001 | xargs kill -9
```

### Instagram "Login Required" Hatası

Instagram bazı postlar için login gerektirebilir. Public postlar için sorun yaşanmaz.

### YouTube yt-dlp Hatası

```bash
# yt-dlp'yi güncelle
pip install --upgrade yt-dlp
```

## 📊 Performance

### İlk İstek (Parse + Cache)
- **Instagram:** 2-5 saniye
- **TikTok:** 3-7 saniye (API key gerekli)
- **YouTube:** 5-10 saniye

### Cache'den Dönüş
- **Tüm platformlar:** <100ms ⚡

### AI Parsing
- **Ek süre:** +2-4 saniye (daha doğru sonuçlar)

## 🔐 Security

Production'da:
- CORS ayarlarını güncelle
- API key authentication ekle
- Rate limiting ekle
- HTTPS kullan

## 📞 Destek

- 📖 Dokümantasyon: [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
- 🐛 Issues: GitHub Issues

## 📄 License

MIT License - Ticari projelerde kullanılabilir

## 🎯 Roadmap

- [ ] TikTok API entegrasyonu
- [x] Database support (MongoDB) ✅
- [x] AI-powered parsing (OpenAI GPT) ✅
- [ ] Video download support
- [ ] Multi-language support
- [ ] Kullanıcı favorileri
- [ ] Tarif paylaşımı

---

**Made with ❤️ for food lovers**
