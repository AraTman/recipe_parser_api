#!/usr/bin/env python3
"""
Production Recipe Parser API
Instagram, TikTok, YouTube Shorts destekli tarif çıkarma API'si
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator
from typing import List, Optional, Dict
import re
import instaloader
import requests
from datetime import datetime
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import hashlib
import json
import asyncio
import google.generativeai as genai

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Recipe Parser API",
    description="Instagram, TikTok, YouTube Shorts'tan tarif çıkarma API'si (MongoDB cache + AI parsing)",
    version="2.0.0"
)

# MongoDB connection
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "recipe_parser")

# Proxy settings (optional)
PROXY_URL = os.getenv("PROXY_URL", "")  # Format: http://user:pass@host:port or http://host:port
PROXY_ENABLED = bool(PROXY_URL)

# n8n webhook (optional)
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "")

# Google AI (Gemini) settings
GOOGLE_AI_API_KEY = os.getenv("GOOGLE_AI_API_KEY", "")
USE_AI_PARSING = os.getenv("USE_AI_PARSING", "true").lower() == "true"

mongo_client = None
db = None

# CORS - Mobil app için
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Production'da specific domain'ler ekle
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== MODELS ====================

class Ingredient(BaseModel):
    item: str
    amount: str
    unit: Optional[str] = None

class RecipeStep(BaseModel):
    order: int
    text: str
    ingredients: Optional[List[str]] = None  # Bu adımda kullanılan malzemeler
    duration: Optional[str] = None
    tip: Optional[str] = None

class Recipe(BaseModel):
    title: str
    description: Optional[str] = None
    ingredients: List[Ingredient]
    steps: List[RecipeStep]
    total_duration: Optional[str] = None
    prep_time: Optional[str] = None
    cook_time: Optional[str] = None
    difficulty: Optional[str] = None
    servings: Optional[str] = None
    calories: Optional[str] = None
    source_url: str
    source_platform: str  # instagram, tiktok, youtube
    video_duration: Optional[float] = None
    thumbnail_url: Optional[str] = None
    author_username: str
    author_name: Optional[str] = None
    likes: Optional[int] = None
    comments: Optional[int] = None
    hashtags: Optional[List[str]] = None
    created_at: str

class RecipeRequest(BaseModel):
    url: str
    language: Optional[str] = "tr"  # tr, en, de, fr, es, ar, etc.
    
    @field_validator('url')
    @classmethod
    def validate_url(cls, v):
        if not any(platform in v.lower() for platform in ['instagram.com', 'tiktok.com', 'youtube.com', 'youtu.be']):
            raise ValueError('Sadece Instagram, TikTok veya YouTube linkleri desteklenir')
        return v
    
    @field_validator('language')
    @classmethod
    def validate_language(cls, v):
        # ISO 639-1 dil kodları
        supported_languages = ['tr', 'en', 'de', 'fr', 'es', 'it', 'ar', 'ru', 'zh', 'ja', 'ko']
        if v and v not in supported_languages:
            raise ValueError(f'Desteklenen diller: {", ".join(supported_languages)}')
        return v or "tr"

class RecipeResponse(BaseModel):
    success: bool
    recipe: Optional[Recipe] = None
    error: Optional[str] = None
    message: Optional[str] = None
    parsed_with_ai: bool = False  # AI ile mi parse edildi?

class HealthResponse(BaseModel):
    status: str
    version: str
    supported_platforms: List[str]
    timestamp: str


# ==================== SCRAPERS ====================

class InstagramScraper:
    """Instagram scraper with proxy support"""
    
    def __init__(self, proxy_url: Optional[str] = None):
        self.proxy_url = proxy_url
        
        # Instaloader proxy ayarları
        loader_kwargs = {
            'download_videos': False,
            'download_video_thumbnails': False,
            'download_geotags': False,
            'download_comments': False,
            'save_metadata': False,
            'compress_json': False,
            'post_metadata_txt_pattern': '',
            'sleep': True,
            'quiet': True,
        }
        
        self.loader = instaloader.Instaloader(**loader_kwargs)
        
        # Proxy ayarla
        if proxy_url:
            self.loader.context._session.proxies = {
                'http': proxy_url,
                'https': proxy_url
            }
            print(f"🔒 Instagram scraper proxy kullanıyor: {proxy_url}")
    
    def extract_shortcode(self, url: str) -> Optional[str]:
        patterns = [
            r'instagram\.com/p/([A-Za-z0-9_-]+)',
            r'instagram\.com/reel/([A-Za-z0-9_-]+)',
            r'instagram\.com/tv/([A-Za-z0-9_-]+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def scrape(self, url: str) -> Dict:
        shortcode = self.extract_shortcode(url)
        if not shortcode:
            raise ValueError('Geçersiz Instagram URL')
        
        post = instaloader.Post.from_shortcode(self.loader.context, shortcode)
        
        return {
            'caption': post.caption if post.caption else '',
            'likes': post.likes if hasattr(post, 'likes') else 0,
            'comments': post.comments if hasattr(post, 'comments') else 0,
            'is_video': post.is_video,
            'video_duration': post.video_duration if post.is_video else None,
            'owner_username': post.owner_username,
            'owner_full_name': post.owner_profile.full_name if post.owner_profile else None,
            'date': post.date_utc.strftime('%Y-%m-%d %H:%M:%S'),
            'thumbnail_url': post.url,
        }


class TikTokScraper:
    """TikTok scraper (API-based) with proxy support"""
    
    def __init__(self, proxy_url: Optional[str] = None):
        self.proxy_url = proxy_url
        self.proxies = {'http': proxy_url, 'https': proxy_url} if proxy_url else None
    
    def extract_video_id(self, url: str) -> Optional[str]:
        patterns = [
            r'tiktok\.com/@[\w.-]+/video/(\d+)',
            r'tiktok\.com/v/(\d+)',
            r'vm\.tiktok\.com/([\w-]+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def scrape(self, url: str) -> Dict:
        """
        TikTok scraping için external API kullan
        Alternatif: TikTok Scraper API (RapidAPI)
        """
        # Basit placeholder - Production'da API key ile çalışacak
        video_id = self.extract_video_id(url)
        if not video_id:
            raise ValueError('Geçersiz TikTok URL')
        
        # TODO: TikTok API entegrasyonu
        # Şimdilik mock data dön
        return {
            'caption': 'TikTok tarifi (API entegrasyonu gerekli)',
            'likes': 0,
            'comments': 0,
            'is_video': True,
            'video_duration': 30.0,
            'owner_username': 'tiktok_user',
            'owner_full_name': 'TikTok User',
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'thumbnail_url': None,
        }


class YouTubeScraper:
    """YouTube Shorts scraper with proxy support"""
    
    def __init__(self, proxy_url: Optional[str] = None):
        self.proxy_url = proxy_url
        self.proxies = {'http': proxy_url, 'https': proxy_url} if proxy_url else None
    
    def extract_video_id(self, url: str) -> Optional[str]:
        patterns = [
            r'youtube\.com/shorts/([A-Za-z0-9_-]+)',
            r'youtu\.be/([A-Za-z0-9_-]+)',
            r'youtube\.com/watch\?v=([A-Za-z0-9_-]+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def scrape(self, url: str) -> Dict:
        """
        YouTube scraping için yt-dlp kullan
        """
        video_id = self.extract_video_id(url)
        if not video_id:
            raise ValueError('Geçersiz YouTube URL')
        
        try:
            import yt_dlp
            
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,
            }
            
            # Proxy ekle
            if self.proxy_url:
                ydl_opts['proxy'] = self.proxy_url
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                return {
                    'caption': info.get('description', ''),
                    'likes': info.get('like_count', 0),
                    'comments': info.get('comment_count', 0),
                    'is_video': True,
                    'video_duration': info.get('duration', 0),
                    'owner_username': info.get('uploader', ''),
                    'owner_full_name': info.get('uploader', ''),
                    'date': info.get('upload_date', datetime.now().strftime('%Y%m%d')),
                    'thumbnail_url': info.get('thumbnail', None),
                }
        except ImportError:
            # yt-dlp yüklü değilse mock data
            return {
                'caption': 'YouTube tarifi (yt-dlp gerekli: pip install yt-dlp)',
                'likes': 0,
                'comments': 0,
                'is_video': True,
                'video_duration': 60.0,
                'owner_username': 'youtube_user',
                'owner_full_name': 'YouTube User',
                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'thumbnail_url': None,
            }


# ==================== AI PARSER (Google Gemini) ====================

class AIRecipeParser:
    """Google Gemini ile tarif parsing"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.model = None
        if api_key:
            try:
                genai.configure(api_key=api_key)
                # Gemini Pro modeli kullan (ücretsiz ve stabil)
                self.model = genai.GenerativeModel('gemini-2.5-flash')
            except Exception as e:
                print(f"⚠️ Google AI initialization failed: {e}")
    
    def parse_recipe(self, raw_text: str, title: str = "", target_language: str = "tr") -> Dict:
        """
        Google Gemini ile tarifi parse et ve istenen dile çevir
        
        Args:
            raw_text: Ham tarif metni
            title: Tarif başlığı
            target_language: Hedef dil kodu (tr, en, de, fr, es, etc.)
        """
        if not self.model:
            raise ValueError("Google AI API key not configured")
        
        # Dil isimleri
        language_names = {
            'tr': 'Türkçe',
            'en': 'English',
            'de': 'Deutsch',
            'fr': 'Français',
            'es': 'Español',
            'it': 'Italiano',
            'ar': 'العربية',
            'ru': 'Русский',
            'zh': '中文',
            'ja': '日本語',
            'ko': '한국어'
        }
        
        target_lang_name = language_names.get(target_language, 'Türkçe')
        
        prompt = f"""Sen bir yemek tarifi uzmanısın. Aşağıdaki tarif metnini analiz et, yapılandırılmış formata çevir ve {target_lang_name} diline çevir.

=== TARİF METNİ ===
Başlık: {title}

{raw_text}

=== GÖREV ===
1. Tarif metnini analiz et ve anla
2. Türkçe ve İngilizce karışık ise temizle
3. Malzemeleri standartlaştır (miktar, birim, isim)
4. Adımları net ve sıralı hale getir
5. **ÖNEMLİ: Her adımda kullanılan malzemeleri "ingredients" listesinde belirt**
6. Gereksiz tekrarları temizle
7. Tahmini süre ve zorluk belirle
8. **TÜM METNİ {target_lang_name} DİLİNE ÇEVİR**

=== ÖNEMLİ ===
- Başlık, açıklama, malzemeler, adımlar ve ipuçları {target_lang_name} dilinde olmalı
- Miktarlar ve birimler hedef dilin standartlarına uygun olmalı
- Zorluk seviyesi: {target_lang_name} dilinde (örn: Easy/Kolay, Medium/Orta, Hard/Zor)

=== ÇIKTI FORMATI ===
Sadece JSON formatında döndür:

{{
  "title": "Kısa ve net başlık ({target_lang_name})",
  "description": "2-3 cümle açıklama ({target_lang_name})",
  "ingredients": [
    {{"item": "Malzeme adı ({target_lang_name})", "amount": "Miktar", "unit": "Birim ({target_lang_name})"}}
  ],
  "steps": [
    {{"order": 1, "text": "Adım açıklaması ({target_lang_name})", "ingredients": ["Malzeme 1", "Malzeme 2"], "duration": "Süre (opsiyonel)"}}
  ],
  "total_duration": "Toplam süre ({target_lang_name})",
  "prep_time": "Hazırlık süresi ({target_lang_name})",
  "cook_time": "Pişirme süresi ({target_lang_name})",
  "difficulty": "Kolay/Orta/Zor ({target_lang_name})",
  "servings": "Porsiyon ({target_lang_name})",
  "tips": ["İpucu 1 ({target_lang_name})", "İpucu 2 ({target_lang_name})"]
}}

Sadece JSON döndür, başka açıklama ekleme."""

        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=4096,  # Daha uzun tarifler için artırıldı
                )
            )
            
            # JSON parse et
            result_text = response.text.strip()
            # Markdown code block temizle
            result_text = re.sub(r'```json\n?', '', result_text)
            result_text = re.sub(r'```\n?', '', result_text)
            result_text = result_text.strip()
            
            parsed = json.loads(result_text)
            return parsed
            
        except json.JSONDecodeError as e:
            print(f"⚠️ AI JSON parse error: {e}")
            print(f"Raw response: {response.text[:500]}")
            raise ValueError(f"AI yanıtı JSON formatında değil: {e}")
        except Exception as e:
            print(f"⚠️ AI parsing error: {e}")
            raise ValueError(f"AI parsing hatası: {e}")


# ==================== DATABASE HELPER ====================

class DatabaseHelper:
    """MongoDB cache yönetimi"""
    
    def __init__(self, db):
        self.db = db
        self.collection = db.recipes if db is not None else None
    
    def get_url_hash(self, url: str) -> str:
        """URL'den unique hash oluştur"""
        return hashlib.md5(url.encode()).hexdigest()
    
    async def get_cached_recipe(self, url: str) -> Optional[Dict]:
        """Cache'den tarif getir"""
        if self.collection is None:
            return None
        
        url_hash = self.get_url_hash(url)
        cached = await self.collection.find_one({"url_hash": url_hash})
        
        if cached:
            # MongoDB ObjectId'yi kaldır
            cached.pop('_id', None)
            return cached
        
        return None
    
    async def save_recipe(self, url: str, recipe_data: Dict) -> bool:
        """Tarifi cache'e kaydet"""
        if self.collection is None:
            return False
        
        url_hash = self.get_url_hash(url)
        
        # Önce var mı kontrol et
        existing = await self.collection.find_one({"url_hash": url_hash})
        
        if existing:
            # Varsa sadece recipe'yi güncelle ve access_count'u artır
            await self.collection.update_one(
                {"url_hash": url_hash},
                {
                    "$set": {
                        "recipe": recipe_data,
                        "cached_at": datetime.now().isoformat()
                    },
                    "$inc": {"access_count": 1}
                }
            )
        else:
            # Yoksa yeni döküman ekle
            document = {
                "url_hash": url_hash,
                "url": url,
                "recipe": recipe_data,
                "cached_at": datetime.now().isoformat(),
                "access_count": 1
            }
            await self.collection.insert_one(document)
        
        return True
    
    async def get_stats(self) -> Dict:
        """Cache istatistikleri"""
        if self.collection is None:
            return {"total_recipes": 0, "total_accesses": 0}
        
        total = await self.collection.count_documents({})
        pipeline = [
            {"$group": {"_id": None, "total_accesses": {"$sum": "$access_count"}}}
        ]
        result = await self.collection.aggregate(pipeline).to_list(1)
        total_accesses = result[0]["total_accesses"] if result else 0
        
        return {
            "total_recipes": total,
            "total_accesses": total_accesses
        }


# ==================== RECIPE PARSER ====================

class RecipeParser:
    """Tarif metnini parse eden sınıf"""
    
    def parse_ingredients(self, text: str) -> List[Ingredient]:
        """Malzemeleri parse et"""
        ingredients = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or len(line) < 3:
                continue
            
            # Miktar + birim + malzeme pattern'leri
            patterns = [
                # "3 yumurta", "1 su bardağı şeker"
                r'^(\d+(?:[.,]\d+)?)\s*(adet|su bardağı|yemek kaşığı|çay kaşığı|tatlı kaşığı|paket|kg|gr|g|ml|lt|l)?\s*(.+)$',
                # "Yarım su bardağı", "Bir avuç"
                r'^(Yarım|Bir|İki|Üç|Dört|Beş)\s*(su bardağı|yemek kaşığı|çay kaşığı|paket|avuç|tutam)?\s*(.+)$',
                # "1/2 su bardağı"
                r'^(\d+/\d+)\s*(su bardağı|yemek kaşığı|çay kaşığı|paket)?\s*(.+)$',
            ]
            
            for pattern in patterns:
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    amount = match.group(1)
                    unit = match.group(2) if match.group(2) else None
                    item = match.group(3).strip()
                    
                    # Temizle
                    item = re.sub(r'^(adet|tane)\s+', '', item, flags=re.IGNORECASE)
                    item = re.sub(r'\s+', ' ', item)
                    
                    if len(item) > 2:  # Çok kısa malzemeler atla
                        ingredients.append(Ingredient(
                            item=item,
                            amount=amount,
                            unit=unit
                        ))
                    break
        
        return ingredients
    
    def parse_steps(self, text: str) -> List[RecipeStep]:
        """Adımları parse et - gelişmiş versiyon"""
        steps = []
        lines = text.split('\n')
        order = 1
        
        # Türkçe yemek fiilleri
        action_verbs = [
            'karıştır', 'ekle', 'dök', 'pişir', 'çırp', 'ısıt', 'doğra',
            'ren', 'kes', 'yoğur', 'beklet', 'dinlendir', 'al', 'koy',
            'ilave', 'hazırla', 'yıka', 'temizle', 'soy', 'dilimle',
            'kavur', 'haşla', 'kaynat', 'kızart', 'servis', 'süsle',
            'tat', 'kontrol', 'çevir', 'karış', 'yap', 'oluştur',
            'geçir', 'oturt', 'tut', 'aç', 'kapat', 'doldur', 'kaynay',
            'soğu', 'eritil', 'düzleştir', 'kaldır'
        ]
        
        # Malzeme başlıkları - bunları atla
        ingredient_headers = [
            'malzemeler', 'malzeme:', 'için malzemeler', 'tabanı için',
            'dolgu için', 'sos için', 'üzeri için', 'sosu için'
        ]
        
        # Miktar ifadeleri - bunlar malzeme satırı
        quantity_patterns = [
            r'^\d+\s*(adet|su bardağı|yemek kaşığı|çay kaşığı|paket|kg|gr|g|ml|lt|l)',
            r'^(yarım|bir|iki|üç|dört|beş)\s*(su bardağı|yemek kaşığı|çay kaşığı)',
            r'^\d+/\d+\s*'
        ]
        
        for line in lines:
            line = line.strip()
            
            # Çok kısa satırları atla
            if not line or len(line) < 10:
                continue
            
            line_lower = line.lower()
            
            # Malzeme başlıklarını atla
            if any(header in line_lower for header in ingredient_headers):
                continue
            
            # Miktar içeren satırları atla (malzeme listesi)
            is_ingredient = False
            for pattern in quantity_patterns:
                if re.match(pattern, line, re.IGNORECASE):
                    is_ingredient = True
                    break
            
            if is_ingredient:
                continue
            
            # Sadece parantez içi ipucu olan satırları atla
            if line.startswith('(') and line.endswith(')'):
                continue
            
            # Fiil içeren ve yeterince uzun cümleler = adım
            if any(verb in line_lower for verb in action_verbs):
                # Uzun paragrafları cümlelere böl
                sentences = self._split_long_paragraph(line)
                
                for sentence in sentences:
                    sentence = sentence.strip()
                    if len(sentence) < 15:  # Çok kısa cümleleri atla
                        continue
                    
                    # Süre bilgisi
                    duration = self._extract_duration(sentence)
                    
                    # İpucu bilgisi (parantez içi)
                    tip = self._extract_tip(sentence)
                    
                    steps.append(RecipeStep(
                        order=order,
                        text=sentence,
                        duration=duration,
                        tip=tip
                    ))
                    order += 1
        
        return steps
    
    def _split_long_paragraph(self, text: str) -> List[str]:
        """Uzun paragrafları mantıklı cümlelere böl"""
        # Eğer çok uzun değilse bölme
        if len(text) < 150:
            return [text]
        
        sentences = []
        
        # Nokta ile bölme (ama sayılardan sonraki noktaları atla)
        parts = re.split(r'\.(?=\s+[A-ZÇĞIÖŞÜ])', text)
        
        for part in parts:
            part = part.strip()
            if not part:
                continue
            
            # Hala çok uzunsa virgüllerden böl
            if len(part) > 200:
                subparts = part.split('.')
                for subpart in subparts:
                    subpart = subpart.strip()
                    if len(subpart) > 30:
                        sentences.append(subpart)
            else:
                sentences.append(part)
        
        return sentences if sentences else [text]
    
    def _extract_duration(self, text: str) -> Optional[str]:
        """Metinden süre bilgisini çıkar"""
        # Süre pattern'leri
        patterns = [
            r'(\d+)\s*-?\s*(\d+)?\s*(dakika|dk|saat|saniye)',
            r'(\d+)\s*(gece|saat)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return None
    
    def _extract_tip(self, text: str) -> Optional[str]:
        """Metinden ipucu bilgisini çıkar (parantez içi)"""
        tip_match = re.search(r'\(([^)]+)\)', text)
        if tip_match:
            tip = tip_match.group(1).strip()
            # Sadece anlamlı ipuçlarını al
            if len(tip) > 10 and not tip[0].isdigit():
                return tip
        return None
    
    def extract_title(self, text: str) -> str:
        """Tarif başlığını çıkar"""
        lines = text.split('\n')
        
        for line in lines[:5]:
            line = line.strip()
            # Kısa, anlamlı satırlar
            if 5 < len(line) < 60 and line and not line[0].isdigit():
                # Emoji ve özel karakterleri temizle
                title = re.sub(r'[^\w\s]', '', line, flags=re.UNICODE)
                title = re.sub(r'\s+', ' ', title).strip()
                if title and len(title) > 5:
                    return title
        
        return "Tarif"
    
    def extract_difficulty(self, text: str) -> str:
        """Zorluk seviyesi belirle"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['kolay', 'basit', 'pratik']):
            return "Kolay"
        elif any(word in text_lower for word in ['zor', 'profesyonel', 'ileri']):
            return "Zor"
        else:
            return "Orta"
    
    def extract_servings(self, text: str) -> Optional[str]:
        """Porsiyon bilgisi çıkar"""
        patterns = [
            r'(\d+)\s*kişilik',
            r'(\d+)\s*porsiyon',
            r'(\d+)\s*servis',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return f"{match.group(1)} kişilik"
        
        return None


# ==================== MAIN SERVICE ====================

class RecipeService:
    """Ana tarif servisi"""
    
    def __init__(self, db=None, proxy_url: Optional[str] = None, ai_parser: Optional[AIRecipeParser] = None):
        self.instagram_scraper = InstagramScraper(proxy_url=proxy_url)
        self.tiktok_scraper = TikTokScraper(proxy_url=proxy_url)
        self.youtube_scraper = YouTubeScraper(proxy_url=proxy_url)
        # Regex parser kaldırıldı - sadece AI parsing
        self.ai_parser = ai_parser
        self.db_helper = DatabaseHelper(db)
        self.proxy_url = proxy_url
    
    def detect_platform(self, url: str) -> str:
        """Platform tespit et"""
        url_lower = url.lower()
        if 'instagram.com' in url_lower:
            return 'instagram'
        elif 'tiktok.com' in url_lower or 'vm.tiktok.com' in url_lower:
            return 'tiktok'
        elif 'youtube.com' in url_lower or 'youtu.be' in url_lower:
            return 'youtube'
        else:
            raise ValueError('Desteklenmeyen platform')
    
    def scrape_content(self, url: str, platform: str) -> Dict:
        """Platform'a göre içerik çek"""
        if platform == 'instagram':
            return self.instagram_scraper.scrape(url)
        elif platform == 'tiktok':
            return self.tiktok_scraper.scrape(url)
        elif platform == 'youtube':
            return self.youtube_scraper.scrape(url)
        else:
            raise ValueError('Desteklenmeyen platform')
    
    async def parse_recipe(self, url: str, use_ai: bool = None, language: str = "tr") -> tuple[Recipe, bool]:
        """URL'den tarif çıkar (cache destekli, AI parsing opsiyonel, çok dilli)
        
        Args:
            url: Tarif URL'i
            use_ai: AI parsing kullan (None = otomatik)
            language: Hedef dil kodu (tr, en, de, fr, es, etc.)
        
        Returns:
            tuple[Recipe, bool]: (recipe, was_parsed_with_ai)
        """
        
        # use_ai parametresi verilmemişse global ayarı kullan
        if use_ai is None:
            use_ai = USE_AI_PARSING and self.ai_parser is not None
        
        # 1. Cache kontrolü (dil bazlı)
        cache_key = f"{url}_{language}"
        cached = await self.db_helper.get_cached_recipe(cache_key)
        if cached:
            print(f"✅ Cache'den döndürüldü: {url} ({language})")
            # Cache'den gelen için AI flag'i bilinmiyor, False döndür
            return Recipe(**cached['recipe']), False
        
        # 2. Platform tespit
        platform = self.detect_platform(url)
        
        # 3. İçerik çek
        content = self.scrape_content(url, platform)
        caption = content['caption']
        
        # 4. Parse et
        if use_ai and self.ai_parser:
            # AI ile parse et
            print(f"🤖 Google AI ile parsing: {url} (dil: {language})")
            try:
                ai_result = self.ai_parser.parse_recipe(
                    caption, 
                    content.get('owner_username', ''),
                    target_language=language
                )
                
                # AI sonucunu Recipe formatına çevir
                ingredients = [
                    Ingredient(
                        item=ing.get('item', ''),
                        amount=ing.get('amount'),
                        unit=ing.get('unit')
                    ) for ing in ai_result.get('ingredients', [])
                ]
                
                steps = [
                    RecipeStep(
                        order=step.get('order', i+1),
                        text=step.get('text', ''),
                        ingredients=step.get('ingredients'),  # Her adımda kullanılan malzemeler
                        duration=step.get('duration'),
                        tip=None
                    ) for i, step in enumerate(ai_result.get('steps', []))
                ]
                
                title = ai_result.get('title', 'Tarif')
                description = ai_result.get('description', caption[:200] + '...' if len(caption) > 200 else caption)
                total_duration = ai_result.get('total_duration')
                prep_time = ai_result.get('prep_time')
                cook_time = ai_result.get('cook_time')
                difficulty = ai_result.get('difficulty', 'Orta')
                servings = ai_result.get('servings')
                
            except Exception as e:
                error_msg = str(e)
                # Rate limit hatası kontrolü
                if "429" in error_msg or "quota" in error_msg.lower() or "rate" in error_msg.lower():
                    print(f"⚠️ AI rate limit aşıldı")
                    raise HTTPException(
                        status_code=429,
                        detail="Google AI rate limit aşıldı. Lütfen birkaç dakika sonra tekrar deneyin."
                    )
                else:
                    print(f"❌ AI parsing başarısız: {e}")
                    raise HTTPException(
                        status_code=500,
                        detail=f"Tarif AI ile parse edilemedi: {str(e)}"
                    )
        
        if not self.ai_parser:
            raise HTTPException(
                status_code=503,
                detail="AI parsing servisi yapılandırılmamış. GOOGLE_AI_API_KEY gerekli."
            )
        
        # 5. Hashtag'ler
        hashtags = re.findall(r'#(\w+)', caption)
        
        # 6. Recipe oluştur
        recipe = Recipe(
            title=title,
            description=description,
            ingredients=ingredients,
            steps=steps,
            total_duration=total_duration,
            prep_time=prep_time,
            cook_time=cook_time,
            difficulty=difficulty,
            servings=servings,
            source_url=url,
            source_platform=platform,
            video_duration=content.get('video_duration'),
            thumbnail_url=content.get('thumbnail_url'),
            author_username=content['owner_username'],
            author_name=content.get('owner_full_name'),
            likes=content.get('likes'),
            comments=content.get('comments'),
            hashtags=hashtags if hashtags else None,
            created_at=datetime.now().isoformat()
        )
        
        # 7. Cache'e kaydet (dil bazlı)
        cache_key = f"{url}_{language}"
        await self.db_helper.save_recipe(cache_key, recipe.model_dump())
        print(f"💾 Cache'e kaydedildi: {url} ({language})")
        
        # use_ai değişkeni son durumu gösterir (AI başarısız olduysa False'a dönmüş olur)
        return recipe, use_ai


# Service will be initialized on startup
service = None


# ==================== STARTUP/SHUTDOWN ====================

@app.on_event("startup")
async def startup_db_client():
    """MongoDB bağlantısını başlat"""
    global mongo_client, db, service
    
    try:
        # MongoDB bağlantısı timeout ile (5 saniye)
        mongo_client = AsyncIOMotorClient(
            MONGODB_URL,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000
        )
        db = mongo_client[MONGODB_DB_NAME]
        
        # Test connection with timeout
        await asyncio.wait_for(db.command('ping'), timeout=5.0)
        print(f"✅ MongoDB bağlantısı başarılı: {MONGODB_DB_NAME}")
        
        # Create index for faster lookups (non-blocking)
        try:
            await asyncio.wait_for(
                db.recipes.create_index("url_hash", unique=True),
                timeout=3.0
            )
        except asyncio.TimeoutError:
            print("⚠️ Index oluşturma timeout, devam ediliyor...")
        
    except (Exception, asyncio.TimeoutError) as e:
        print(f"⚠️ MongoDB bağlantısı başarısız: {e}")
        print("⚠️ Cache olmadan devam ediliyor...")
        db = None
        mongo_client = None
    
    # Initialize AI parser if API key exists
    ai_parser = None
    if GOOGLE_AI_API_KEY:
        ai_parser = AIRecipeParser(api_key=GOOGLE_AI_API_KEY)
        # API key'in son 5 hanesini göster (güvenlik için)
        key_preview = f"...{GOOGLE_AI_API_KEY[-5:]}" if len(GOOGLE_AI_API_KEY) >= 5 else "***"
        print(f"🤖 Google AI Parser başlatıldı (AI Parsing: {USE_AI_PARSING}, Key: {key_preview})")
    else:
        print("⚠️ Google AI API key bulunamadı, regex parsing kullanılacak")
    
    # Initialize service with DB, proxy and AI parser
    service = RecipeService(
        db=db, 
        proxy_url=PROXY_URL if PROXY_ENABLED else None,
        ai_parser=ai_parser
    )
    print(f"🚀 RecipeService başlatıldı (Proxy: {PROXY_ENABLED}, AI: {ai_parser is not None})")


@app.on_event("shutdown")
async def shutdown_db_client():
    """MongoDB bağlantısını kapat"""
    global mongo_client
    if mongo_client:
        mongo_client.close()
        print("👋 MongoDB bağlantısı kapatıldı")


# ==================== API ENDPOINTS ====================

@app.get("/", response_model=HealthResponse)
async def root():
    """Health check ve API bilgisi"""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        supported_platforms=["Instagram", "TikTok", "YouTube Shorts"],
        timestamp=datetime.now().isoformat()
    )

@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        supported_platforms=["Instagram", "TikTok", "YouTube Shorts"],
        timestamp=datetime.now().isoformat()
    )

@app.post("/api/v1/parse-recipe", response_model=RecipeResponse)
async def parse_recipe(request: RecipeRequest):
    """
    Instagram, TikTok veya YouTube Shorts URL'den tarif çıkar (Çok Dilli)
    
    **Özellikler:**
    - ✅ Google AI (Gemini) ile akıllı parsing
    - ✅ Çok dilli destek (11 dil)
    - ✅ MongoDB cache (dil bazlı)
    - ✅ Otomatik çeviri
    
    **Desteklenen Platformlar:**
    - Instagram (Reels, Posts)
    - TikTok
    - YouTube Shorts
    
    **Desteklenen Diller:**
    - tr: Türkçe (varsayılan)
    - en: English
    - de: Deutsch
    - fr: Français
    - es: Español
    - it: Italiano
    - ar: العربية
    - ru: Русский
    - zh: 中文
    - ja: 日本語
    - ko: 한국어
    
    **Örnek Request:**
    ```json
    {
        "url": "https://www.instagram.com/reel/ABC123/",
        "language": "en"
    }
    ```
    
    **Örnek Response:**
    ```json
    {
        "success": true,
        "recipe": {
            "title": "Carrot Cake",
            "description": "A delicious carrot cake recipe...",
            "ingredients": [
                {"item": "Carrots", "amount": "2", "unit": "cups"}
            ],
            "steps": [
                {"order": 1, "text": "Preheat the oven to 180°C..."}
            ],
            "difficulty": "Easy",
            ...
        },
        "parsed_with_ai": true,
        "message": "Tarif başarıyla çıkarıldı (AI ile, dil: en)"
    }
    ```
    """
    try:
        recipe, parsed_with_ai = await service.parse_recipe(
            url=request.url,
            language=request.language
        )
        
        return RecipeResponse(
            success=True,
            recipe=recipe,
            parsed_with_ai=parsed_with_ai,
            message=f"Tarif başarıyla çıkarıldı ({'AI' if parsed_with_ai else 'Regex'} ile, dil: {request.language})"
        )
        
    except ValueError as e:
        return RecipeResponse(
            success=False,
            error=str(e),
            message="Geçersiz URL veya desteklenmeyen platform"
        )
    except Exception as e:
        return RecipeResponse(
            success=False,
            error=str(e),
            message="Tarif çıkarılırken hata oluştu"
        )


@app.get("/api/v1/supported-platforms")
async def supported_platforms():
    """Desteklenen platformları listele"""
    return {
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


@app.get("/api/v1/cache/stats")
async def cache_stats():
    """
    Cache istatistiklerini getir
    
    **Response:**
    ```json
    {
        "total_recipes": 150,
        "total_accesses": 1250,
        "cache_enabled": true
    }
    ```
    """
    stats = await service.db_helper.get_stats()
    return {
        **stats,
        "cache_enabled": db is not None
    }


if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting Recipe Parser API...")
    print("📱 Supported: Instagram, TikTok, YouTube Shorts")
    print("🌐 Server: http://0.0.0.0:8001")
    print("📖 Docs: http://0.0.0.0:8001/docs")
    
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
