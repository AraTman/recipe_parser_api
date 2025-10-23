# 🍳 Recipe Helper - Mobil App Konsepti

## 📱 Ekranlar

### 1. Ana Ekran (Home)
```
┌─────────────────────────┐
│  🍳 Recipe Helper       │
│                         │
│  ┌───────────────────┐  │
│  │ Instagram Link    │  │
│  │ Yapıştır...       │  │
│  └───────────────────┘  │
│                         │
│  [📋 Yapıştır ve Çözümle]│
│                         │
│  ─────────────────────  │
│                         │
│  📚 Son Tarifler        │
│  ┌─────┐ ┌─────┐       │
│  │ 🥘  │ │ 🍰  │       │
│  │Kek  │ │Çorba│       │
│  └─────┘ └─────┘       │
└─────────────────────────┘
```

### 2. Tarif Detay Ekranı
```
┌─────────────────────────┐
│ ← Havuçlu Tarçınlı Kek  │
│                         │
│ [▶️ Video Oynat]        │
│ 🎬 13.9 saniye          │
│                         │
│ ⏱️ 50 dakika | 🔥 Orta  │
│                         │
│ 📝 Malzemeler (12)      │
│ ☐ 3 adet Yumurta        │
│ ☐ 1 su bardağı Şeker    │
│ ☐ 1 su bardağı Süt      │
│ ...                     │
│                         │
│ [🚀 Pişirmeye Başla]    │
└─────────────────────────┘
```

### 3. Adım Adım Rehber
```
┌─────────────────────────┐
│ Adım 2/8                │
│ ━━━━━━━━━━━━━━━━━━━━━━  │
│                         │
│ 🥄 Sütü ve yağı ekleyin │
│                         │
│ [▶️ Video Göster]       │
│                         │
│ ⏱️ Timer: 00:00         │
│ [⏰ Zamanlayıcı Başlat] │
│                         │
│ [◀️ Geri]  [İleri ▶️]   │
│                         │
│ [🔊 Sesli Oku]          │
└─────────────────────────┘
```

### 4. Alışveriş Listesi
```
┌─────────────────────────┐
│ 🛒 Alışveriş Listesi    │
│                         │
│ Havuçlu Kek için:       │
│ ☐ 3 adet Yumurta        │
│ ☐ 1 kg Havuç            │
│ ☐ 200g Ceviz            │
│                         │
│ [📤 Paylaş]             │
│ [✅ Tümünü İşaretle]    │
└─────────────────────────┘
```

## 🎨 Özellikler

### Temel (MVP)
- ✅ Instagram link yapıştır
- ✅ Tarif otomatik parse
- ✅ Malzeme listesi
- ✅ Adım adım rehber
- ✅ Timer/Zamanlayıcı
- ✅ Sesli okuma (TTS)

### Premium
- ⭐ Video senkronizasyon
- ⭐ Porsiyon hesaplama
- ⭐ Alışveriş listesi
- ⭐ Favori tarifler
- ⭐ Offline mod
- ⭐ Kendi tariflerini ekle

## 🔧 Teknik Stack

### Frontend (Mobil)
```
React Native / Flutter
- Navigation: React Navigation
- State: Redux / Zustand
- UI: React Native Paper
- TTS: react-native-tts
- Video: react-native-video
```

### Backend (API)
```
FastAPI (Python)
- Instagram Scraper
- Recipe Parser
- Database: MongoDB
- Cache: Redis
```

### AI/ML
```
OpenAI GPT-4 (Gelişmiş parsing)
- Malzeme extraction
- Adım belirleme
- Zorluk seviyesi
- Porsiyon hesaplama
```

## 📊 Monetization

### Freemium Model
```
Ücretsiz:
- 10 tarif/ay
- Temel özellikler
- Reklamlar

Premium ($4.99/ay):
- Sınırsız tarif
- Video senkronizasyon
- Alışveriş listesi
- Reklamsız
- Offline mod
```

## 🚀 MVP Roadmap

### Faz 1 (2 hafta)
- [x] Instagram scraper
- [ ] Recipe parser API
- [ ] Basit mobil UI
- [ ] Link yapıştır + parse

### Faz 2 (2 hafta)
- [ ] Adım adım rehber
- [ ] Timer özelliği
- [ ] Sesli okuma
- [ ] Favori kaydetme

### Faz 3 (2 hafta)
- [ ] Video entegrasyonu
- [ ] Alışveriş listesi
- [ ] Porsiyon hesaplama
- [ ] Premium özellikler

## 💡 Kullanım Senaryosu

```
1. Kullanıcı Instagram'da yemek videosu görür
2. Linki kopyalar
3. Recipe Helper'ı açar
4. Linki yapıştırır
5. App tarifi parse eder (5 saniye)
6. Malzeme listesini gösterir
7. "Pişirmeye Başla" butonuna basar
8. Adım adım rehber başlar
9. Her adımda:
   - Metin gösterir
   - Sesli okur
   - Timer başlatır
   - Video snippet gösterir (opsiyonel)
10. Tarif tamamlanır! 🎉
```

## 🎯 Hedef Kitle

- 👩‍🍳 Yemek yapmayı seven ama tarif takip etmekte zorlananlar
- 📱 Instagram/TikTok'ta yemek videosu izleyenler
- ⏱️ Pratik çözüm arayanlar
- 🎓 Yeni öğrenenler

## 💰 Pazar Potansiyeli

- 📊 Türkiye'de 50M+ Instagram kullanıcısı
- 🍳 Yemek içeriği en popüler kategorilerden
- 💵 Benzer uygulamalar: Yummly, Tasty, SideChef
- 🎯 Niche: Instagram/TikTok odaklı ilk Türkçe app
