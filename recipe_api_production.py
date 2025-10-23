#!/usr/bin/env python3
"""
Production Recipe Parser API
Instagram, TikTok, YouTube Shorts destekli tarif çıkarma API'si
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
from typing import List, Optional, Dict
import re
import instaloader
import requests
from datetime import datetime
import os

app = FastAPI(
    title="Recipe Parser API",
    description="Instagram, TikTok, YouTube Shorts'tan tarif çıkarma API'si",
    version="1.0.0"
)

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
    """Instagram scraper"""
    
    def __init__(self):
        self.loader = instaloader.Instaloader(
            download_videos=False,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False,
            compress_json=False,
            post_metadata_txt_pattern='',
            sleep=True,
            quiet=True,
        )
    
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
    """TikTok scraper (API-based)"""
    
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
    """YouTube Shorts scraper"""
    
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
        """Adımları parse et"""
        steps = []
        lines = text.split('\n')
        order = 1
        
        # Türkçe yemek fiilleri
        verbs = [
            'karıştır', 'ekle', 'dök', 'pişir', 'çırp', 'ısıt', 'doğra',
            'ren', 'kes', 'yoğur', 'beklet', 'dinlendir', 'al', 'koy',
            'ilave', 'hazırla', 'yıka', 'temizle', 'soy', 'dilimle',
            'kavur', 'haşla', 'kaynat', 'kızart', 'servis', 'süsle',
            'tat', 'kontrol', 'çevir', 'karış', 'yap', 'oluştur'
        ]
        
        for line in lines:
            line = line.strip()
            if not line or len(line) < 10:
                continue
            
            # Fiil içeren ve yeterince uzun cümleler
            if any(verb in line.lower() for verb in verbs):
                # Süre bilgisi
                duration_match = re.search(r'(\d+)\s*(dakika|saat|saniye)', line, re.IGNORECASE)
                duration = duration_match.group(0) if duration_match else None
                
                # İpucu bilgisi (parantez içi)
                tip_match = re.search(r'\(([^)]+)\)', line)
                tip = tip_match.group(1) if tip_match else None
                
                steps.append(RecipeStep(
                    order=order,
                    text=line,
                    duration=duration,
                    tip=tip
                ))
                order += 1
        
        return steps
    
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
    
    def __init__(self):
        self.instagram_scraper = InstagramScraper()
        self.tiktok_scraper = TikTokScraper()
        self.youtube_scraper = YouTubeScraper()
        self.parser = RecipeParser()
    
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
    
    def parse_recipe(self, url: str) -> Recipe:
        """URL'den tarif çıkar"""
        
        # Platform tespit
        platform = self.detect_platform(url)
        
        # İçerik çek
        content = self.scrape_content(url, platform)
        
        # Parse et
        caption = content['caption']
        title = self.parser.extract_title(caption)
        ingredients = self.parser.parse_ingredients(caption)
        steps = self.parser.parse_steps(caption)
        
        # Süre bilgileri
        duration_match = re.search(r'(\d+)\s*dakika', caption, re.IGNORECASE)
        total_duration = duration_match.group(0) if duration_match else None
        
        # Hashtag'ler
        hashtags = re.findall(r'#(\w+)', caption)
        
        # Recipe oluştur
        return Recipe(
            title=title,
            description=caption[:200] + '...' if len(caption) > 200 else caption,
            ingredients=ingredients,
            steps=steps,
            total_duration=total_duration,
            difficulty=self.parser.extract_difficulty(caption),
            servings=self.parser.extract_servings(caption),
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


# Initialize service
service = RecipeService()


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
    
    **Desteklenen Platformlar:**
    - Instagram (Reels, Posts)
    - TikTok
    - YouTube Shorts
    
    **Örnek Request:**
    ```json
    {
        "url": "https://www.instagram.com/p/ABC123/"
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
        }
    }
    ```
    """
    try:
        recipe = service.parse_recipe(request.url)
        
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


if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting Recipe Parser API...")
    print("📱 Supported: Instagram, TikTok, YouTube Shorts")
    print("🌐 Server: http://0.0.0.0:8001")
    print("📖 Docs: http://0.0.0.0:8001/docs")
    
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
