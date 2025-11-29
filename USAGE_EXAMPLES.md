# 📚 Kullanım Örnekleri

## 🚀 Hızlı Başlangıç

### 1. MongoDB ile Çalıştırma

```bash
# MongoDB'yi başlat
docker run -d -p 27017:27017 --name recipe-mongo mongo

# .env dosyasını düzenle
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=recipe_parser

# API'yi başlat
python3 recipe_api_production.py
```

### 2. MongoDB Olmadan Çalıştırma

```bash
# .env'de MongoDB URL'yi boş bırak veya yorum satırı yap
# API otomatik olarak cache olmadan çalışır
python3 recipe_api_production.py
```

---

## 📡 API Kullanım Örnekleri

### Normal Parsing (Regex)

```bash
curl -X POST http://localhost:8001/api/v1/parse-recipe \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.instagram.com/p/ABC123/",
    "use_ai": false
  }'
```

**Avantajlar:**
- ✅ Hızlı (2-5 saniye)
- ✅ Ücretsiz
- ✅ API key gerektirmez

**Dezavantajlar:**
- ⚠️ Karmaşık tariflerde hata yapabilir
- ⚠️ Türkçe dilbilgisi kurallarına bağımlı

---

### AI-Powered Parsing (OpenAI GPT)

```bash
curl -X POST http://localhost:8001/api/v1/parse-recipe \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.instagram.com/p/ABC123/",
    "use_ai": true
  }'
```

**Avantajlar:**
- ✅ Çok daha doğru sonuçlar
- ✅ Karmaşık tarifleri anlayabilir
- ✅ Bağlam anlayışı

**Dezavantajlar:**
- ⚠️ Daha yavaş (+2-4 saniye)
- ⚠️ OpenAI API key gerekli (ücretli)

**Maliyet:**
- GPT-4o-mini: ~$0.0001 per tarif
- Aylık 1000 tarif: ~$0.10

---

### Cache İstatistikleri

```bash
curl http://localhost:8001/api/v1/cache/stats
```

**Response:**
```json
{
  "total_recipes": 150,
  "total_accesses": 1250,
  "cache_enabled": true,
  "ai_enabled": true
}
```

---

## 📱 Mobil App Entegrasyonu

### React Native Örneği

```javascript
// API service
const RecipeAPI = {
  baseURL: 'http://your-server:8001',
  
  async parseRecipe(url, useAI = false) {
    try {
      const response = await fetch(`${this.baseURL}/api/v1/parse-recipe`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url, use_ai: useAI })
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
  },
  
  async getCacheStats() {
    const response = await fetch(`${this.baseURL}/api/v1/cache/stats`);
    return await response.json();
  }
};

// Kullanım
const App = () => {
  const [recipe, setRecipe] = useState(null);
  const [loading, setLoading] = useState(false);
  
  const handlePaste = async (url) => {
    setLoading(true);
    try {
      // Normal parsing
      const recipe = await RecipeAPI.parseRecipe(url, false);
      setRecipe(recipe);
    } catch (error) {
      Alert.alert('Hata', error.message);
    } finally {
      setLoading(false);
    }
  };
  
  const handlePasteWithAI = async (url) => {
    setLoading(true);
    try {
      // AI parsing
      const recipe = await RecipeAPI.parseRecipe(url, true);
      setRecipe(recipe);
    } catch (error) {
      Alert.alert('Hata', error.message);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <View>
      <TextInput 
        placeholder="Instagram linkini yapıştır"
        onSubmitEditing={(e) => handlePaste(e.nativeEvent.text)}
      />
      <Button title="Normal Parse" onPress={() => handlePaste(url)} />
      <Button title="AI Parse" onPress={() => handlePasteWithAI(url)} />
      
      {loading && <ActivityIndicator />}
      
      {recipe && (
        <View>
          <Text>{recipe.title}</Text>
          <Text>Malzemeler: {recipe.ingredients.length}</Text>
          <Text>Adımlar: {recipe.steps.length}</Text>
        </View>
      )}
    </View>
  );
};
```

---

## 🔄 Cache Mantığı

### İlk İstek (Cache Miss)

```
1. Kullanıcı URL gönderir
2. MongoDB'de kontrol edilir → Bulunamadı
3. Instagram'dan içerik çekilir (3 saniye)
4. Tarif parse edilir (1 saniye)
5. MongoDB'ye kaydedilir
6. Kullanıcıya döndürülür
Toplam: ~4 saniye
```

### İkinci İstek (Cache Hit)

```
1. Kullanıcı aynı URL'yi gönderir
2. MongoDB'de kontrol edilir → Bulundu!
3. Cache'den döndürülür
Toplam: <100ms ⚡
```

### Cache Yönetimi

```python
# Cache'i manuel temizleme (MongoDB shell)
db.recipes.deleteMany({})

# Belirli bir URL'yi silme
db.recipes.deleteOne({"url": "https://instagram.com/p/ABC123/"})

# Eski kayıtları silme (30 günden eski)
db.recipes.deleteMany({
  "cached_at": {
    "$lt": new Date(Date.now() - 30*24*60*60*1000)
  }
})
```

---

## 🎯 Kullanım Senaryoları

### Senaryo 1: Temel Kullanım (Ücretsiz)

```javascript
// MongoDB yok, AI yok
// Her istek yeniden parse edilir
const recipe = await parseRecipe(url, false);
```

**Uygun olduğu durumlar:**
- Prototip/test
- Düşük trafik
- Maliyet hassasiyeti

---

### Senaryo 2: Cache ile (Önerilen)

```javascript
// MongoDB var, AI yok
// Aynı URL'ler cache'den döner
const recipe = await parseRecipe(url, false);
```

**Uygun olduğu durumlar:**
- Orta-yüksek trafik
- Popüler tarifler
- Hız önemli

**Avantajlar:**
- 40x daha hızlı (4s → 100ms)
- Instagram rate limit sorunları yok
- Kullanıcı deneyimi iyileşir

---

### Senaryo 3: AI ile (Premium)

```javascript
// MongoDB var, AI var
// İlk istek AI ile parse, sonrakiler cache'den
const recipe = await parseRecipe(url, true);
```

**Uygun olduğu durumlar:**
- Yüksek kalite gerekli
- Karmaşık tarifler
- Premium özellik

**Maliyet:**
- İlk parse: $0.0001
- Cache hit: $0
- 10,000 unique tarif/ay: ~$1

---

## 🔐 Production Deployment

### Docker Compose ile

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8001:8001"
    environment:
      - MONGODB_URL=mongodb://mongo:27017
      - MONGODB_DB_NAME=recipe_parser
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ENABLE_AI_PARSING=true
    depends_on:
      - mongo
  
  mongo:
    image: mongo:latest
    ports:
      - "27017:27017"
    volumes:
      - mongo_data:/data/db

volumes:
  mongo_data:
```

```bash
# Başlat
docker-compose up -d

# Logları izle
docker-compose logs -f api

# Durdur
docker-compose down
```

---

## 📊 Monitoring

### Health Check

```bash
# API sağlıklı mı?
curl http://localhost:8001/health

# Response
{
  "status": "healthy",
  "version": "2.0.0",
  "supported_platforms": ["Instagram", "TikTok", "YouTube Shorts"],
  "timestamp": "2025-10-23T19:00:00"
}
```

### Cache Metrics

```bash
# Cache performansı
curl http://localhost:8001/api/v1/cache/stats

# Response
{
  "total_recipes": 1500,      # Toplam unique tarif
  "total_accesses": 15000,    # Toplam erişim
  "cache_enabled": true,
  "ai_enabled": true
}

# Cache hit rate: 15000/1500 = 10x
# Her tarif ortalama 10 kez istenmiş
```

---

## 💡 Best Practices

### 1. Cache Kullan
```javascript
// ✅ İyi
const recipe = await parseRecipe(url);  // Cache'den gelir

// ❌ Kötü
// Her seferinde yeniden parse etme
```

### 2. AI'yi Akıllıca Kullan
```javascript
// ✅ İyi: İlk istekte AI, sonra cache
if (isFirstTime) {
  recipe = await parseRecipe(url, true);  // AI
} else {
  recipe = await parseRecipe(url, false); // Cache
}

// ❌ Kötü: Her istekte AI
recipe = await parseRecipe(url, true);  // Pahalı!
```

### 3. Error Handling
```javascript
// ✅ İyi
try {
  const recipe = await parseRecipe(url, useAI);
  return recipe;
} catch (error) {
  if (useAI) {
    // AI başarısız, regex'e düş
    return await parseRecipe(url, false);
  }
  throw error;
}
```

### 4. Rate Limiting (Mobil App)
```javascript
// Kullanıcı başına limit
const MAX_REQUESTS_PER_DAY = 100;

if (userRequestCount >= MAX_REQUESTS_PER_DAY) {
  throw new Error('Günlük limit aşıldı');
}
```

---

## 🎓 Öğrenme Kaynakları

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [MongoDB Motor Docs](https://motor.readthedocs.io/)
- [OpenAI API Docs](https://platform.openai.com/docs)
- [Instaloader Docs](https://instaloader.github.io/)
