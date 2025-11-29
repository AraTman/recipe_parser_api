#!/usr/bin/env python3
"""
Production Recipe Parser API
Instagram, TikTok, YouTube Shorts destekli tarif çıkarma API'si
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
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
ENABLE_AI_PARSING = os.getenv("ENABLE_AI_PARSING", "false").lower() == "true"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Proxy settings (optional)
PROXY_URL = os.getenv("PROXY_URL", "")  # Format: http://user:pass@host:port or http://host:port
PROXY_ENABLED = bool(PROXY_URL)

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
    use_ai: Optional[bool] = False  # AI-powered parsing kullan
    
    @validator('url')
    def validate_url(cls, v):
        if not any(platform in v.lower() for platform in ['instagram.com', 'tiktok.com', 'youtube.com', 'youtu.be']):
            raise ValueError('Sadece Instagram, TikTok veya YouTube linkleri desteklenir')
        return v

class RecipeResponse(BaseModel):
    success: bool
    recipe: Optional[Recipe] = None
    error: Optional[str] = None
    message: Optional[str] = None

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


# ==================== AI PARSER ====================

class AIRecipeParser:
    """OpenAI GPT ile gelişmiş tarif parsing"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.enabled = bool(api_key)
    
    async def parse_with_ai(self, text: str, platform: str) -> Dict:
        """AI ile tarif parse et"""
        if not self.enabled:
            raise ValueError("OpenAI API key tanımlanmamış")
        
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=self.api_key)
            
            prompt = f"""
Aşağıdaki {platform} tarif metnini analiz et ve JSON formatında döndür:

Metin:
{text}

Çıktı formatı (JSON):
{{
    "title": "Tarif başlığı",
    "ingredients": [
        {{"item": "Malzeme adı", "amount": "Miktar", "unit": "Birim"}},
        ...
    ],
    "steps": [
        {{"order": 1, "text": "Adım açıklaması", "duration": "Süre (varsa)"}},
        ...
    ],
    "total_duration": "Toplam süre",
    "difficulty": "Kolay/Orta/Zor",
    "servings": "Porsiyon bilgisi"
}}

Sadece JSON döndür, başka açıklama ekleme.
"""
            
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Sen bir yemek tarifi analiz uzmanısın. Verilen metinlerden tarif bilgilerini çıkarıyorsun."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            raise ValueError(f"AI parsing hatası: {str(e)}")


# ==================== DATABASE HELPER ====================

class DatabaseHelper:
    """MongoDB cache yönetimi"""
    
    def __init__(self, db):
        self.db = db
        self.collection = db.recipes if db else None
    
    def get_url_hash(self, url: str) -> str:
        """URL'den unique hash oluştur"""
        return hashlib.md5(url.encode()).hexdigest()
    
    async def get_cached_recipe(self, url: str) -> Optional[Dict]:
        """Cache'den tarif getir"""
        if not self.collection:
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
        if not self.collection:
            return False
        
        url_hash = self.get_url_hash(url)
        
        document = {
            "url_hash": url_hash,
            "url": url,
            "recipe": recipe_data,
            "cached_at": datetime.now().isoformat(),
            "access_count": 1
        }
        
        # Upsert: varsa güncelle, yoksa ekle
        await self.collection.update_one(
            {"url_hash": url_hash},
            {
                "$set": document,
                "$inc": {"access_count": 1}
            },
            upsert=True
        )
        
        return True
    
    async def get_stats(self) -> Dict:
        """Cache istatistikleri"""
        if not self.collection:
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
    
    def __init__(self, db=None, openai_api_key: str = "", proxy_url: Optional[str] = None):
        self.instagram_scraper = InstagramScraper(proxy_url=proxy_url)
        self.tiktok_scraper = TikTokScraper(proxy_url=proxy_url)
        self.youtube_scraper = YouTubeScraper(proxy_url=proxy_url)
        self.parser = RecipeParser()
        self.ai_parser = AIRecipeParser(openai_api_key)
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
    
    async def parse_recipe(self, url: str, use_ai: bool = False) -> Recipe:
        """URL'den tarif çıkar (cache + AI destekli)"""
        
        # 1. Cache kontrolü
        cached = await self.db_helper.get_cached_recipe(url)
        if cached:
            print(f"✅ Cache'den döndürüldü: {url}")
            return Recipe(**cached['recipe'])
        
        # 2. Platform tespit
        platform = self.detect_platform(url)
        
        # 3. İçerik çek
        content = self.scrape_content(url, platform)
        caption = content['caption']
        
        # 4. Parse et (AI veya Regex)
        if use_ai and self.ai_parser.enabled:
            print(f"🤖 AI ile parsing: {url}")
            try:
                ai_result = await self.ai_parser.parse_with_ai(caption, platform)
                
                # AI sonucunu Recipe formatına dönüştür
                ingredients = [Ingredient(**ing) for ing in ai_result.get('ingredients', [])]
                steps = [RecipeStep(**step) for step in ai_result.get('steps', [])]
                title = ai_result.get('title', 'Tarif')
                total_duration = ai_result.get('total_duration')
                difficulty = ai_result.get('difficulty', 'Orta')
                servings = ai_result.get('servings')
                
            except Exception as e:
                print(f"⚠️ AI parsing başarısız, regex'e geçiliyor: {e}")
                # AI başarısız olursa regex'e düş
                title = self.parser.extract_title(caption)
                ingredients = self.parser.parse_ingredients(caption)
                steps = self.parser.parse_steps(caption)
                duration_match = re.search(r'(\d+)\s*dakika', caption, re.IGNORECASE)
                total_duration = duration_match.group(0) if duration_match else None
                difficulty = self.parser.extract_difficulty(caption)
                servings = self.parser.extract_servings(caption)
        else:
            print(f"📝 Regex ile parsing: {url}")
            # Standart regex parsing
            title = self.parser.extract_title(caption)
            ingredients = self.parser.parse_ingredients(caption)
            steps = self.parser.parse_steps(caption)
            duration_match = re.search(r'(\d+)\s*dakika', caption, re.IGNORECASE)
            total_duration = duration_match.group(0) if duration_match else None
            difficulty = self.parser.extract_difficulty(caption)
            servings = self.parser.extract_servings(caption)
        
        # 5. Hashtag'ler
        hashtags = re.findall(r'#(\w+)', caption)
        
        # 6. Recipe oluştur
        recipe = Recipe(
            title=title,
            description=caption[:200] + '...' if len(caption) > 200 else caption,
            ingredients=ingredients,
            steps=steps,
            total_duration=total_duration,
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
        
        # 7. Cache'e kaydet
        await self.db_helper.save_recipe(url, recipe.dict())
        print(f"💾 Cache'e kaydedildi: {url}")
        
        return recipe


# Service will be initialized on startup
service = None


# ==================== STARTUP/SHUTDOWN ====================

@app.on_event("startup")
async def startup_db_client():
    """MongoDB bağlantısını başlat"""
    global mongo_client, db, service
    
    try:
        mongo_client = AsyncIOMotorClient(MONGODB_URL)
        db = mongo_client[MONGODB_DB_NAME]
        
        # Test connection
        await db.command('ping')
        print(f"✅ MongoDB bağlantısı başarılı: {MONGODB_DB_NAME}")
        
        # Create index for faster lookups
        await db.recipes.create_index("url_hash", unique=True)
        
    except Exception as e:
        print(f"⚠️ MongoDB bağlantısı başarısız: {e}")
        print("⚠️ Cache olmadan devam ediliyor...")
        db = None
    
    # Initialize service with DB and proxy
    service = RecipeService(db=db, openai_api_key=OPENAI_API_KEY, proxy_url=PROXY_URL if PROXY_ENABLED else None)
    print(f"🚀 RecipeService başlatıldı (AI: {service.ai_parser.enabled}, Proxy: {PROXY_ENABLED})")


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
    Instagram, TikTok veya YouTube Shorts URL'den tarif çıkar
    
    **Yeni Özellikler:**
    - ✅ MongoDB cache (aynı URL tekrar istenirse cache'den döner)
    - ✅ AI-powered parsing (use_ai: true ile)
    
    **Desteklenen Platformlar:**
    - Instagram (Reels, Posts)
    - TikTok
    - YouTube Shorts
    
    **Örnek Request (Normal):**
    ```json
    {
        "url": "https://www.instagram.com/p/ABC123/",
        "use_ai": false
    }
    ```
    
    **Örnek Request (AI ile):**
    ```json
    {
        "url": "https://www.instagram.com/p/ABC123/",
        "use_ai": true
    }
    ```
    
    **Örnek Response:**
    ```json
    {
        "success": true,
        "recipe": {
            "title": "Havuçlu Kek",
            "ingredients": [...],
            "steps": [...],
            ...
        },
        "message": "Tarif başarıyla çıkarıldı"
    }
    ```
    """
    try:
        recipe = await service.parse_recipe(request.url, use_ai=request.use_ai)
        
        return RecipeResponse(
            success=True,
            recipe=recipe,
            message="Tarif başarıyla çıkarıldı"
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
        "cache_enabled": true,
        "ai_enabled": true
    }
    ```
    """
    stats = await service.db_helper.get_stats()
    return {
        **stats,
        "cache_enabled": db is not None,
        "ai_enabled": service.ai_parser.enabled
    }


if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting Recipe Parser API...")
    print("📱 Supported: Instagram, TikTok, YouTube Shorts")
    print("🌐 Server: http://0.0.0.0:8001")
    print("📖 Docs: http://0.0.0.0:8001/docs")
    
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
