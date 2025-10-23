# 🍳 Recipe Parser API - Documentation

## 📋 Genel Bakış

Instagram, TikTok ve YouTube Shorts'tan yemek tariflerini otomatik çıkaran production-ready REST API.

## 🚀 Hızlı Başlangıç

### 1. Kurulum

```bash
# Repository'yi clone'la
cd milyem_wp_bot

# Requirements'ları kur
pip install -r requirements_recipe_api.txt

# API'yi başlat
python3 recipe_api_production.py
```

### 2. API Çalışıyor mu Kontrol Et

```bash
curl http://localhost:8001/health
```

## 📡 API Endpoints

### Health Check

**GET** `/health`

```bash
curl http://localhost:8001/health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "supported_platforms": ["Instagram", "TikTok", "YouTube Shorts"],
  "timestamp": "2025-10-23T19:00:00"
}
```

---

### Parse Recipe (Ana Endpoint)

**POST** `/api/v1/parse-recipe`

Instagram, TikTok veya YouTube Shorts URL'den tarif çıkarır.

**Request Body:**
```json
{
  "url": "https://www.instagram.com/p/ABC123/"
}
```

**Response:**
```json
{
  "success": true,
  "recipe": {
    "title": "Havuçlu Tarçınlı Kek",
    "description": "Sonbaharın vazgeçilmezi...",
    "ingredients": [
      {
        "item": "Yumurta",
        "amount": "3",
        "unit": "adet"
      },
      {
        "item": "Toz şeker",
        "amount": "1",
        "unit": "su bardağı"
      }
    ],
    "steps": [
      {
        "order": 1,
        "text": "Yumurta ve şekeri karıştırın",
        "duration": null,
        "tip": null
      }
    ],
    "total_duration": "50 dakika",
    "prep_time": null,
    "cook_time": null,
    "difficulty": "Orta",
    "servings": null,
    "calories": null,
    "source_url": "https://www.instagram.com/p/ABC123/",
    "source_platform": "instagram",
    "video_duration": 13.933,
    "thumbnail_url": "https://...",
    "author_username": "chef_user",
    "author_name": "Chef Name",
    "likes": 43420,
    "comments": 293,
    "hashtags": ["tarçınlıkek", "kek"],
    "created_at": "2025-10-23T19:00:00"
  },
  "message": "Tarif başarıyla çıkarıldı"
}
```

**Error Response:**
```json
{
  "success": false,
  "recipe": null,
  "error": "Geçersiz Instagram URL",
  "message": "Geçersiz URL veya desteklenmeyen platform"
}
```

---

### Supported Platforms

**GET** `/api/v1/supported-platforms`

Desteklenen platformları listeler.

```bash
curl http://localhost:8001/api/v1/supported-platforms
```

**Response:**
```json
{
  "platforms": [
    {
      "name": "Instagram",
      "types": ["Reels", "Posts", "IGTV"],
      "example": "https://www.instagram.com/p/ABC123/"
    },
    {
      "name": "TikTok",
      "types": ["Videos"],
      "example": "https://www.tiktok.com/@user/video/123456"
    },
    {
      "name": "YouTube",
      "types": ["Shorts", "Videos"],
      "example": "https://www.youtube.com/shorts/ABC123"
    }
  ]
}
```

---

## 📱 Mobil App Entegrasyonu

### React Native / Flutter Örneği

```javascript
// API call function
async function parseRecipe(url) {
  try {
    const response = await fetch('http://your-server:8001/api/v1/parse-recipe', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ url: url })
    });
    
    const data = await response.json();
    
    if (data.success) {
      return data.recipe;
    } else {
      throw new Error(data.error);
    }
  } catch (error) {
    console.error('Recipe parse error:', error);
    throw error;
  }
}

// Kullanım
const recipe = await parseRecipe('https://www.instagram.com/p/ABC123/');
console.log(recipe.title);
console.log(recipe.ingredients);
console.log(recipe.steps);
```

---

## 🔧 Production Deployment

### Docker ile Deploy

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements_recipe_api.txt .
RUN pip install --no-cache-dir -r requirements_recipe_api.txt

COPY recipe_api_production.py .

EXPOSE 8001

CMD ["python3", "recipe_api_production.py"]
```

```bash
# Build
docker build -t recipe-parser-api .

# Run
docker run -p 8001:8001 recipe-parser-api
```

### Systemd Service (Linux)

```ini
[Unit]
Description=Recipe Parser API
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/recipe-api
ExecStart=/usr/bin/python3 /opt/recipe-api/recipe_api_production.py
Restart=always

[Install]
WantedBy=multi-user.target
```

### Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name api.yourapp.com;

    location / {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## ⚡ Performance & Limits

### Rate Limiting

- Instagram: ~200 requests/saat (login olmadan)
- TikTok: API key gerekli
- YouTube: yt-dlp ile sınırsız

### Response Time

- Instagram: 2-5 saniye
- TikTok: 3-7 saniye
- YouTube: 5-10 saniye

### Caching (Önerilen)

```python
# Redis ile caching ekle
import redis
cache = redis.Redis(host='localhost', port=6379)

# URL'yi cache key olarak kullan
cache_key = f"recipe:{url}"
cached = cache.get(cache_key)

if cached:
    return json.loads(cached)
else:
    recipe = parse_recipe(url)
    cache.setex(cache_key, 3600, json.dumps(recipe))  # 1 saat
    return recipe
```

---

## 🐛 Troubleshooting

### Instagram "Login Required" Hatası

```python
# Çözüm: Session cookie kullan
loader = instaloader.Instaloader()
loader.load_session_from_file('username')
```

### TikTok API Hatası

```bash
# TikTok için RapidAPI key gerekli
# https://rapidapi.com/tikwm-tikwm-default/api/tiktok-scraper7
```

### YouTube yt-dlp Hatası

```bash
# yt-dlp'yi güncelle
pip install --upgrade yt-dlp
```

---

## 📊 Monitoring

### Health Check Endpoint

```bash
# Cron job ile health check
*/5 * * * * curl -f http://localhost:8001/health || systemctl restart recipe-api
```

### Logging

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('recipe_api.log'),
        logging.StreamHandler()
    ]
)
```

---

## 🔐 Security

### API Key Authentication (Önerilen)

```python
from fastapi import Header, HTTPException

async def verify_api_key(x_api_key: str = Header()):
    if x_api_key != "your-secret-key":
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return x_api_key

@app.post("/api/v1/parse-recipe", dependencies=[Depends(verify_api_key)])
async def parse_recipe(request: RecipeRequest):
    ...
```

### CORS Configuration

```python
# Production'da specific origin'ler ekle
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourapp.com"],  # Sadece mobil app domain'i
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)
```

---

## 📞 Support

- 📧 Email: support@yourapp.com
- 📖 Docs: http://localhost:8001/docs
- 🐛 Issues: GitHub Issues

---

## 📝 License

MIT License - Free to use for commercial projects
