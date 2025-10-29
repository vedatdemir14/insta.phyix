#!/usr/bin/env python3
"""
Unified Link System - Temizlenmiş Versiyon
Sadece gerekli fonksiyonlar ve API endpoints
"""

import os
import sys
import time
import json
import asyncio
import argparse
import unicodedata
import re
from typing import List, Dict, Optional, Tuple, Any
from urllib.parse import urlparse, urljoin
from concurrent.futures import ThreadPoolExecutor
import requests
from bs4 import BeautifulSoup
from colorama import Fore, Style, init
from supabase import create_client, Client
from openai import AsyncOpenAI
import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Colorama'yı başlat
init(autoreset=True)

# =============================================================================
# SUPABASE CLIENT
# =============================================================================

class SupabaseClient:
    def __init__(self):
        """Supabase client'ı başlat"""
        self.supabase = None
        self._init_supabase()
    
    def _init_supabase(self):
        """Supabase bağlantısını başlat"""
        try:
            # Hardcoded API keys - Buraya kendi Supabase bilgilerini ekle
            url = "https://qdvfntffaorztslkukgb.supabase.co"  # Supabase URL'ini buraya ekle
            key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFkdmZudGZmYW9yenRzbGt1a2diIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDU5NDg4MzUsImV4cCI6MjA2MTUyNDgzNX0.89PKgpdI0ItYQ-4FlY2ZSN5lSnyr0aIMuh4cAPjpKYs"  # Supabase anon key'ini buraya ekle
            
            # Environment variables'dan al (varsa)
            env_url = os.getenv("SUPABASE_URL")
            env_key = os.getenv("SUPABASE_KEY")
            
            if env_url and env_key:
                url = env_url
                key = env_key
            
            if not url or not key or url == "https://your-project.supabase.co":
                print(f"{Fore.YELLOW}[SUPABASE WARNING]{Style.RESET_ALL} Supabase credentials bulunamadı")
                return
            
            self.supabase = create_client(url, key)
            print(f"{Fore.GREEN}[SUPABASE]{Style.RESET_ALL} Bağlantı başarılı!")
            
        except Exception as e:
            print(f"{Fore.RED}[SUPABASE ERROR]{Style.RESET_ALL} Bağlantı hatası: {e}")
    
    def save_article(self, title: str, url: str, domain: str, keyword: str = None):
        """Article'ı Supabase'e kaydet"""
        try:
            print(f"{Fore.CYAN}[SUPABASE DEBUG]{Style.RESET_ALL} save_article çağrıldı: {title}")
            
            if not self.supabase:
                print(f"{Fore.RED}[SUPABASE ERROR]{Style.RESET_ALL} Supabase client yok")
                return None
            
            # Önce article var mı kontrol et
            existing = self.supabase.table('articles').select('id').eq('url', url).execute()
            
            if existing.data:
                article_id = existing.data[0]['id']
                print(f"{Fore.YELLOW}[SUPABASE WARNING]{Style.RESET_ALL} Article zaten mevcut: {url} (ID: {article_id})")
                return article_id
            
            # Yeni article ekle
            article_data = {
                'title': title,
                'url': url,
                'domain': domain,
                'keyword': keyword
            }
            
            print(f"{Fore.CYAN}[SUPABASE DEBUG]{Style.RESET_ALL} Article data: {article_data}")
            
            result = self.supabase.table('articles').insert(article_data).execute()
            
            print(f"{Fore.CYAN}[SUPABASE DEBUG]{Style.RESET_ALL} Insert result: {result}")
            
            if result.data and len(result.data) > 0:
                article_id = result.data[0].get('id')
                if article_id:
                    print(f"{Fore.GREEN}[SUPABASE]{Style.RESET_ALL} Article kaydedildi: {title} (ID: {article_id})")
                    return article_id
                else:
                    print(f"{Fore.RED}[SUPABASE ERROR]{Style.RESET_ALL} Article ID None")
            else:
                print(f"{Fore.RED}[SUPABASE ERROR]{Style.RESET_ALL} Article kaydedilemedi - data yok")
            
            return None
            
        except Exception as e:
            print(f"{Fore.RED}[SUPABASE ERROR]{Style.RESET_ALL} Article kaydetme hatası: {e}")
            return None
    
    def update_article_keyword(self, article_id: int, keyword: str):
        """Article'ın keyword'ünü güncelle"""
        try:
            if not self.supabase:
                return False
            
            result = self.supabase.table('articles').update({
                'keyword': keyword
            }).eq('id', article_id).execute()
            
            if result.data:
                print(f"{Fore.GREEN}[SUPABASE]{Style.RESET_ALL} Article keyword güncellendi: ID {article_id} -> {keyword}")
                return True
            
            return False
            
        except Exception as e:
            print(f"{Fore.RED}[SUPABASE ERROR]{Style.RESET_ALL} Keyword güncelleme hatası: {e}")
            return False

# =============================================================================
# LINK SCRAPER
# =============================================================================

class LinkScraper:
    def __init__(self, base_url, max_depth=2, delay=1, max_workers=10):
        """Link scraper sınıfı"""
        self.base_url = self._clean_url(base_url)
        self.domain = urlparse(self.base_url).netloc
        self.max_depth = max_depth
        self.delay = delay
        self.max_workers = max_workers
        self.visited_urls = set()
        self.all_links = set()
        self.session = requests.Session()
        
        # Supabase client ekle
        self.supabase = SupabaseClient()
        
        # Random User-Agent ve headers
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0 Safari/537.36'
        ]
        self._update_headers()
    
    def _clean_url(self, url):
        """URL'yi temizle"""
        if not url:
            return ""
        
        # Çift protokol kontrolü
        if url.startswith('https://https://'):
            url = url.replace('https://https://', 'https://')
        elif url.startswith('http://http://'):
            url = url.replace('http://http://', 'http://')
        
        # Protokol ekle
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        return url
    
    def _update_headers(self):
        """Headers'ları random olarak güncelle"""
        import random
        user_agent = random.choice(self.user_agents)
        self.session.headers.update({
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9,tr;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'DNT': '1',
            'Sec-GPC': '1'
        })
    
    def is_valid_url(self, url):
        """URL'nin geçerli olup olmadığını kontrol et"""
        try:
            parsed = urlparse(url)
            return bool(parsed.netloc) and parsed.scheme in ('http', 'https')
        except:
            return False
    
    def is_same_domain(self, url):
        """URL'nin aynı domain'de olup olmadığını kontrol et"""
        try:
            parsed = urlparse(url)
            return parsed.netloc == self.domain
        except:
            return False
    
    def _is_blog_post_link(self, url: str):
        """URL'nin blog yazısı linki olup olmadığını kontrol et"""
        try:
            url_lower = url.lower()
            
            # Blog yazısı göstergeleri
            blog_indicators = [
                '/blog/', '/blogs/', '/post/', '/posts/', '/article/', '/articles/',
                '/story/', '/stories/', '/entry/', '/entries/'
            ]
            
            # Blog yazısı mı?
            has_blog_indicator = any(indicator in url_lower for indicator in blog_indicators)
            
            # Teknik dosya değil
            technical_extensions = ['.css', '.js', '.json', '.xml', '.txt', '.pdf', '.jpg', '.png', '.gif', '.svg']
            is_not_technical = not any(url_lower.endswith(ext) for ext in technical_extensions)
            
            # Pagination değil
            is_not_pagination = '/page/' not in url_lower
            
            # Admin/API değil
            is_not_admin = not any(pattern in url_lower for pattern in ['/admin/', '/api/', '/ajax/', '/wp-admin/'])
            
            # Sadece blog yazıları (liste sayfaları değil)
            is_blog_post = has_blog_indicator and is_not_technical and is_not_pagination and is_not_admin
            
            return is_blog_post
            
        except:
            return False

# =============================================================================
# ASYNC KEYWORD GENERATOR
# =============================================================================

class AsyncKeywordGenerator:
    def __init__(self, api_key: str = None, max_concurrent: int = 5):
        """Async keyword generator'ı başlat (OpenRouter)"""
        # Hardcoded API key - Buraya kendi OpenRouter API key'ini ekle
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY") or "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"
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        
        if self.api_key and self.api_key != "your-openrouter-api-key" and self.api_key.startswith("sk-or-"):
            self.client = AsyncOpenAI(
                api_key=self.api_key,
                base_url="https://openrouter.ai/api/v1"
            )
        else:
            self.client = None
            print(f"{Fore.YELLOW}[KEYWORD GENERATOR WARNING]{Style.RESET_ALL} OpenRouter API key bulunamadı")
    
    async def generate_keywords_async(self, url: str, title: str = None, content: str = None) -> List[Dict[str, any]]:
        """Asenkron keyword üretimi"""
        async with self.semaphore:
            try:
                if not self.client:
                    return self._fallback_keywords(url, title)
                
                prompt = self._create_prompt(url, title, content)
                
                response = await self.client.chat.completions.create(
                    model="google/gemini-2.0-flash-001",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=500,
                    temperature=0.7
                )
                
                content = response.choices[0].message.content
                keywords = self._parse_keywords(content)
                
                if not keywords:
                    return self._fallback_keywords(url, title)
                
                return keywords
                
            except Exception as e:
                print(f"{Fore.YELLOW}[KEYWORD ERROR]{Style.RESET_ALL} {url}: {e}")
                return self._fallback_keywords(url, title)
    
    def _create_prompt(self, url: str, title: str = None, content: str = None) -> str:
        """Keyword üretimi için prompt oluştur"""
        prompt = f"""
        URL: {url}
        """
        
        if title:
            prompt += f"Başlık: {title}\n"
        
        if content:
            prompt += f"İçerik: {content[:500]}...\n"
        
        prompt += """
        
        Bu URL için SEO-friendly Türkçe keyword'ler üret. Her keyword için:
        - keyword: Anahtar kelime
        - relevance_score: 0.0-1.0 arası relevans skoru
        - source: "ai_generated"
        - category: "primary" veya "secondary"
        
        JSON formatında döndür:
        [
            {"keyword": "anahtar kelime", "relevance_score": 0.9, "source": "ai_generated", "category": "primary"},
            {"keyword": "ikinci kelime", "relevance_score": 0.7, "source": "ai_generated", "category": "secondary"}
        ]
        """
        
        return prompt
    
    def _parse_keywords(self, content: str) -> List[Dict[str, any]]:
        """AI yanıtından keyword'leri parse et"""
        try:
            # JSON kısmını bul
            json_start = content.find('[')
            json_end = content.rfind(']') + 1
            
            if json_start == -1 or json_end == 0:
                return []
            
            json_str = content[json_start:json_end]
            keywords = json.loads(json_str)
            
            # Geçerli keyword'leri filtrele
            valid_keywords = []
            for kw in keywords:
                if isinstance(kw, dict) and 'keyword' in kw:
                    valid_keywords.append({
                        'keyword': kw.get('keyword', ''),
                        'relevance_score': float(kw.get('relevance_score', 0.5)),
                        'source': kw.get('source', 'ai_generated'),
                        'category': kw.get('category', 'secondary')
                    })
            
            return valid_keywords
            
        except Exception as e:
            print(f"{Fore.YELLOW}[PARSE ERROR]{Style.RESET_ALL} {e}")
            return []
    
    def _fallback_keywords(self, url: str, title: str = None) -> List[Dict[str, any]]:
        """Fallback keyword'ler"""
        keywords = []
        
        if title:
            keywords.append({
                'keyword': title.lower(),
                'relevance_score': 0.8,
                'source': 'fallback',
                'category': 'primary'
            })
        
        # URL'den keyword çıkar
        url_parts = url.split('/')[-1].replace('-', ' ').replace('_', ' ')
        if url_parts and len(url_parts) > 3:
            keywords.append({
                'keyword': url_parts,
                'relevance_score': 0.6,
                'source': 'fallback',
                'category': 'secondary'
            })
        
        # Default keyword'ler
        default_keywords = [
            {'keyword': 'web sayfası', 'relevance_score': 0.5, 'source': 'default', 'category': 'secondary'},
            {'keyword': 'içerik', 'relevance_score': 0.4, 'source': 'default', 'category': 'secondary'}
        ]
        keywords.extend(default_keywords)
        
        return keywords

# =============================================================================
# TEXT LINKIFIER
# =============================================================================

class TextLinkifier:
    def __init__(self):
        """Text linkifier'ı başlat"""
        self.supabase = SupabaseClient()
        self.used_keywords = set()
        
        # Türkçe stopword'ler
        self.stopwords = {
            've', 'ile', 'için', 'olan', 'bir', 'bu', 'şu', 'o', 'da', 'de', 'ta', 'te',
            'den', 'dan', 'ten', 'tan', 'nin', 'nın', 'nun', 'nün', 'in', 'ın', 'un', 'ün',
            'ya', 'ye', 'yi', 'yı', 'yu', 'yü', 'na', 'ne', 'ni', 'nı', 'nu', 'nü',
            'la', 'le', 'lı', 'li', 'lu', 'lü', 'sı', 'si', 'su', 'sü', 'sa', 'se',
            'mi', 'mı', 'mu', 'mü', 'ma', 'me', 'mı', 'mi', 'mu', 'mü',
            'ki', 'kı', 'ku', 'kü', 'ka', 'ke', 'kı', 'ki', 'ku', 'kü',
            'çok', 'az', 'daha', 'en', 'çok', 'az', 'daha', 'en', 'çok', 'az',
            'ama', 'ancak', 'fakat', 'lakin', 'yalnız', 'sadece', 'sade', 'yalnız',
            'eğer', 'şayet', 'eğer', 'şayet', 'eğer', 'şayet', 'eğer', 'şayet',
            'çünkü', 'zira', 'çünkü', 'zira', 'çünkü', 'zira', 'çünkü', 'zira',
            'böyle', 'şöyle', 'böyle', 'şöyle', 'böyle', 'şöyle', 'böyle', 'şöyle',
            'nasıl', 'niçin', 'neden', 'nasıl', 'niçin', 'neden', 'nasıl', 'niçin',
            'ne', 'kim', 'kime', 'kimden', 'kimin', 'kiminle', 'kiminle', 'kiminle',
            'hangi', 'hangisi', 'hangi', 'hangisi', 'hangi', 'hangisi', 'hangi', 'hangisi',
            'nerede', 'nereye', 'nereden', 'nerede', 'nereye', 'nereden', 'nerede', 'nereye',
            'ne zaman', 'ne zaman', 'ne zaman', 'ne zaman', 'ne zaman', 'ne zaman',
            'kaç', 'kaçıncı', 'kaç', 'kaçıncı', 'kaç', 'kaçıncı', 'kaç', 'kaçıncı'
        }
    
    def normalize_turkish(self, text: str) -> str:
        """Türkçe karakterleri normalize et"""
        if not text:
            return ""
        
        text = unicodedata.normalize('NFD', text)
        
        replacements = {
            'ı': 'i', 'İ': 'I', 'ğ': 'g', 'Ğ': 'G',
            'ü': 'u', 'Ü': 'U', 'ş': 's', 'Ş': 'S',
            'ö': 'o', 'Ö': 'O', 'ç': 'c', 'Ç': 'C'
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        return text.lower().strip()
    
    def normalize(self, text: str) -> str:
        """Genel normalize işlemi"""
        if not text:
            return ""
        
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def is_stopword_or_short(self, word: str) -> bool:
        """Kelimenin stopword veya çok kısa olup olmadığını kontrol et"""
        if not word or len(word) < 3:
            return True
        
        if word in self.stopwords:
            return True
        
        if word.isdigit():
            return True
        
        return False
    
    def get_article_titles_from_db(self) -> List[Dict]:
        """Veritabanından keyword'leri getir (articles tablosundan)"""
        try:
            result = self.supabase.supabase.table('articles').select('*').execute()
            
            if not result.data:
                print(f"{Fore.YELLOW}[LINKIFIER]{Style.RESET_ALL} Veritabanında article bulunamadı")
                return []
            
            articles = []
            for item in result.data:
                if item.get('keyword') and item.get('url'):
                    articles.append({
                        'keyword': item.get('keyword', ''),
                        'url': item.get('url', ''),
                        'relevance_score': 0.8  # Default score
                    })
            
            print(f"{Fore.GREEN}[LINKIFIER]{Style.RESET_ALL} {len(articles)} article keyword yüklendi")
            return articles
            
        except Exception as e:
            print(f"{Fore.RED}[LINKIFIER ERROR]{Style.RESET_ALL} Veritabanı hatası: {e}")
            return []
    
    def linkify_text_with_db(self, text: str) -> str:
        """Metni veritabanındaki keyword'lerle linkify et"""
        if not text:
            return text
        
        articles = self.get_article_titles_from_db()
        if not articles:
            return text
        
        original_text = text
        normalized_text = self.normalize_turkish(self.normalize(text))
        
        valid_titles = []
        for article in articles:
            keyword_norm = self.normalize_turkish(self.normalize(article['keyword']))
            if not self.is_stopword_or_short(keyword_norm):
                valid_titles.append((
                    keyword_norm, 
                    article['keyword'], 
                    article['url'],
                    article['relevance_score']
                ))
        
        valid_titles.sort(key=lambda x: (-x[3], -len(x[0].split())))
        
        used_keywords = set()
        
        for keyword_norm, original_keyword, url, relevance_score in valid_titles:
            if keyword_norm in used_keywords:
                continue
            
            if keyword_norm in normalized_text:
                used_keywords.add(keyword_norm)
                
                # Markdown link oluştur
                def replacer(match):
                    return f"[{original_keyword}]({url})"
                
                # Case-insensitive replacement
                pattern = re.compile(re.escape(original_keyword), re.IGNORECASE)
                original_text = pattern.sub(replacer, original_text)
        
        return original_text
    
    def get_linkification_stats(self, text: str) -> dict:
        """Linkleme istatistiklerini hesapla"""
        if not text:
            return {
                'links_added': 0,
                'matched_keywords': [],
                'total_keywords': 0
            }
        
        articles = self.get_article_titles_from_db()
        if not articles:
            return {
                'links_added': 0,
                'matched_keywords': [],
                'total_keywords': 0
            }
        
        original_text = text
        normalized_text = self.normalize_turkish(self.normalize(text))
        
        valid_titles = []
        for article in articles:
            keyword_norm = self.normalize_turkish(self.normalize(article['keyword']))
            if not self.is_stopword_or_short(keyword_norm):
                valid_titles.append((
                    keyword_norm, 
                    article['keyword'], 
                    article['url'],
                    article['relevance_score']
                ))
        
        valid_titles.sort(key=lambda x: (-x[3], -len(x[0].split())))
        
        used_keywords = set()
        matched_keywords = []
        links_added = 0
        
        for keyword_norm, original_keyword, url, relevance_score in valid_titles:
            if keyword_norm in used_keywords:
                continue
            
            if keyword_norm in normalized_text:
                used_keywords.add(keyword_norm)
                matched_keywords.append(original_keyword)
                links_added += 1
        
        return {
            'links_added': links_added,
            'matched_keywords': matched_keywords,
            'total_keywords': len(valid_titles)
        }

# =============================================================================
# SELENIUM SCRAPER (Next Button Scraping)
# =============================================================================

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, WebDriverException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print(f"{Fore.YELLOW}[WARNING]{Style.RESET_ALL} Selenium yüklü değil. pip install selenium yükleyin.")

class SeleniumScraper:
    def __init__(self):
        """Selenium scraper'ı başlat"""
        self.driver = None
        self.supabase = SupabaseClient()
        self.keyword_generator = AsyncKeywordGenerator()
    
    def _get_selenium_driver(self):
        """Selenium driver'ı başlat (anti-detection)"""
        if not SELENIUM_AVAILABLE:
            return None
        if self.driver is None:
            try:
                chrome_options = Options()
                chrome_options.add_argument('--no-sandbox')
                chrome_options.add_argument('--disable-dev-shm-usage')
                chrome_options.add_argument('--disable-gpu')
                chrome_options.add_argument('--window-size=1366,768')
                chrome_options.add_argument('--disable-blink-features=AutomationControlled')
                chrome_options.add_argument('--disable-extensions')
                chrome_options.add_argument('--disable-plugins')
                chrome_options.add_argument('--disable-images')
                chrome_options.add_argument('--disable-javascript')
                chrome_options.add_argument('--disable-css')
                chrome_options.add_argument('--disable-web-security')
                chrome_options.add_argument('--allow-running-insecure-content')
                chrome_options.add_argument('--disable-features=VizDisplayCompositor')
                chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
                chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
                chrome_options.add_experimental_option('useAutomationExtension', False)
                chrome_options.add_argument('--disable-automation')
                chrome_options.add_argument('--disable-infobars')
                # chrome_options.add_argument('--headless') # Headless mode kapatıldı
                self.driver = webdriver.Chrome(options=chrome_options)
                self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                self.driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
                self.driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']})")
                self.driver.set_page_load_timeout(30)
                self.driver.implicitly_wait(10)
            except Exception as e:
                print(f"{Fore.YELLOW}[SELENIUM WARNING]{Style.RESET_ALL} Chrome driver başlatılamadı: {e}")
                return None
        return self.driver
    
    def _full_scroll_page(self, driver):
        """Sayfayı tamamen scroll et"""
        try:
            last_height = driver.execute_script("return document.body.scrollHeight")
            while True:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            print(f"{Fore.CYAN}[FULL SCROLL]{Style.RESET_ALL} Sayfa tamamen scroll edildi")
        except Exception as e:
            print(f"{Fore.YELLOW}[SCROLL WARNING]{Style.RESET_ALL} Scroll hatası: {e}")
    
    def _extract_all_links_from_page(self, driver):
        """Sayfadaki tüm linkleri çıkar"""
        try:
            all_links = driver.execute_script("""
                var links = [];
                var elements = document.querySelectorAll('a[href]');
                for (var i = 0; i < elements.length; i++) {
                    var href = elements[i].href;
                    if (href && href.startsWith('http')) {
                        links.push(href);
                    }
                }
                return links;
            """)
            return all_links
        except Exception as e:
            print(f"{Fore.YELLOW}[LINK EXTRACTION WARNING]{Style.RESET_ALL} Link çıkarma hatası: {e}")
            return []
    
    def _is_blog_post_link(self, url: str):
        """URL'nin blog yazısı linki olup olmadığını kontrol et (genişletilmiş)"""
        try:
            url_lower = url.lower()
            
            # Blog yazısı göstergeleri (genişletilmiş)
            blog_indicators = [
                '/blog/', '/blogs/', '/post/', '/posts/', '/article/', '/articles/',
                '/story/', '/stories/', '/entry/', '/entries/', '/ilgi-alanlari/',
                '/saglik-rehberi/', '/hastaliklar/', '/tedaviler/', '/prosedurler/',
                '/makale/', '/icerik/', '/detay/', '/haber/', '/news/'
            ]
            
            # Blog yazısı mı?
            has_blog_indicator = any(indicator in url_lower for indicator in blog_indicators)
            
            # Teknik dosya değil
            technical_extensions = ['.css', '.js', '.json', '.xml', '.txt', '.pdf', '.jpg', '.png', '.gif', '.svg', '.ico', '.woff', '.woff2']
            is_not_technical = not any(url_lower.endswith(ext) for ext in technical_extensions)
            
            # Pagination değil
            is_not_pagination = '/page/' not in url_lower and '?page=' not in url_lower
            
            # Admin/API değil
            is_not_admin = not any(pattern in url_lower for pattern in ['/admin/', '/api/', '/ajax/', '/wp-admin/', '/login/', '/register/'])
            
            # Ana sayfa değil
            is_not_homepage = not url_lower.endswith('/') or url_lower.count('/') > 3
            
            # İçerik sayfası mı? (daha esnek kontrol)
            is_content_page = (
                has_blog_indicator or  # Blog göstergesi var
                (is_not_technical and is_not_pagination and is_not_admin and is_not_homepage and 
                 len(url_lower.split('/')) > 4)  # En az 4 seviye derinlik
            )
            
            return is_content_page
            
        except:
            return False
    
    def _find_pagination_container(self, driver):
        """Pagination container'ını bul (sayfanın her yerinde) - hata toleranslı"""
        try:
            container_selectors = [
                ".pagination", ".pager", ".page-navigation", ".pagination-wrapper",
                ".pagination-container", ".pagination-nav", ".pagination-list",
                "ul.pagination", "nav.pagination", ".pagination ul",
                ".page-numbers", ".wp-pagenavi", ".pagination-box",
                ".pagination-bar", ".pagination-menu", ".pagination-controls",
                ".pagination-buttons", ".pagination-links"
            ]
            
            for selector in container_selectors:
                try:
                    containers = driver.find_elements(By.CSS_SELECTOR, selector)
                    for i, container in enumerate(containers):
                        try:
                            links = container.find_elements(By.TAG_NAME, "a")
                            if len(links) >= 3:  # En az 3 link olmalı
                                print(f"{Fore.CYAN}[PAGINATION CONTAINER FOUND]{Style.RESET_ALL} Container bulundu: {selector} (Container {i+1}) - {len(links)} pagination link")
                                return container
                        except Exception as e:
                            continue  # Bu container'ı atla, diğerine geç
                except Exception as e:
                    continue  # Bu selector'ı atla, diğerine geç
            
            print(f"{Fore.YELLOW}[PAGINATION WARNING]{Style.RESET_ALL} Pagination container bulunamadı")
            return None
            
        except Exception as e:
            print(f"{Fore.YELLOW}[PAGINATION ERROR]{Style.RESET_ALL} Container arama hatası: {e}")
            return None
    
    def _find_next_button_in_container(self, container):
        """Container içinde Next butonunu bul (gelişmiş)"""
        try:
            links = container.find_elements(By.TAG_NAME, "a")
            
            # Next buton metinleri
            next_texts = ['next', 'sonraki', 'ileri', '»', '>', '→', 'next page', 'sonraki sayfa']
            
            for i, link in enumerate(links):
                try:
                    text = link.text.strip().lower()
                    href = link.get_attribute('href') or ''
                    rel = link.get_attribute('rel') or ''
                    aria_label = link.get_attribute('aria-label') or ''
                    title = link.get_attribute('title') or ''
                    
                    # Disabled kontrolü
                    if 'disabled' in link.get_attribute('class') or 'disabled' in link.get_attribute('className'):
                        continue
                    
                    # Text kontrolü
                    if any(next_text in text for next_text in next_texts):
                        print(f"{Fore.GREEN}[NEXT BUTTON FOUND]{Style.RESET_ALL} Next butonu bulundu: '{text}' - {href}")
                        return link
                    
                    # Rel kontrolü
                    if 'next' in rel.lower():
                        print(f"{Fore.GREEN}[NEXT BUTTON FOUND]{Style.RESET_ALL} Next butonu bulundu (rel): '{rel}' - {href}")
                        return link
                    
                    # Aria-label kontrolü
                    if any(next_text in aria_label.lower() for next_text in next_texts):
                        print(f"{Fore.GREEN}[NEXT BUTTON FOUND]{Style.RESET_ALL} Next butonu bulundu (aria-label): '{aria_label}' - {href}")
                        return link
                    
                    # Title kontrolü
                    if any(next_text in title.lower() for next_text in next_texts):
                        print(f"{Fore.GREEN}[NEXT BUTTON FOUND]{Style.RESET_ALL} Next butonu bulundu (title): '{title}' - {href}")
                        return link
                    
                    # Sayısal pagination kontrolü (son sayfa değilse)
                    if text.isdigit():
                        try:
                            current_page = int(text)
                            # Eğer bu sayfa mevcut sayfadan büyükse, next olabilir
                            if current_page > 1:  # Basit kontrol
                                print(f"{Fore.CYAN}[NEXT BUTTON DEBUG]{Style.RESET_ALL} Sayısal link: {text} - {href}")
                        except:
                            pass
                    
                except Exception as e:
                    continue
            
            print(f"{Fore.YELLOW}[NEXT BUTTON WARNING]{Style.RESET_ALL} Next butonu bulunamadı")
            return None
            
        except Exception as e:
            print(f"{Fore.YELLOW}[NEXT BUTTON ERROR]{Style.RESET_ALL} Next buton arama hatası: {e}")
            return None
    
    async def next_button_scrape(self, url, generate_keywords: bool = True):
        """Next butonuna tıklayarak pagination scraping.
        generate_keywords True ise, scraping bittikten sonra toplu ve eşzamanlı keyword üretimi yapılır.
        """
        try:
            driver = self._get_selenium_driver()
            if not driver:
                return {
                    'success': False,
                    'blog_links': [],
                    'pages_scraped': 0,
                    'error': 'Selenium driver başlatılamadı'
                }
            
            print(f"{Fore.CYAN}[NEXT BUTTON SCRAPE]{Style.RESET_ALL} Next buton scraping başlatılıyor: {url}")
            
            all_blog_links = set()
            pages_scraped = 0
            articles_saved = 0
            saved_articles: list[tuple[int, str, str]] = []  # (article_id, url, title)
            current_url = url
            
            # İlk sayfayı yükle
            driver.get(current_url)
            time.sleep(3)
            
            while True:
                print(f"{Fore.YELLOW}[PAGE {pages_scraped + 1}]{Style.RESET_ALL} Sayfa işleniyor: {current_url}")
                
                # Full scroll yap
                self._full_scroll_page(driver)
                
                # Bu sayfadaki tüm linkleri al
                page_links = self._extract_all_links_from_page(driver)
                print(f"{Fore.CYAN}[DEBUG]{Style.RESET_ALL} Toplam {len(page_links)} link bulundu")
                
                # Blog linklerini filtrele ve articles tablosuna kaydet
                blog_links = set()
                for link in page_links:
                    if self._is_blog_post_link(link):
                        clean_link = link.split('#')[0]
                        blog_links.add(clean_link)
                        print(f"{Fore.GREEN}[BLOG LINK]{Style.RESET_ALL} {clean_link}")
                        
                        # Article'ı database'e kaydet
                        try:
                            from urllib.parse import urlparse
                            domain = urlparse(clean_link).netloc
                            # Son boş olmayan path segmentinden başlık üret
                            parts = [p for p in clean_link.rstrip('/').split('/') if p]
                            last_seg = parts[-1] if parts else ''
                            title = last_seg.replace('-', ' ').replace('_', ' ').title()
                            
                            article_id = self.supabase.save_article(
                                title=title,
                                url=clean_link,
                                domain=domain,
                                keyword=None  # Önce None, sonra keyword üretilecek
                            )
                            
                            if article_id:
                                articles_saved += 1
                                print(f"{Fore.GREEN}[ARTICLE SAVED]{Style.RESET_ALL} {title} (ID: {article_id})")
                                saved_articles.append((article_id, clean_link, title))
                            else:
                                print(f"{Fore.RED}[ARTICLE ERROR]{Style.RESET_ALL} Article kaydedilemedi: {title}")
                                    
                        except Exception as e:
                            print(f"{Fore.RED}[ARTICLE ERROR]{Style.RESET_ALL} Article kaydetme hatası {clean_link}: {e}")
                            import traceback
                            print(f"{Fore.RED}[TRACEBACK]{Style.RESET_ALL} {traceback.format_exc()}")
                
                all_blog_links.update(blog_links)
                print(f"{Fore.GREEN}[PAGE SUCCESS]{Style.RESET_ALL} Sayfa {pages_scraped + 1}: {len(blog_links)} blog yazısı bulundu")
                
                pages_scraped += 1
                
                # Next butonunu bul ve tıkla
                container = self._find_pagination_container(driver)
                if container:
                    next_button = self._find_next_button_in_container(container)
                    if next_button:
                        try:
                            next_url = next_button.get_attribute('href')
                            if next_url and next_url != current_url:
                                current_url = next_url
                                driver.get(current_url)
                                time.sleep(3)
                            else:
                                print(f"{Fore.YELLOW}[NO NEXT]{Style.RESET_ALL} Next buton bulunamadı veya aynı URL")
                                break
                        except Exception as e:
                            print(f"{Fore.RED}[NEXT ERROR]{Style.RESET_ALL} Next buton tıklama hatası: {e}")
                            break
                    else:
                        print(f"{Fore.YELLOW}[NO NEXT]{Style.RESET_ALL} Next buton bulunamadı")
                        break
                else:
                    print(f"{Fore.YELLOW}[NO PAGINATION]{Style.RESET_ALL} Pagination container bulunamadı")
                    break
            
            # Toplu keyword üretimi (opsiyonel)
            keywords_updated = 0
            if generate_keywords and saved_articles:
                print(f"{Fore.CYAN}[KEYWORD BATCH]{Style.RESET_ALL} Toplu keyword üretimi başlıyor... ({len(saved_articles)} article)")

                sem = asyncio.Semaphore(10)

                async def process_one(article_id: int, link: str, title: str):
                    nonlocal keywords_updated
                    async with sem:
                        try:
                            keywords = await self.keyword_generator.generate_keywords_async(link, title)
                            if keywords and len(keywords) > 0:
                                first_keyword = keywords[0].get('keyword', '')
                                if first_keyword:
                                    self.supabase.update_article_keyword(article_id, first_keyword)
                                    keywords_updated += 1
                                    print(f"{Fore.GREEN}[ARTICLE KEYWORD]{Style.RESET_ALL} {title}: {first_keyword}")
                        except Exception as e:
                            print(f"{Fore.YELLOW}[KEYWORD WARNING]{Style.RESET_ALL} Batch keyword hatası {title}: {e}")

                tasks = []
                for aid, lnk, ttl in saved_articles:
                    tasks.append(process_one(aid, lnk, ttl))
                await asyncio.gather(*tasks)

            print(f"{Fore.GREEN}[NEXT BUTTON COMPLETE]{Style.RESET_ALL} {pages_scraped} sayfa tarandı, {len(all_blog_links)} blog yazısı bulundu, {articles_saved} article kaydedildi, {keywords_updated} keyword güncellendi")
            
            return {
                'success': True,
                'blog_links': list(all_blog_links),
                'pages_scraped': pages_scraped,
                'total_blog_posts': len(all_blog_links),
                'articles_saved': articles_saved,
                'keywords_updated': keywords_updated
            }
            
        except Exception as e:
            print(f"{Fore.RED}[NEXT BUTTON ERROR]{Style.RESET_ALL} Hata: {e}")
            return {
                'success': False,
                'blog_links': [],
                'pages_scraped': 0,
                'error': str(e)
            }
        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None

# =============================================================================
# UNIFIED LINK SYSTEM
# =============================================================================

class UnifiedLinkSystem:
    def __init__(self):
        """Unified link system'i başlat"""
        self.supabase = SupabaseClient()
        self.linkifier = TextLinkifier()
        self.keyword_generator = AsyncKeywordGenerator()
    
    def _clean_url(self, url):
        """URL'yi temizle"""
        if not url:
            return ""
        
        if url.startswith('https://https://'):
            url = url.replace('https://https://', 'https://')
        elif url.startswith('http://http://'):
            url = url.replace('http://http://', 'http://')
        
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        return url
    
    def linkify_text(self, text: str) -> str:
        """Metni linkify et"""
        print(f"{Fore.CYAN}[UNIFIED SYSTEM]{Style.RESET_ALL} Text linkify başlatılıyor...")
        
        linkified = self.linkifier.linkify_text_with_db(text)
        
        print(f"{Fore.GREEN}[UNIFIED SYSTEM]{Style.RESET_ALL} Text linkify tamamlandı!")
        return linkified

# =============================================================================
# PYDANTIC MODELS
# =============================================================================

class LinkifyRequest(BaseModel):
    text: str
    max_links: int = 10

class LinkifyResponse(BaseModel):
    original_text: str
    linkified_text: str
    links_added: int
    matched_keywords: List[str]
    total_keywords: int

# =============================================================================
# FASTAPI APP
# =============================================================================

app = FastAPI(
    title="Unified Link System API",
    description="Link scraping, keyword generation, and text linkification system",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency
def get_unified_system():
    return UnifiedLinkSystem()

# =============================================================================
# API MODELS
# =============================================================================

class APIResponse(BaseModel):
    success: bool
    message: str
    data: dict = {}

# =============================================================================
# API ENDPOINTS
# =============================================================================

@app.get("/api/v1/scraping/next-button-scraping", response_model=APIResponse)
async def next_button_scraping(
    url: str,
    save_to_db: bool = True
):
    """Next buton scraping endpoint"""
    try:
        # URL'yi temizle
        clean_url = url.replace('https://https://', 'https://')
        if not clean_url.startswith(('http://', 'https://')):
            clean_url = 'https://' + clean_url
        
        print(f"{Fore.CYAN}[NEXT BUTTON SCRAPING]{Style.RESET_ALL} Next buton scraping başlatılıyor...")
        
        # Selenium scraper'ı başlat
        scraper = SeleniumScraper()
        result = await scraper.next_button_scrape(clean_url, generate_keywords=True)
        
        if result['success']:
            return APIResponse(
                success=True,
                message=f"{result['pages_scraped']} sayfa tarandı, {result['total_blog_posts']} blog yazısı bulundu, {result['articles_saved']} article kaydedildi, {result.get('keywords_updated', 0)} keyword güncellendi",
                data={
                    "pages_scraped": result['pages_scraped'],
                    "total_blog_posts": result['total_blog_posts'],
                    "articles_saved": result['articles_saved'],
                    "keywords_updated": result.get('keywords_updated', 0),
                    "blog_links": result['blog_links'][:10]  # İlk 10 link
                }
            )
        else:
            return APIResponse(
                success=False,
                message=f"Scraping hatası: {result.get('error', 'Bilinmeyen hata')}",
                data={}
            )
            
    except Exception as e:
        print(f"{Fore.RED}[API ERROR]{Style.RESET_ALL} Next button scraping hatası: {e}")
        return APIResponse(
            success=False,
            message=f"API hatası: {str(e)}",
            data={}
        )

@app.get("/")
async def root():
    return {"message": "Unified Link System API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": time.time()}

@app.post("/api/v1/linkify", response_model=LinkifyResponse)
async def linkify_text(
    request: LinkifyRequest,
    system: UnifiedLinkSystem = Depends(get_unified_system)
):
    """Metni linkify et"""
    try:
        linkified_text = system.linkify_text(request.text)
        
        # İstatistikler
        stats = system.linkifier.get_linkification_stats(request.text)
        
        return LinkifyResponse(
            original_text=request.text,
            linkified_text=linkified_text,
            links_added=stats['links_added'],
            matched_keywords=stats['matched_keywords'],
            total_keywords=stats['total_keywords']
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# MAIN FUNCTION
# =============================================================================

def main():
    """Ana fonksiyon"""
    parser = argparse.ArgumentParser(description="Unified Link System")
    parser.add_argument('--api', action='store_true', help='API modunda çalıştır')
    parser.add_argument('--host', default='0.0.0.0', help='API host (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=8000, help='API port (default: 8000)')
    parser.add_argument('--workers', type=int, default=1, help='API workers (default: 1)')
    parser.add_argument('--log-level', default='info', help='Log level (default: info)')
    
    args = parser.parse_args()
    
    if args.api:
        print(f"{Fore.CYAN}[API MODE]{Style.RESET_ALL} API server başlatılıyor...")
        print(f"Host: {args.host}")
        print(f"Port: {args.port}")
        print(f"Reload: False")
        print(f"Workers: {args.workers}")
        print(f"Log Level: {args.log_level}")
        print(f"{Fore.CYAN}[DOCS]{Style.RESET_ALL} Swagger UI: http://{args.host}:{args.port}/docs")
        print(f"{Fore.CYAN}[DOCS]{Style.RESET_ALL} ReDoc: http://{args.host}:{args.port}/redoc")
        print("=" * 60)
        
        uvicorn.run(
            "unified_link_system_clean:app",
            host=args.host,
            port=args.port,
            workers=args.workers,
            log_level=args.log_level,
            reload=False
        )
    else:
        print(f"{Fore.YELLOW}[CLI MODE]{Style.RESET_ALL} CLI modu henüz implement edilmedi")
        print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} API modu için --api parametresini kullanın")

if __name__ == "__main__":
    main()
