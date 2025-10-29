from flask import Flask, request, jsonify
import requests
import re
import time
import json
import asyncio
import os
from playwright.sync_api import sync_playwright
try:
    from serpapi import search as GoogleSearch
except ImportError:
    # SerpAPI yoksa mock class oluştur
    class GoogleSearch:
        def __init__(self, params):
            self.params = params
        def get_dict(self):
            return {"organic_results": []}
from bs4 import BeautifulSoup
from supabase import create_client, Client
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from openai import AsyncOpenAI

app = Flask(__name__)

# ==================== API Keys and Constants ====================
SUPABASE_URL = "https://qdvfntffaorztslkukgb.supabase.co"
SUPABASE_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFkdmZudGZmYW9yenRzbGt1a2diIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDU5NDg4MzUsImV4cCI6MjA2MTUyNDgzNX0.89PKgpdI0ItYQ-4FlY2ZSN5lSnyr0aIMuh4cAPjpKYs"
SUPABASE_TABLE = "articles"

# ==================== Supabase Client ====================
class SupabaseClient:
    def __init__(self):
        """Supabase client'ı başlat"""
        self.supabase = None
        self._init_supabase()
    
    def _init_supabase(self):
        """Supabase bağlantısını başlat"""
        try:
            self.supabase = create_client(SUPABASE_URL, SUPABASE_API_KEY)
            print("✅ Supabase bağlantısı başarılı!")
        except Exception as e:
            print(f"❌ Supabase bağlantı hatası: {e}")
    
    def save_article(self, title: str, url: str, domain: str, keyword: str = None):
        """Article'ı Supabase'e kaydet"""
        try:
            if not self.supabase:
                return None
            
            # Önce article var mı kontrol et
            existing = self.supabase.table('articles').select('id').eq('url', url).execute()
            
            if existing.data:
                article_id = existing.data[0]['id']
                return article_id
            
            # Yeni article ekle
            article_data = {
                'title': title,
                'url': url,
                'domain': domain,
                'keyword': keyword
            }
            
            result = self.supabase.table('articles').insert(article_data).execute()
            
            if result.data and len(result.data) > 0:
                article_id = result.data[0].get('id')
                if article_id:
                    print(f"✅ Article kaydedildi: {title} (ID: {article_id})")
                    return article_id
                else:
                    print(f"❌ Article ID None")
            else:
                print(f"❌ Article kaydedilemedi - data yok")
            
            return None
            
        except Exception as e:
            print(f"❌ Article kaydetme hatası: {e}")
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
                print(f"✅ Article keyword güncellendi: ID {article_id} -> {keyword}")
                return True
            return False
            
        except Exception as e:
            print(f"❌ Keyword güncelleme hatası: {e}")
            return False
    
    def get_domain_articles(self, domain: str):
        """Domain'e ait mevcut article'ları getir"""
        try:
            if not self.supabase:
                return []
            
            result = self.supabase.table('articles').select('id, title, url, keyword').eq('domain', domain).execute()
            
            if result.data:
                print(f"✅ Domain {domain} için {len(result.data)} article bulundu")
                return result.data
            else:
                print(f"⚠️ Domain {domain} için article bulunamadı")
                return []
                
        except Exception as e:
            print(f"❌ Domain article getirme hatası: {e}")
            return []
    
    def has_domain_articles(self, domain: str):
        """Domain'in daha önce taranıp taranmadığını kontrol et"""
        try:
            if not self.supabase:
                return False
            
            result = self.supabase.table('articles').select('id').eq('domain', domain).limit(1).execute()
            return len(result.data) > 0 if result.data else False
                
        except Exception as e:
            print(f"❌ Domain kontrol hatası: {e}")
            return False

# ==================== Async Keyword Generator ====================
class AsyncKeywordGenerator:
    def __init__(self, api_key: str = None, max_concurrent: int = 5):
        """Async keyword generator'ı başlat (OpenRouter)"""
        self.api_key = api_key or OPENROUTER_API_KEY
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        
        if self.api_key:
            self.client = AsyncOpenAI(
                api_key=self.api_key,
                base_url="https://openrouter.ai/api/v1"
            )
        else:
            self.client = None
            print("⚠️ OpenRouter API key bulunamadı")
    
    async def generate_keywords_async(self, url: str, title: str = None, content: str = None):
        """Asenkron keyword üretimi"""
        async with self.semaphore:
            try:
                if not self.client:
                    return self._fallback_keywords(url, title)
                
                prompt = self._create_prompt(url, title, content)
                
                response = await self.client.chat.completions.create(
                    model=GPT_MODEL,
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
                print(f"⚠️ Keyword üretim hatası: {e}")
                return self._fallback_keywords(url, title)
    
    def _create_prompt(self, url: str, title: str = None, content: str = None):
        """Keyword üretimi için prompt oluştur"""
        prompt = f"URL: {url}\n"
        if title:
            prompt += f"Başlık: {title}\n"
        if content:
            prompt += f"İçerik: {content[:1000]}...\n"
        
        prompt += """
Bu URL için SEO dostu, Türkçe keyword'ler üret. Sadece en önemli 1 keyword'ü döndür.
Format: {"keyword": "anahtar kelime"}
"""
        return prompt
    
    def _parse_keywords(self, content: str):
        """GPT yanıtından keyword'leri çıkar"""
        try:
            import json
            # JSON formatında arama
            if "{" in content and "}" in content:
                start = content.find("{")
                end = content.rfind("}") + 1
                json_str = content[start:end]
                data = json.loads(json_str)
                if "keyword" in data:
                    return [{"keyword": data["keyword"], "relevance": 0.9, "category": "general"}]
            
            # Basit text formatında arama
            lines = content.strip().split('\n')
            for line in lines:
                line = line.strip()
                if line and len(line) > 3:
                    return [{"keyword": line, "relevance": 0.8, "category": "general"}]
            
            return []
        except:
            return []
    
    def _fallback_keywords(self, url: str, title: str = None):
        """Fallback keyword'ler"""
        if title:
            return [{"keyword": title, "relevance": 0.5, "category": "fallback"}]
        
        # URL'den keyword çıkar
        from urllib.parse import urlparse
        path = urlparse(url).path
        if path:
            keyword = path.split('/')[-1].replace('-', ' ').replace('_', ' ').title()
            return [{"keyword": keyword, "relevance": 0.3, "category": "url"}]
        
        return [{"keyword": "Genel", "relevance": 0.1, "category": "default"}]

# ==================== Selenium Scraper ====================
class SeleniumScraper:
    def __init__(self):
        """Selenium scraper'ı başlat"""
        self.driver = None
        self.supabase = SupabaseClient()
        self.keyword_generator = AsyncKeywordGenerator()
    
    def _get_selenium_driver(self):
        """Selenium driver'ı başlat (anti-detection)"""
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
                
                self.driver = webdriver.Chrome(options=chrome_options)
                self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                self.driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
                self.driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']})")
                self.driver.set_page_load_timeout(30)
                self.driver.implicitly_wait(10)
            except Exception as e:
                print(f"⚠️ Chrome driver başlatılamadı: {e}")
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
            print("✅ Sayfa tamamen scroll edildi")
        except Exception as e:
            print(f"⚠️ Scroll hatası: {e}")
    
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
            print(f"⚠️ Link çıkarma hatası: {e}")
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
                                print(f"✅ Pagination container bulundu: {selector} (Container {i+1}) - {len(links)} pagination link")
                                return container
                        except Exception as e:
                            continue  # Bu container'ı atla, diğerine geç
                except Exception as e:
                    continue  # Bu selector'ı atla, diğerine geç
            
            print("⚠️ Pagination container bulunamadı")
            return None
            
        except Exception as e:
            print(f"⚠️ Container arama hatası: {e}")
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
                        print(f"✅ Next butonu bulundu: '{text}' - {href}")
                        return link
                    
                    # Rel kontrolü
                    if 'next' in rel.lower():
                        print(f"✅ Next butonu bulundu (rel): '{rel}' - {href}")
                        return link
                    
                    # Aria-label kontrolü
                    if any(next_text in aria_label.lower() for next_text in next_texts):
                        print(f"✅ Next butonu bulundu (aria-label): '{aria_label}' - {href}")
                        return link
                    
                    # Title kontrolü
                    if any(next_text in title.lower() for next_text in next_texts):
                        print(f"✅ Next butonu bulundu (title): '{title}' - {href}")
                        return link
                    
                except Exception as e:
                    continue
            
            print("⚠️ Next butonu bulunamadı")
            return None
            
        except Exception as e:
            print(f"⚠️ Next buton arama hatası: {e}")
            return None
    
    async def next_button_scrape(self, url, generate_keywords: bool = True):
        """Next butonuna tıklayarak pagination scraping"""
        try:
            # Domain kontrolü
            from urllib.parse import urlparse
            domain = urlparse(url).netloc
            
            if self.supabase.has_domain_articles(domain):
                print(f"🔄 Domain {domain} daha önce taranmış!")
                existing_articles = self.supabase.get_domain_articles(domain)
                
                return {
                    'success': True,
                    'blog_links': [article['url'] for article in existing_articles],
                    'pages_scraped': 0,
                    'total_blog_posts': len(existing_articles),
                    'articles_saved': 0,
                    'keywords_updated': 0,
                    'cached': True,
                    'message': f"Domain {domain} daha önce taranmış. {len(existing_articles)} mevcut article bulundu."
                }
            
            driver = self._get_selenium_driver()
            if not driver:
                return {
                    'success': False,
                    'blog_links': [],
                    'pages_scraped': 0,
                    'error': 'Selenium driver başlatılamadı'
                }
            
            print(f"🚀 Next buton scraping başlatılıyor: {url}")
            
            all_blog_links = set()
            pages_scraped = 0
            articles_saved = 0
            saved_articles = []  # (article_id, url, title)
            current_url = url
            
            # İlk sayfayı yükle
            driver.get(current_url)
            time.sleep(3)
            
            while True:
                print(f"📄 Sayfa {pages_scraped + 1} işleniyor: {current_url}")
                
                # Full scroll yap
                self._full_scroll_page(driver)
                
                # Bu sayfadaki tüm linkleri al
                page_links = self._extract_all_links_from_page(driver)
                print(f"🔍 Toplam {len(page_links)} link bulundu")
                
                # Blog linklerini filtrele ve articles tablosuna kaydet
                blog_links = set()
                for link in page_links:
                    if self._is_blog_post_link(link):
                        clean_link = link.split('#')[0]
                        blog_links.add(clean_link)
                        print(f"✅ Blog link: {clean_link}")
                        
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
                                print(f"✅ Article kaydedildi: {title} (ID: {article_id})")
                                saved_articles.append((article_id, clean_link, title))
                            else:
                                print(f"❌ Article kaydedilemedi: {title}")
                                    
                        except Exception as e:
                            print(f"❌ Article kaydetme hatası {clean_link}: {e}")
                
                all_blog_links.update(blog_links)
                print(f"✅ Sayfa {pages_scraped + 1}: {len(blog_links)} blog yazısı bulundu")
                
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
                                print("⚠️ Next buton bulunamadı veya aynı URL")
                                break
                        except Exception as e:
                            print(f"❌ Next buton tıklama hatası: {e}")
                            break
                    else:
                        print("⚠️ Next buton bulunamadı")
                        break
                else:
                    print("⚠️ Pagination container bulunamadı")
                    break
            
            # Toplu keyword üretimi (opsiyonel)
            keywords_updated = 0
            if generate_keywords and saved_articles:
                print(f"🤖 Toplu keyword üretimi başlıyor... ({len(saved_articles)} article)")

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
                                    print(f"✅ Keyword: {title} -> {first_keyword}")
                        except Exception as e:
                            print(f"⚠️ Keyword hatası {title}: {e}")

                tasks = []
                for aid, lnk, ttl in saved_articles:
                    tasks.append(process_one(aid, lnk, ttl))
                await asyncio.gather(*tasks)

            print(f"🎉 {pages_scraped} sayfa tarandı, {len(all_blog_links)} blog yazısı bulundu, {articles_saved} article kaydedildi, {keywords_updated} keyword güncellendi")
            
            return {
                'success': True,
                'blog_links': list(all_blog_links),
                'pages_scraped': pages_scraped,
                'total_blog_posts': len(all_blog_links),
                'articles_saved': articles_saved,
                'keywords_updated': keywords_updated
            }
            
        except Exception as e:
            print(f"❌ Next buton scraping hatası: {e}")
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
    
    async def _force_scrape(self, url, generate_keywords: bool = True):
        """Domain kontrolü olmadan zorla scraping"""
        try:
            driver = self._get_selenium_driver()
            if not driver:
                return {
                    'success': False,
                    'blog_links': [],
                    'pages_scraped': 0,
                    'error': 'Selenium driver başlatılamadı'
                }
            
            print(f"🚀 Force scraping başlatılıyor: {url}")
            
            all_blog_links = set()
            pages_scraped = 0
            articles_saved = 0
            saved_articles = []  # (article_id, url, title)
            current_url = url
            
            # İlk sayfayı yükle
            driver.get(current_url)
            time.sleep(3)
            
            while True:
                print(f"📄 Sayfa {pages_scraped + 1} işleniyor: {current_url}")
                
                # Full scroll yap
                self._full_scroll_page(driver)
                
                # Bu sayfadaki tüm linkleri al
                page_links = self._extract_all_links_from_page(driver)
                print(f"🔍 Toplam {len(page_links)} link bulundu")
                
                # Blog linklerini filtrele ve articles tablosuna kaydet
                blog_links = set()
                for link in page_links:
                    if self._is_blog_post_link(link):
                        clean_link = link.split('#')[0]
                        blog_links.add(clean_link)
                        print(f"✅ Blog link: {clean_link}")
                        
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
                                print(f"✅ Article kaydedildi: {title} (ID: {article_id})")
                                saved_articles.append((article_id, clean_link, title))
                            else:
                                print(f"❌ Article kaydedilemedi: {title}")
                                    
                        except Exception as e:
                            print(f"❌ Article kaydetme hatası {clean_link}: {e}")
                
                all_blog_links.update(blog_links)
                print(f"✅ Sayfa {pages_scraped + 1}: {len(blog_links)} blog yazısı bulundu")
                
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
                                print("⚠️ Next buton bulunamadı veya aynı URL")
                                break
                        except Exception as e:
                            print(f"❌ Next buton tıklama hatası: {e}")
                            break
                    else:
                        print("⚠️ Next buton bulunamadı")
                        break
                else:
                    print("⚠️ Pagination container bulunamadı")
                    break
            
            # Toplu keyword üretimi (opsiyonel)
            keywords_updated = 0
            if generate_keywords and saved_articles:
                print(f"🤖 Toplu keyword üretimi başlıyor... ({len(saved_articles)} article)")

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
                                    print(f"✅ Keyword: {title} -> {first_keyword}")
                        except Exception as e:
                            print(f"⚠️ Keyword hatası {title}: {e}")

                tasks = []
                for aid, lnk, ttl in saved_articles:
                    tasks.append(process_one(aid, lnk, ttl))
                await asyncio.gather(*tasks)

            print(f"🎉 Force scraping tamamlandı: {pages_scraped} sayfa tarandı, {len(all_blog_links)} blog yazısı bulundu, {articles_saved} article kaydedildi, {keywords_updated} keyword güncellendi")
            
            return {
                'success': True,
                'blog_links': list(all_blog_links),
                'pages_scraped': pages_scraped,
                'total_blog_posts': len(all_blog_links),
                'articles_saved': articles_saved,
                'keywords_updated': keywords_updated,
                'cached': False
            }
            
        except Exception as e:
            print(f"❌ Force scraping hatası: {e}")
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

UNSPLASH_ACCESS_KEY = "Uxa5kcrc5cowwfkAQA1TOnjqUK7yGuM5z3AKztJ_cpE"
OPENROUTER_API_KEY = "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"
GPT_MODEL = "google/gemini-2.0-flash-001"
DEEPL_KEY = "721f4e0a-7600-425a-9bd4-7c4282e7770c:fx"
SERP_API_KEY = "d378363e8fbf685794a5463f509ad88318551b8ff5a74164782b8ec8788dec02"
USE_GPT_MOCK = False

STOPWORDS = set([
    "ve", "de", "da", "bir", "bu", "şu", "ile", "gibi", "veya", "ama", "fakat", "çünkü", "ki",
    "daha", "çok", "az", "en", "değil", "mi", "mı", "mu", "mü", "ya", "ya da", "hem", "hem de",
    "o", "onu", "ona", "onun", "onlar", "onların", "onlara", "onları"
])


# ==================== Part 1: Linkify Functions ====================

def normalize_turkish(text):
    replacements = {
        'ğ': 'g', 'ü': 'u', 'ş': 's', 'ı': 'i', 'ç': 'c', 'ö': 'o',
        'Ğ': 'G', 'Ü': 'U', 'Ş': 'S', 'I': 'I', 'Ç': 'C', 'Ö': 'O'
    }
    for key, value in replacements.items():
        text = text.replace(key, value)
    return text


def get_article_titles_from_db():
    headers = {
        "apikey": SUPABASE_API_KEY,
        "Authorization": f"Bearer {SUPABASE_API_KEY}",
        "Content-Type": "application/json"
    }
    try:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/{SUPABASE_TABLE}?select=keyword,url",
            headers=headers
        )
        if response.status_code == 200:
            print("article db", response.json())
            return response.json()
        else:
            print("Supabase fetch error:", response.text)
            return []
    except Exception as e:
        print("Supabase connection error:", e)
        return []


def normalize(text):
    # Küçük harfe çevir, baştaki/sondaki boşlukları temizle
    return re.sub(r'\s+', ' ', text.lower().strip())


def is_stopword_or_short(text):
    # Sadece stopword veya 3 harften kısa ise True döner
    words = text.split()
    return (
            all(w in STOPWORDS for w in words) or
            any(len(w) < 3 for w in words)
    )


def linkify_text_with_db(text):
    articles = get_article_titles_from_db()
    if not articles:
        return text

    original_text = text
    normalized_text = normalize_turkish(normalize(text))

    # İçindekiler bölümünü tespit et ve koruma altına al
    protected_sections = _extract_protected_sections(original_text)
    
    # Korumalı bölümleri geçici olarak değiştir
    temp_text = original_text
    for i, section in enumerate(protected_sections):
        temp_text = temp_text.replace(section, f"__PROTECTED_SECTION_{i}__")

    valid_titles = []
    for article in articles:
        keyword_norm = normalize_turkish(normalize(article['keyword']))
        if not is_stopword_or_short(keyword_norm):
            valid_titles.append((keyword_norm, article['keyword'], article['url']))
    valid_titles.sort(key=lambda x: -len(x[0].split()))

    used_keywords = set()
    for keyword_norm, original_keyword, url in valid_titles:
        if keyword_norm in used_keywords:
            continue

        if re.search(r'\b' + re.escape(keyword_norm) + r'\b', normalize_turkish(normalize(temp_text)), flags=re.IGNORECASE):
            pattern = r'\b' + re.escape(original_keyword) + r'\b'

            def replacer(match):
                used_keywords.add(keyword_norm)
                return f'[{match.group(0)}]({url})'

            temp_text, n = re.subn(pattern, replacer, temp_text, count=1, flags=re.IGNORECASE)
    
    # Korumalı bölümleri geri yükle
    final_text = temp_text
    for i, section in enumerate(protected_sections):
        final_text = final_text.replace(f"__PROTECTED_SECTION_{i}__", section)
    
    print(final_text)
    return final_text


def _extract_protected_sections(text):
    """İçindekiler bölümlerini tespit et ve koruma altına al"""
    protected_sections = []
    
    # İçindekiler başlığı ve altındaki liste
    patterns = [
        # Türkçe içindekiler
        r'(İçindekiler\s*\n\s*[•\-\*]\s*.*?)(?=\n\n|\n[A-ZÜĞŞÇÖİ]|\Z)',
        r'(İçindekiler\s*\n\s*[•\-\*]\s*.*?)(?=\n\s*[A-ZÜĞŞÇÖİ][a-züğşçöı]|\Z)',
        # İngilizce table of contents
        r'(Table of Contents\s*\n\s*[•\-\*]\s*.*?)(?=\n\n|\n[A-Z]|\Z)',
        r'(Contents\s*\n\s*[•\-\*]\s*.*?)(?=\n\n|\n[A-Z]|\Z)',
        # Genel liste yapıları (başlık + liste)
        r'((?:İçindekiler|Table of Contents|Contents|Liste|List)\s*\n\s*[•\-\*]\s*.*?)(?=\n\s*[A-ZÜĞŞÇÖİ]|\Z)',
    ]
    
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.MULTILINE | re.DOTALL | re.IGNORECASE)
        for match in matches:
            section = match.group(1).strip()
            if len(section) > 50:  # Çok kısa bölümleri atla
                protected_sections.append(section)
    
    return protected_sections


# ==================== Image Functions ====================

def translate_to_english(text):
    url = "https://api-free.deepl.com/v2/translate"
    data = {
        'auth_key': DEEPL_KEY,
        'text': text,
        'source_lang': 'TR',
        'target_lang': 'EN'
    }
    response = requests.post(url, data=data)
    result = response.json()
    return result['translations'][0]['text']


def fetch_unsplash_images(query, count=10):
    url = "https://api.unsplash.com/search/photos"
    params = {
        "query": query,
        "per_page": count,
        "client_id": UNSPLASH_ACCESS_KEY
    }
    response = requests.get(url, params=params)
    data = response.json()

    return [result["urls"]["regular"] for result in data.get("results", [])]


def select_top_3_images(image_urls, query):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": (
                        f"Aşağıda '{query}' konusuyla ilgili 10 görselin URL'leri verilmiştir:\n\n"
                        f"{chr(10).join(image_urls)}\n\n"
                        f"Lütfen bu listedeki URL'lerden sadece konuyla en alakalı ve en güzel görünen 3 tanesini seç. Medikal ve tıbbi olanları seçmeni istiyorum. "
                        f"ve sadece bu 3 URL'yi satır satır olacak şekilde döndür. Başka açıklama yazma."
                    )
                }
            ]
        }
    ]

    payload = {
        "model": GPT_MODEL,
        "messages": messages,
    }

    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
    response.raise_for_status()
    output = response.json()["choices"][0]["message"]["content"]

    urls = [line.strip() for line in output.strip().splitlines() if "http" in line]
    return urls[:3]


# ==================== Content with Images Placement ====================

def place_images_in_content(content, image_urls, main_topic):
    """Place images within content with GPT's help"""

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": (
                        f"Aşağıdaki içeriğe 3 adet resim eklemen gerekiyor:\n\n"
                        f"İÇERİK:\n{content}\n\n"
                        f"GÖRSELLER (3 adet):\n{chr(10).join(image_urls)}\n\n"
                        f"Lütfen şu şekilde görsel yerleştirme yap:\n"
                        f"1. İlk görseli içeriğin en başına ekle\n"
                        f"2. Diğer iki görselin her birini farklı farklı uygun alt başlıkların hemen üstüne ekle\n\n"
                        f"Yerleştirme yaparken kullanılabilir HTML img etiketleri şu format olmalı:\n"
                        f"<img src=\"URL\" alt=\"{main_topic} ile ilgili görsel\" />\n\n"
                        f"Sadece orijinal içeriğin img etiketleri eklenmiş halini döndür. Başka açıklama yapma."
                    )
                }
            ]
        }
    ]

    payload = {
        "model": GPT_MODEL,
        "messages": messages,
    }

    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
    response.raise_for_status()

    return response.json()["choices"][0]["message"]["content"]


# ==================== Part 2: Similar Titles Functions ====================

def fetch_google_results(query):
    print("\n" + "=" * 70)
    print(f"🔍 SEARCHING GOOGLE FOR: {query}")
    print("📍 Location: Istanbul, Turkey")
    print("=" * 70)

    params = {
        "engine": "google",
        "q": query,
        "api_key": SERP_API_KEY,
        "num": 20,
        "location": "Istanbul,Istanbul,Turkey",
        "hl": "tr",  # Interface language
        "gl": "tr",  # Country for Google search
        "google_domain": "google.com.tr"
    }

    try:
        print("\n📡 Sending request to SerpAPI...")
        search = GoogleSearch(params)
        results = search.get_dict()
        urls = []

        if "organic_results" in results:
            print("\n📑 FOUND SEARCH RESULTS:")
            print("-" * 50)

            for i, res in enumerate(results["organic_results"], 1):
                url = res["link"]
                title = res.get("title", "No title")
                snippet = res.get("snippet", "No snippet")

                if "memorial.com.tr" not in url and "memorial" not in url:
                    urls.append(url)
                    print(f"\n✅ Result {i}:")
                    print(f"🔗 URL: {url}")
                    print(f"📌 Title: {title}")
                    print(f"📝 Snippet: {snippet}")
                else:
                    print(f"\n❌ SKIPPED Result {i}:")
                    print(f"🔗 URL: {url}")
                    print("Reason: Memorial domain filtered")

                if len(urls) >= 20:
                    break

            print(f"\n📊 Total valid URLs found: {len(urls)}")
            print("-" * 50)
        else:
            print("\n❌ NO RESULTS FOUND!")
            if "error" in results:
                print(f"Error message: {results['error']}")

        return urls

    except Exception as e:
        print(f"\n❌ ERROR in Google search: {str(e)}")
        return []


def take_headings_from_url(url):
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True,
                                        args=['--disable-gpu', '--no-sandbox', '--disable-dev-shm-usage'])
            context = browser.new_context(
                viewport={'width': 1280, 'height': 800},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            )
            page = context.new_page()

            try:
                page.goto(url, wait_until='networkidle', timeout=30000)
                headings = page.query_selector_all("h1, h2")
                heading_texts = [h.inner_text().strip() for h in headings if h.inner_text().strip()]
                return heading_texts
            except Exception as e:
                print(f"❌ Page navigation error ({url}): {e}")
                return []
            finally:
                context.close()
                browser.close()

    except Exception as e:
        print(f"❌ Playwright initialization error ({url}): {e}")
        return []


def ask_gpt_similar_titles(texts, query, subheading_count):
    if USE_GPT_MOCK:
        print("\n⚙️ MOCK MODE ACTIVE")
        return "\n".join([f"Başlık {i + 1}" for i in range(subheading_count)])

    print("\n" + "=" * 70)
    print(f"🤖 GENERATING TITLES WITH GPT FOR: {query}")
    print(f"📊 Requested number of titles: {subheading_count}")
    print("=" * 70)

    prompt = f"""
Konu: {query}

Aşağıda verilen 5 sayfadan alınan içeriklere göre, yalnızca '{query}' konusuna odaklanarak {subheading_count} adet alt başlık öner.
Bu başlıklar:
- Konuyla doğrudan ilgili olmalı
- Birbirinden farklı açıları ele almalı
- SEO dostu olmalı
- Türkçe dilbilgisi kurallarına uygun olmalı
- Okuyucunun merakını çekecek şekilde olmalı
Sadece başlıkları sırasız ve liste halinde ver. Açıklama ekleme.
"""

    for i, text in enumerate(texts[:10], 1):  # Limit to first 10 texts
        prompt += f"\n---\nSayfa {i}:\n{text[:2000]}\n"  # Limit each text to 1000 chars

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "http://localhost:5000",
        "Content-Type": "application/json"
    }

    payload = {
        "model": GPT_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 2000
    }

    try:
        print("\n📤 Sending request to OpenRouter API...")
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=60
        )
        response.raise_for_status()

        data = response.json()
        print("✅ Received response from OpenRouter API")

        if "choices" in data and len(data["choices"]) > 0:
            content = data["choices"][0]["message"]["content"]
            if not content or not content.strip():
                print("❌ Empty content received from OpenRouter API")
                return None

            print("\n📝 RAW GPT RESPONSE:")
            print("-" * 50)
            print(content)
            print("-" * 50)

            return content
        else:
            print("❌ Invalid response format from OpenRouter API")
            return None

    except requests.exceptions.RequestException as e:
        print(f"❌ Network error with OpenRouter API: {str(e)}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error in ask_gpt_similar_titles: {str(e)}")
        return None


def extract_titles_from_gpt_response(response):
    print("\n" + "=" * 70)
    print("🎯 PROCESSING GPT RESPONSE")
    print("=" * 70)

    if not response or not isinstance(response, str):
        print(f"❌ Invalid response type: {type(response)}")
        return []

    try:
        # Split into lines and clean up
        lines = [line.strip() for line in response.strip().split('\n')]
        titles = []

        print("\n📋 EXTRACTED TITLES:")
        print("-" * 50)

        for line in lines:
            # Skip empty lines
            if not line:
                continue

            # Remove common list markers and numbering
            line = re.sub(r'^[-•*\d.]+\s*', '', line)
            line = line.strip()

            # Validate the title
            if line and len(line) >= 3 and len(line.split()) >= 1:
                # Clean up any remaining special characters
                line = re.sub(r'[^\w\s\-üğışçöĞÜŞİÇÖ]', ' ', line)
                line = re.sub(r'\s+', ' ', line).strip()

                if line:
                    titles.append(line)
                    print(f"✅ {len(titles)}. {line}")
            else:
                print(f"❌ Skipped invalid title: {line}")

        print(f"\n📊 Total valid titles extracted: {len(titles)}")
        print("=" * 70)
        return titles

    except Exception as e:
        print(f"❌ Error extracting titles: {str(e)}")
        return []


def take_text_from_url(url):
    try:
        print(f"\n🌐 Processing URL: {url}")
        print("=" * 50)

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
        }

        response = requests.get(url, headers=headers, timeout=45, verify=True)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser", from_encoding=response.encoding)

        # Remove script and style elements
        for element in soup(["script", "style"]):
            element.decompose()

        # Get h1 headings
        h1_headings = soup.find_all('h1')
        h1_texts = [heading.get_text(separator=' ', strip=True) for heading in h1_headings if
                    heading.get_text(strip=True)]

        # Get h2 headings
        h2_headings = soup.find_all('h2')
        h2_texts = [heading.get_text(separator=' ', strip=True) for heading in h2_headings if
                    heading.get_text(strip=True)]

        print(f"\n📝 Found {len(h1_texts)} H1 headings and {len(h2_texts)} H2 headings")
        print("-" * 50)

        if h1_texts:
            print("\n🔷 H1 HEADINGS:")
            print("-" * 30)
            for i, heading in enumerate(h1_texts, 1):
                print(f"{i}. {heading}")

        if h2_texts:
            print("\n🔶 H2 HEADINGS:")
            print("-" * 30)
            for i, heading in enumerate(h2_texts, 1):
                print(f"{i}. {heading}")

        # Combine all headings
        all_texts = h1_texts + h2_texts

        if not all_texts:
            print("\n⚠️ NO HEADINGS FOUND IN THIS PAGE!")

        print("\n" + "=" * 50)
        return ' '.join(all_texts).strip()

    except requests.exceptions.RequestException as e:
        print(f"❌ Network error for {url}: {str(e)}")
        return ""
    except Exception as e:
        print(f"❌ Error processing {url}: {str(e)}")
        return ""


# ==================== API Routes ====================

# Route for Part 1: Linkify with Images
@app.route('/linkify-with-images', methods=['POST'])
def linkify_with_images_api():
    start_time = time.time()

    try:
        # Get and validate input
        if request.is_json:
            data = request.get_json()
            user_text = data.get('text', '')
            main_topic = data.get('topic', '')
        else:
            user_text = request.form.get('text', '')
            main_topic = request.form.get('topic', '')

        if not user_text:
            return jsonify({"error": "Missing 'text' field"}), 400

        if not main_topic:
            # If topic is not specified, guess from first sentence or part of content
            main_topic = user_text.split('.')[0] if '.' in user_text else user_text[:50]

        # Process the content
        try:
            # 1. Add links to text
            app.logger.info("Step 1: Adding links to text")
            linked_text = linkify_text_with_db(user_text)

            # 2. Translate main topic
            app.logger.info("Step 2: Translating topic")
            translated_topic = translate_to_english(main_topic)
            app.logger.info(f"Translated topic: {translated_topic}")

            # 3. Fetch images
            app.logger.info("Step 3: Fetching images")
            all_images = fetch_unsplash_images(translated_topic)
            app.logger.info(f"Found {len(all_images)} images")

            # 4. Select best images
            app.logger.info("Step 4: Selecting best images")
            top_images = select_top_3_images(all_images, main_topic)
            app.logger.info(f"Selected {len(top_images)} top images")

            # 5. Place images in content
            app.logger.info("Step 5: Placing images in content")
            final_content = place_images_in_content(linked_text, top_images, main_topic)

            return jsonify({
                "content_with_images": final_content,
                "processing_time_seconds": time.time() - start_time
            })

        except Exception as e:
            app.logger.error(f"Error during content enrichment: {str(e)}")
            return jsonify({
                "error": "Content enrichment failed",
                "details": str(e),
                "linked_text": linked_text if 'linked_text' in locals() else None,
                "processing_time_seconds": time.time() - start_time
            }), 500

    except Exception as e:
        app.logger.error(f"Error processing request: {str(e)}")
        return jsonify({
            "error": "Request processing failed",
            "details": str(e),
            "processing_time_seconds": time.time() - start_time
        }), 500


# Route for Part 1: Simple linkify
@app.route('/linkify', methods=['POST', 'GET'])
def linkify_api():
    start_time = time.time()

    if request.is_json:
        data = request.get_json()
        user_text = data.get('text', '')
    else:
        user_text = request.form.get('text', '')

    if not user_text:
        return jsonify({"error": "Missing 'text' field"}), 400

    linked_text = linkify_text_with_db(user_text)
    processing_time = time.time() - start_time

    return jsonify({
        "linked_text": linked_text,
        "processing_time_seconds": processing_time
    })


# Route for Part 1: Select images
@app.route("/select-images", methods=["POST"])
def select_images():
    data = request.get_json()
    query = data.get("query")

    if not query:
        return jsonify({"error": "Query is required"}), 400

    try:
        translated_query = translate_to_english(query)
        all_images = fetch_unsplash_images(translated_query)
        top_images = select_top_3_images(all_images, query)

        return jsonify({
            "selected_image_tags": [f'<img src="{url}" alt="image" />' for url in top_images],
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Route for Scraping
@app.route("/scrape", methods=["GET"])
def scrape_website():
    """Website scraping endpoint"""
    try:
        url = request.args.get("url")
        force = request.args.get("force", "false").lower() == "true"
        
        if not url:
            return jsonify({"error": "URL parameter is required"}), 400
        
        # URL'yi temizle
        clean_url = url.replace('https://https://', 'https://')
        if not clean_url.startswith(('http://', 'https://')):
            clean_url = 'https://' + clean_url
        
        print(f"🚀 Scraping başlatılıyor: {clean_url}")
        
        # Async fonksiyonu çalıştır
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            scraper = SeleniumScraper()
            
            # Force parametresi varsa domain kontrolünü atla
            if force:
                print("🔄 Force mode: Domain kontrolü atlanıyor")
                result = loop.run_until_complete(scraper._force_scrape(clean_url, generate_keywords=True))
            else:
                result = loop.run_until_complete(scraper.next_button_scrape(clean_url, generate_keywords=True))
            
            if result['success']:
                # Cached response için özel mesaj
                if result.get('cached', False):
                    message = result.get('message', 'Domain daha önce taranmış')
                else:
                    message = f"{result['pages_scraped']} sayfa tarandı, {result['total_blog_posts']} blog yazısı bulundu, {result['articles_saved']} article kaydedildi, {result.get('keywords_updated', 0)} keyword güncellendi"
                
                return jsonify({
                    "success": True,
                    "message": message,
                    "cached": result.get('cached', False),
                    "data": {
                        "pages_scraped": result['pages_scraped'],
                        "total_blog_posts": result['total_blog_posts'],
                        "articles_saved": result['articles_saved'],
                        "keywords_updated": result.get('keywords_updated', 0),
                        "blog_links": result['blog_links'][:10],  # İlk 10 link
                        "cached": result.get('cached', False)
                    }
                })
            else:
                return jsonify({
                    "success": False,
                    "message": f"Scraping hatası: {result.get('error', 'Bilinmeyen hata')}",
                    "data": {}
                }), 500
                
        finally:
            loop.close()
            
    except Exception as e:
        print(f"❌ API hatası: {e}")
        return jsonify({
            "success": False,
            "message": f"API hatası: {str(e)}",
            "data": {}
        }), 500

# Route for Part 2: Similar Titles
@app.route("/similar-titles", methods=["GET"])
def get_similar_titles():
    try:
        # Safely get and validate query parameter
        query = request.args.get("query")
        if not query:
            return jsonify({"error": "Query parameter is required"}), 400

        # Ensure query is properly encoded string
        try:
            query = str(query).encode('utf-8', errors='ignore').decode('utf-8')
        except Exception as e:
            return jsonify({"error": "Invalid query parameter encoding"}), 400

        word_count = request.args.get("word_count", default=2000, type=int)
        if word_count < 0:
            return jsonify({"error": "Word count must be a positive number"}), 400

        app.logger.info(f"Processing query: {query}")
        app.logger.info(f"Target word count: {word_count}")

        # Fetch URLs with error handling
        try:
            urls = fetch_google_results(query)
            if not urls:
                return jsonify({"error": "No relevant search results found"}), 404
            app.logger.info(f"Found {len(urls)} URLs to process")
        except Exception as e:
            app.logger.error(f"Error fetching Google results: {str(e)}")
            return jsonify({"error": "Failed to fetch search results"}), 500

        # Process URLs and get texts
        raw_texts = []
        for url in urls:
            try:
                text = take_text_from_url(url)
                if text and text.strip():
                    # Ensure text is properly encoded
                    text = text.encode('utf-8', errors='ignore').decode('utf-8')
                    raw_texts.append(text)
            except Exception as e:
                app.logger.error(f"Error processing URL {url}: {str(e)}")
                continue

        if not raw_texts:
            return jsonify({"error": "Could not extract content from any URLs"}), 404

        # Determine subheading count based on word count
        if 2000 <= word_count <= 2500:
            subheading_count = 20
        elif 1500 <= word_count < 2000:
            subheading_count = 15
        elif 2500 < word_count <= 3000:
            subheading_count = 25
        else:
            subheading_count = 12

        # Get titles from GPT
        try:
            result = ask_gpt_similar_titles(raw_texts, query, subheading_count)
            if not result:
                return jsonify({"error": "Could not generate titles"}), 500

            titles = extract_titles_from_gpt_response(result)
            if not titles:
                return jsonify({"error": "No valid titles were generated"}), 500

            # Ensure titles are properly encoded
            titles = [title.encode('utf-8', errors='ignore').decode('utf-8') for title in titles]
            return jsonify({"similar_titles": titles})

        except Exception as e:
            app.logger.error(f"Error generating titles: {str(e)}")
            return jsonify({"error": "Failed to generate titles"}), 500

    except Exception as e:
        app.logger.error(f"Unexpected error in similar-titles route: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


# Test routes
@app.route("/test")
def test():
    return "Test başarılı! Servis çalışıyor.", 200

@app.route("/test-linkify", methods=["POST"])
def test_linkify_protection():
    """İçindekiler korumasını test et"""
    sample_text = """İçindekiler

• Giriş
• Kemoterapi Nedir ve Nasıl Etki Eder
• Kemoterapinin Kanser Türlerine Göre Kullanımı
• Kemoterapi Çeşitleri ve Size Uygun Tedavi Hangisi
• Kemoterapi Yan Etkileriyle Başa Çıkma Yolları
• Kemoterapi Süreci: Seanslar, Süre ve Beklentiler
• Kemoterapi Sonrası İyileşme: Nelere Dikkat Etmeli
• Kemoterapi ve Beslenme: Tedavi Sürecinde Nasıl Beslenmeli
• Kemoterapi Psikolojinizi Nasıl Etkiler? Destek ve Yardım
• Radyoterapi mi Kemoterapi mi? Farkları ve Seçenekler
• Kemoterapi Kimlere Uygulanır? Uygun Adaylar Kimlerdir
• Sıcak Kemoterapi: Yeni Nesil Tedavi Yöntemi Nedir?
• Kemoterapi Hakkında Sıkça Sorulan Sorular ve Cevapları

Kemoterapi, kanser tedavisinde kullanılan en yaygın yöntemlerden biridir. Bu tedavi yöntemi, kanser hücrelerini yok etmek veya büyümelerini durdurmak için güçlü ilaçlar kullanır."""
    
    result = linkify_text_with_db(sample_text)
    
    return jsonify({
        "original_text": sample_text,
        "linkified_text": result,
        "protection_working": "İçindekiler" in result and "•" in result and not any(word in result for word in ["[Giriş]", "[Kemoterapi Nedir]", "[Kemoterapinin Kanser]"])
    })


@app.route("/")
def home():
    return "Content Enrichment API - Tüm rotalar aktif.", 200


@app.route("/test-openrouter")
def test_openrouter():
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "HTTP-Referer": "http://localhost:5000",
            "Content-Type": "application/json"
        }

        payload = {
            "model": GPT_MODEL,
            "messages": [{"role": "user", "content": "Say 'Hello World'"}],
            "temperature": 0.7,
            "max_tokens": 50
        }

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=10
        )
        response.raise_for_status()

        return jsonify({
            "status": "success",
            "response": response.json()
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


@app.route("/test-linkify", methods=["GET"])
def test_linkify():
    sample_request = {
        "text": "Diyabet hastalığı önemli bir sağlık sorunudur. Hipertansiyon ile birlikte görülebilir. Düzenli egzersiz ve sağlıklı beslenme önemlidir.",
        "topic": "Diyabet ve Sağlıklı Yaşam"
    }

    sample_response = {
        "example_request": sample_request,
        "instructions": {
            "method": "POST",
            "url": "/linkify-with-images",
            "headers": {
                "Content-Type": "application/json"
            },
            "body": sample_request
        }
    }

    return jsonify(sample_response)


if __name__ == '__main__':
    import logging
    import os
    
    # Environment detection
    is_production = os.getenv('FLASK_ENV') == 'production'
    
    # Configure logging
    if is_production:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            handlers=[
                logging.FileHandler('/app/logs/app.log'),
                logging.StreamHandler()
            ]
        )
    else:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    # Set Flask logger
    app.logger.handlers = []
    app.logger.propagate = True

    # Add console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    app.logger.addHandler(console_handler)

    # Print startup message
    print("=" * 50)
    print("🚀 Starting Content Enrichment API...")
    print(f"🌍 Environment: {'Production' if is_production else 'Development'}")
    print(f"🔗 Host: 0.0.0.0")
    print(f"🔌 Port: 5000")
    print("=" * 50)

    # Run application
    app.run(
        debug=not is_production,
        host="0.0.0.0",
        port=5000,
        threaded=True
    )