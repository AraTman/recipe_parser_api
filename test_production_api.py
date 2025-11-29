#!/usr/bin/env python3
"""
Production API Test Script
Instagram, TikTok, YouTube test senaryoları
"""

import requests
import json
import time

API_URL = "http://localhost:8001"

# Test URLs
TEST_URLS = {
    "instagram": "https://www.instagram.com/reel/DNX8U4tMR_P/?igsh=MWd6ZzQ3M2NoYnlpdg==",  # Havuçlu kek
    "youtube": "https://www.youtube.com/shorts/example123",  # YouTube short
    "tiktok": "https://www.tiktok.com/@user/video/123456",  # TikTok video
}


def test_health():
    """Health check test"""
    print("\n" + "="*60)
    print("🏥 HEALTH CHECK TEST")
    print("="*60)
    
    try:
        response = requests.get(f"{API_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status: {data['status']}")
            print(f"📦 Version: {data['version']}")
            print(f"🌐 Platforms: {', '.join(data['supported_platforms'])}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        print("\n💡 API çalışmıyor. Başlatmak için:")
        print("   python3 recipe_api_production.py")
        return False


def test_parse_recipe(platform: str, url: str):
    """Tarif parse testi"""
    print("\n" + "="*60)
    print(f"🧪 TESTING {platform.upper()}")
    print("="*60)
    print(f"📱 URL: {url}")
    
    try:
        payload = {"url": url}
        response = requests.post(
            f"{API_URL}/api/v1/parse-recipe",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data['success']:
                recipe = data['recipe']
                
                print("\n✅ SUCCESS!")
                print("-"*60)
                print(f"📝 Tarif: {recipe['title']}")
                print(f"🌐 Platform: {recipe['source_platform']}")
                print(f"👤 Yazar: @{recipe['author_username']}")
                print(f"⏱️  Süre: {recipe['total_duration'] or 'Belirtilmemiş'}")
                print(f"🔥 Zorluk: {recipe['difficulty']}")
                print(f"🎬 Video: {recipe['video_duration']} saniye" if recipe['video_duration'] else "")
                
                print(f"\n🥘 Malzemeler ({len(recipe['ingredients'])}):")
                for ing in recipe['ingredients'][:5]:  # İlk 5 malzeme
                    unit = f" {ing['unit']}" if ing['unit'] else ""
                    print(f"  • {ing['amount']}{unit} {ing['item']}")
                if len(recipe['ingredients']) > 5:
                    print(f"  ... ve {len(recipe['ingredients']) - 5} malzeme daha")
                
                print(f"\n👨‍🍳 Adımlar ({len(recipe['steps'])}):")
                for step in recipe['steps'][:3]:  # İlk 3 adım
                    duration = f" ({step['duration']})" if step['duration'] else ""
                    print(f"  {step['order']}. {step['text'][:60]}...{duration}")
                if len(recipe['steps']) > 3:
                    print(f"  ... ve {len(recipe['steps']) - 3} adım daha")
                
                if recipe.get('hashtags'):
                    print(f"\n🏷️  Hashtag'ler: {', '.join(['#' + tag for tag in recipe['hashtags'][:5]])}")
                
                # Save to file
                filename = f"recipe_{recipe['source_platform']}_{int(time.time())}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(recipe, f, ensure_ascii=False, indent=2)
                print(f"\n💾 Kaydedildi: {filename}")
                
                return True
            else:
                print(f"\n❌ Error: {data['error']}")
                print(f"💬 Message: {data.get('message', 'N/A')}")
                return False
        else:
            print(f"\n❌ HTTP Error: {response.status_code}")
            print(response.text)
            return False
            
    except requests.exceptions.Timeout:
        print("\n⏱️  Timeout! API çok yavaş yanıt veriyor.")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


def test_supported_platforms():
    """Desteklenen platformları test et"""
    print("\n" + "="*60)
    print("🌐 SUPPORTED PLATFORMS")
    print("="*60)
    
    try:
        response = requests.get(f"{API_URL}/api/v1/supported-platforms")
        if response.status_code == 200:
            data = response.json()
            for platform in data['platforms']:
                print(f"\n✅ {platform['name']}")
                print(f"   Types: {', '.join(platform['types'])}")
                print(f"   Example: {platform['example']}")
            return True
        else:
            print(f"❌ Failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def run_all_tests():
    """Tüm testleri çalıştır"""
    print("\n" + "🚀"*30)
    print("RECIPE PARSER API - PRODUCTION TESTS")
    print("🚀"*30)
    
    # Health check
    if not test_health():
        return
    
    # Supported platforms
    test_supported_platforms()
    
    # Instagram test
    test_parse_recipe("instagram", TEST_URLS["instagram"])
    
    # YouTube test (optional)
    # test_parse_recipe("youtube", TEST_URLS["youtube"])
    
    # TikTok test (optional)
    # test_parse_recipe("tiktok", TEST_URLS["tiktok"])
    
    print("\n" + "="*60)
    print("✅ TESTS COMPLETED!")
    print("="*60)
    print("\n📖 API Documentation: http://localhost:8001/docs")
    print("🔗 Swagger UI: http://localhost:8001/docs")
    print("📝 ReDoc: http://localhost:8001/redoc")


if __name__ == "__main__":
    run_all_tests()
