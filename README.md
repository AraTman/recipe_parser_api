# 🍳 Recipe Parser API

Instagram, TikTok ve YouTube Shorts'tan yemek tariflerini otomatik çıkaran production-ready REST API.

## 🚀 Hızlı Başlangıç

### 1. Kurulum

```bash
# Virtual environment oluştur (önerilen)
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# Requirements'ları kur
pip install -r requirements.txt
```

### 2. API'yi Başlat

```bash
python3 recipe_api_production.py
```

API şu adreste çalışacak: `http://localhost:8001`

### 3. Test Et

```bash
# Otomatik testleri çalıştır
python3 test_production_api.py

# Veya manuel test
curl -X POST http://localhost:8001/api/v1/parse-recipe \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.instagram.com/p/ABC123/"}'
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

## 📡 API Endpoints

### Parse Recipe
```http
POST /api/v1/parse-recipe
Content-Type: application/json

{
  "url": "https://www.instagram.com/p/ABC123/"
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

```json
{
  "success": true,
  "recipe": {
    "title": "Havuçlu Tarçınlı Kek",
    "ingredients": [
      {
        "item": "Yumurta",
        "amount": "3",
        "unit": "adet"
      }
    ],
    "steps": [
      {
        "order": 1,
        "text": "Yumurta ve şekeri karıştırın",
        "duration": null
      }
    ],
    "total_duration": "50 dakika",
    "difficulty": "Orta",
    "source_platform": "instagram",
    "video_duration": 13.933,
    "author_username": "chef_user",
    "likes": 43420,
    "hashtags": ["kek", "tarif"]
  }
}
```

## 🔧 Konfigürasyon

### Environment Variables (Opsiyonel)

```bash
# .env dosyası oluştur
API_HOST=0.0.0.0
API_PORT=8001
LOG_LEVEL=INFO
```

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

- **Instagram:** 2-5 saniye
- **TikTok:** 3-7 saniye (API key gerekli)
- **YouTube:** 5-10 saniye

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
- [ ] Redis caching
- [ ] Database support (MongoDB)
- [ ] AI-powered parsing (OpenAI GPT)
- [ ] Video download support
- [ ] Multi-language support

---

**Made with ❤️ for food lovers**
