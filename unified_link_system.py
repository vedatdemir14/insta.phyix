#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unified Link System - Tüm sistemi tek dosyada toplar
Link Scraper + Keyword Generator + Text Linkifier + Supabase Client + API Client
"""

import requests
import json
import time
import sys
import argparse
import asyncio
import aiohttp
import re
import unicodedata
from typing import List, Dict, Set, Tuple, Optional, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from datetime import datetime
from colorama import init, Fore, Style
from supabase import create_client, Client

# Selenium imports (optional)
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

# Colorama'yı başlat
init(autoreset=True)

# =============================================================================
# SUPABASE CLIENT
# =============================================================================

class SupabaseClient:
    def __init__(self):
        """Supabase client'ını başlat"""
        self.url = "https://qdvfntffaorztslkukgb.supabase.co"
        self.key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFkdmZudGZmYW9yenRzbGt1a2diIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDU5NDg4MzUsImV4cCI6MjA2MTUyNDgzNX0.89PKgpdI0ItYQ-4FlY2ZSN5lSnyr0aIMuh4cAPjpKYs"
        
        try:
            self.supabase: Client = create_client(self.url, self.key)
            print(f"{Fore.GREEN}[SUPABASE]{Style.RESET_ALL} Bağlantı başarılı!")
        except Exception as e:
            print(f"{Fore.YELLOW}[SUPABASE WARNING]{Style.RESET_ALL} Bağlantı hatası: {e}")
            self.supabase = None
    
    def create_scraping_session(self, base_url: str, domain: str, depth: int = 1) -> Optional[int]:
        """Yeni bir scraping oturumu oluştur"""
        if not self.supabase:
            return None
        try:
            result = self.supabase.table('scraping_sessions').insert({
                'base_url': base_url,
                'domain': domain,
                'scraping_depth': depth,
                'status': 'running'
            }).execute()
            
            if result.data:
                session_id = result.data[0]['id']
                print(f"{Fore.GREEN}[SUPABASE]{Style.RESET_ALL} Oturum oluşturuldu: {session_id}")
                return session_id
            return None
        except Exception as e:
            print(f"{Fore.RED}[SUPABASE ERROR]{Style.RESET_ALL} Oturum oluşturma hatası: {e}")
            return None
    
    def update_session_status(self, session_id: int, status: str, total_links: int = 0, total_pages: int = 0):
        """Scraping oturumunun durumunu güncelle"""
        try:
            update_data = {
                'status': status,
                'total_links_found': total_links,
                'total_pages_visited': total_pages
            }
            
            if status == 'completed':
                update_data['completed_at'] = datetime.now().isoformat()
            
            self.supabase.table('scraping_sessions').update(update_data).eq('id', session_id).execute()
            print(f"{Fore.GREEN}[SUPABASE]{Style.RESET_ALL} Oturum güncellendi: {status}")
        except Exception as e:
            print(f"{Fore.RED}[SUPABASE ERROR]{Style.RESET_ALL} Oturum güncelleme hatası: {e}")
    
    def save_link(self, url: str, domain: str = None, 
                  content_type: str = None, status_code: int = None, 
                  content_length: int = None) -> Optional[int]:
        """Link'i veritabanına kaydet (title olmadan)"""
        try:
            print(f"{Fore.CYAN}[SUPABASE DEBUG]{Style.RESET_ALL} save_link çağrıldı: {url}")
            
            if not self.supabase:
                print(f"{Fore.RED}[SUPABASE ERROR]{Style.RESET_ALL} Supabase client bağlantısı yok!")
                return None
            
            # Önce link var mı kontrol et
            existing = self.supabase.table('links').select('id').eq('url', url).execute()
            
            if existing.data:
                link_id = existing.data[0]['id']
                print(f"{Fore.YELLOW}[SUPABASE]{Style.RESET_ALL} Link zaten mevcut: {url} (ID: {link_id})")
                return link_id
            
            # Yeni link ekle (title olmadan)
            link_data = {
                'url': url,
                'domain': domain,
                'content_type': content_type,
                'status_code': status_code,
                'content_length': content_length,
                'is_processed': False
            }
            
            result = self.supabase.table('links').insert(link_data).execute()
            
            if result.data:
                link_id = result.data[0]['id']
                print(f"{Fore.GREEN}[SUPABASE]{Style.RESET_ALL} Link kaydedildi: {url} (ID: {link_id})")
                return link_id
            else:
                print(f"{Fore.RED}[SUPABASE ERROR]{Style.RESET_ALL} Insert işlemi başarısız - data yok")
                return None
        except Exception as e:
            print(f"{Fore.RED}[SUPABASE ERROR]{Style.RESET_ALL} Link kaydetme hatası: {e}")
            return None
    
    def save_article(self, title: str, url: str, domain: str, keyword: str = None):
        """Article'ı Supabase'e kaydet"""
        try:
            print(f"{Fore.CYAN}[SUPABASE DEBUG]{Style.RESET_ALL} save_article çağrıldı: {title}")
            
            if not self.supabase:
                print(f"{Fore.RED}[SUPABASE ERROR]{Style.RESET_ALL} Supabase client bağlantısı yok!")
                return None
            
            # Önce article var mı kontrol et
            existing = self.supabase.table('articles').select('id').eq('url', url).execute()
            
            if existing.data:
                article_id = existing.data[0]['id']
                print(f"{Fore.YELLOW}[SUPABASE]{Style.RESET_ALL} Article zaten mevcut: {url} (ID: {article_id})")
                return article_id
            
            # Yeni article ekle (sadece mevcut kolonlar)
            article_data = {
                'title': title,
                'url': url,
                'domain': domain,
                'keyword': keyword
            }
            
            result = self.supabase.table('articles').insert(article_data).execute()
            
            print(f"{Fore.CYAN}[SUPABASE DEBUG]{Style.RESET_ALL} Insert result: {result}")
            print(f"{Fore.CYAN}[SUPABASE DEBUG]{Style.RESET_ALL} Result data: {result.data}")
            
            # Error kontrolü
            if hasattr(result, 'error') and result.error:
                print(f"{Fore.RED}[SUPABASE ERROR]{Style.RESET_ALL} Error: {result.error}")
                return None
            
            if result.data and len(result.data) > 0:
                article_id = result.data[0].get('id')
                if article_id:
                    print(f"{Fore.GREEN}[SUPABASE]{Style.RESET_ALL} Article kaydedildi: {title} (ID: {article_id})")
                    return article_id
                else:
                    print(f"{Fore.YELLOW}[SUPABASE WARNING]{Style.RESET_ALL} Article kaydedildi ama ID None: {title}")
                    return None
            else:
                print(f"{Fore.RED}[SUPABASE ERROR]{Style.RESET_ALL} Article insert işlemi başarısız - data yok veya boş")
                return None
        except Exception as e:
            print(f"{Fore.RED}[SUPABASE ERROR]{Style.RESET_ALL} Article kaydetme hatası: {e}")
            return None
    
    def update_article_keyword(self, article_id: int, keyword: str):
        """Article'ın keyword'ünü güncelle"""
        try:
            if not self.supabase:
                print(f"{Fore.RED}[SUPABASE ERROR]{Style.RESET_ALL} Supabase client bağlantısı yok!")
                return False
            
            # Article'ın keyword'ünü güncelle (sadece mevcut kolonlar)
            result = self.supabase.table('articles').update({
                'keyword': keyword
            }).eq('id', article_id).execute()
            
            if result.data:
                print(f"{Fore.GREEN}[SUPABASE]{Style.RESET_ALL} Article keyword güncellendi: ID {article_id} -> {keyword}")
                return True
            else:
                print(f"{Fore.RED}[SUPABASE ERROR]{Style.RESET_ALL} Article keyword güncellenemedi: ID {article_id}")
                return False
        except Exception as e:
            print(f"{Fore.RED}[SUPABASE ERROR]{Style.RESET_ALL} Article keyword güncelleme hatası: {e}")
            return False
    
    def save_keywords(self, link_id: int, keywords: List[Dict[str, any]]):
        """Link için keyword'leri kaydet"""
        try:
            # Önce mevcut keyword'leri sil
            self.supabase.table('keywords').delete().eq('link_id', link_id).execute()
            
            # Yeni keyword'leri ekle
            keyword_data = []
            for kw in keywords:
                keyword_data.append({
                    'link_id': link_id,
                    'keyword': kw.get('keyword', ''),
                    'relevance_score': kw.get('relevance_score', 1.0),
                    'source': kw.get('source', 'ai_generated')
                })
            
            if keyword_data:
                result = self.supabase.table('keywords').insert(keyword_data).execute()
                print(f"{Fore.GREEN}[SUPABASE]{Style.RESET_ALL} {len(keyword_data)} keyword kaydedildi")
            
        except Exception as e:
            print(f"{Fore.RED}[SUPABASE ERROR]{Style.RESET_ALL} Keyword kaydetme hatası: {e}")
    
    def get_links_by_domain(self, domain: str) -> List[Dict]:
        """Domain'e göre linkleri getir"""
        try:
            result = self.supabase.table('links').select('*').eq('domain', domain).execute()
            return result.data if result.data else []
        except Exception as e:
            print(f"{Fore.RED}[SUPABASE ERROR]{Style.RESET_ALL} Link getirme hatası: {e}")
            return []
    
    def search_links_by_keyword(self, keyword: str) -> List[Dict]:
        """Keyword'e göre linkleri ara"""
        try:
            result = self.supabase.table('keywords').select('*, links(*)').ilike('keyword', f'%{keyword}%').execute()
            return result.data if result.data else []
        except Exception as e:
            print(f"{Fore.RED}[SUPABASE ERROR]{Style.RESET_ALL} Keyword arama hatası: {e}")
            return []

# =============================================================================
# LINK SCRAPER
# =============================================================================

class LinkScraper:
    def __init__(self, base_url, max_depth=2, delay=1, max_workers=10):
        """Link scraper sınıfı"""
        # URL'yi temizle
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
        
        # SSL verification'ı kapat (bazı siteler için)
        self.session.verify = False
        
        # Warnings'leri kapat
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
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
        
        self.lock = threading.Lock()
        self.progress_counter = 0
        
        # Selenium driver (lazy loading)
        self._driver = None
        
        # Proxy desteği
        self.proxies = [
            # Ücretsiz proxy'ler (örnek)
            # 'http://proxy1:port',
            # 'http://proxy2:port',
        ]
        self.current_proxy_index = 0
    
    def _get_next_proxy(self):
        """Sonraki proxy'yi al"""
        if not self.proxies:
            return None
        
        proxy = self.proxies[self.current_proxy_index]
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxies)
        return proxy
    
    def _update_proxy(self):
        """Proxy'yi güncelle"""
        proxy = self._get_next_proxy()
        if proxy:
            self.session.proxies = {
                'http': proxy,
                'https': proxy
            }
            print(f"{Fore.CYAN}[PROXY]{Style.RESET_ALL} Proxy güncellendi: {proxy}")
        else:
            self.session.proxies = {}
        
    def is_valid_url(self, url):
        """URL'nin geçerli olup olmadığını kontrol et"""
        try:
            # URL'yi temizle
            url = self._clean_url(url)
            parsed = urlparse(url)
            return bool(parsed.netloc) and parsed.scheme in ['http', 'https']
        except:
            return False
    
    def _clean_url(self, url):
        """URL'yi temizle ve düzelt"""
        if not url:
            return url
            
        # Çift https:// sorununu düzelt
        if url.startswith('https://https://'):
            url = url.replace('https://https://', 'https://')
        elif url.startswith('http://http://'):
            url = url.replace('http://http://', 'http://')
        
        # Eksik protokol ekle
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        return url
    
    def is_same_domain(self, url):
        """URL'nin aynı domain'de olup olmadığını kontrol et"""
        try:
            parsed = urlparse(url)
            return parsed.netloc == self.domain or parsed.netloc.endswith('.' + self.domain)
        except:
            return False
    
    def is_content_page(self, url):
        """URL'nin içerik sayfası olup olmadığını kontrol et"""
        try:
            parsed = urlparse(url)
            path = parsed.path.lower()
            url_lower = url.lower()
            
            # Teknik dosya uzantıları
            technical_extensions = [
                '.css', '.js', '.json', '.xml', '.txt', '.pdf', '.doc', '.docx',
                '.xls', '.xlsx', '.ppt', '.pptx', '.zip', '.rar', '.tar', '.gz',
                '.jpg', '.jpeg', '.png', '.gif', '.svg', '.ico', '.webp', '.bmp',
                '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mp3', '.wav',
                '.ogg', '.aac', '.flac', '.m4a', '.wma', '.woff', '.woff2', '.ttf'
            ]
            
            for ext in technical_extensions:
                if path.endswith(ext):
                    return False
            
            # Admin ve yönetim paneli
            admin_patterns = [
                '/admin/', '/wp-admin/', '/administrator/', '/login/', '/logout/',
                '/register/', '/signup/', '/signin/', '/signout/', '/dashboard/',
                '/panel/', '/control/', '/manage/', '/settings/', '/config/',
                '/user/', '/users/', '/profile/', '/account/', '/my-account/'
            ]
            
            for pattern in admin_patterns:
                if pattern in path:
                    return False
            
            # API ve teknik endpoint'ler
            api_patterns = [
                '/api/', '/ajax/', '/rest/', '/graphql/', '/feed/', '/rss/',
                '/sitemap', '/robots.txt', '/manifest.json', '/sw.js',
                '/service-worker.js', '/.well-known/', '/oauth/', '/auth/',
                '/token/', '/jwt/', '/webhook/', '/callback/', '/redirect/'
            ]
            
            for pattern in api_patterns:
                if pattern in path:
                    return False
            
            # Tag, kategori ve filtreleme sayfaları (blog pagination hariç)
            filter_patterns = [
                '/tag/', '/tags/', '/category/', '/categories/', '/cat/',
                '/filter/', '/filters/', '/search/', '/query/', '/q=',
                '/sort/', '/order/', '/paged/', '/p=',
                '/archive/', '/archives/', '/date/', '/year/', '/month/',
                '/author/', '/authors/', '/user/', '/users/'
            ]
            
            for pattern in filter_patterns:
                if pattern in path:
                    return False
            
            # Blog pagination sayfalarını içerik sayfası olarak kabul et
            if '/page/' in path and ('/blog' in path or '/blogs' in path):
                return True
            
            # Ana sayfa
            if path == '/' or path == '' or url_lower == f"https://{self.domain}" or url_lower == f"https://{self.domain}/":
                return True
            
            # İçerik sayfaları
            content_patterns = [
                '/about', '/contact', '/services', '/products', '/blog', '/news',
                '/help', '/faq', '/privacy', '/terms', '/support', '/company',
                '/team', '/careers', '/jobs', '/portfolio', '/gallery', '/testimonials',
                '/reviews', '/pricing', '/plans', '/features', '/benefits',
                '/solutions', '/solutions/', '/case-studies', '/whitepapers',
                '/resources', '/downloads', '/guides', '/tutorials', '/how-to'
            ]
            
            for pattern in content_patterns:
                if pattern in path:
                    return True
            
            # Blog ve makale sayfaları
            blog_patterns = [
                '/post/', '/posts/', '/article/', '/articles/', '/story/',
                '/stories/', '/entry/', '/entries/', '/content/', '/page/',
                '/blog/', '/blogs/', '/blog-post/', '/blog-posts/'
            ]
            
            for pattern in blog_patterns:
                if pattern in path:
                    return True
            
            # Basit sayfa yapısı
            path_parts = [p for p in path.split('/') if p]
            if len(path_parts) <= 3 and '?' not in url and not any(char in path for char in ['#', '&', '=']):
                return True
            
            return False
            
        except:
            return False
    
    def _get_selenium_driver(self):
        """Selenium driver'ı başlat (anti-detection)"""
        if not SELENIUM_AVAILABLE:
            return None
            
        if self._driver is None:
            try:
                chrome_options = Options()
                
                # Anti-detection ayarları
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
                
                # Gerçekçi User-Agent
                chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
                
                # Automation detection'ı gizle
                chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
                chrome_options.add_experimental_option('useAutomationExtension', False)
                chrome_options.add_argument('--disable-automation')
                chrome_options.add_argument('--disable-infobars')
                
                # Headless mode'u kapat (daha az şüpheli)
                # chrome_options.add_argument('--headless')
                
                self._driver = webdriver.Chrome(options=chrome_options)
                
                # WebDriver property'sini gizle
                self._driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                self._driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
                self._driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']})")
                
                # Timeout ayarları
                self._driver.set_page_load_timeout(30)
                self._driver.implicitly_wait(10)
                
            except Exception as e:
                print(f"{Fore.YELLOW}[SELENIUM WARNING]{Style.RESET_ALL} Chrome driver başlatılamadı: {e}")
                return None
        
        return self._driver
    
    def _extract_links_selenium(self, url):
        """Selenium ile link çıkar (recaptcha bypass)"""
        driver = self._get_selenium_driver()
        if not driver:
            return set()
        
        try:
            print(f"{Fore.CYAN}[SELENIUM]{Style.RESET_ALL} Selenium ile scraping: {url}")
            
            # Random bekleme (human-like behavior)
            import random
            time.sleep(random.uniform(2, 4))
            
            # Sayfayı yükle
            driver.get(url)
            
            # Recaptcha kontrolü ve çözme
            if self._handle_recaptcha(driver):
                print(f"{Fore.GREEN}[RECAPTCHA SOLVED]{Style.RESET_ALL} Recaptcha çözüldü")
            else:
                print(f"{Fore.YELLOW}[RECAPTCHA SKIP]{Style.RESET_ALL} Recaptcha bulunamadı veya çözülemedi")
            
            # Human-like behavior
            self._simulate_human_behavior(driver)
            
            # Sayfanın yüklenmesini bekle
            try:
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
            except TimeoutException:
                print(f"{Fore.YELLOW}[SELENIUM WARNING]{Style.RESET_ALL} Sayfa yüklenme timeout, devam ediliyor...")
            
            # JavaScript ile linkleri bul
            links = driver.execute_script("""
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
            
            # Linkleri temizle
            clean_links = set()
            for link in links:
                if link and self.is_valid_url(link):
                    clean_link = link.split('#')[0]  # Fragment'ları kaldır
                    clean_links.add(clean_link)
            
            print(f"{Fore.GREEN}[SELENIUM SUCCESS]{Style.RESET_ALL} {len(clean_links)} link bulundu")
            return clean_links
            
        except TimeoutException:
            print(f"{Fore.RED}[SELENIUM ERROR]{Style.RESET_ALL} Sayfa yüklenme timeout: {url}")
            return set()
        except WebDriverException as e:
            print(f"{Fore.RED}[SELENIUM ERROR]{Style.RESET_ALL} WebDriver hatası: {e}")
            return set()
        except Exception as e:
            print(f"{Fore.RED}[SELENIUM ERROR]{Style.RESET_ALL} Genel hata: {e}")
            return set()
    
    def _handle_recaptcha(self, driver):
        """Recaptcha'yı çözmeye çalış"""
        try:
            # Recaptcha iframe'lerini bul
            recaptcha_iframes = driver.find_elements(By.CSS_SELECTOR, "iframe[src*='recaptcha']")
            
            if not recaptcha_iframes:
                print(f"{Fore.CYAN}[RECAPTCHA DEBUG]{Style.RESET_ALL} Recaptcha iframe bulunamadı")
                return False
            
            print(f"{Fore.CYAN}[RECAPTCHA DEBUG]{Style.RESET_ALL} {len(recaptcha_iframes)} recaptcha iframe bulundu")
            
            # İlk iframe'e geç
            driver.switch_to.frame(recaptcha_iframes[0])
            
            # Checkbox'ı bul ve tıkla
            try:
                checkbox = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, ".recaptcha-checkbox-border"))
                )
                
                # Human-like tıklama
                driver.execute_script("arguments[0].click();", checkbox)
                print(f"{Fore.GREEN}[RECAPTCHA CLICK]{Style.RESET_ALL} Checkbox tıklandı")
                
                # Ana frame'e geri dön
                driver.switch_to.default_content()
                
                # Recaptcha çözülmesini bekle (2-5 saniye)
                time.sleep(random.uniform(2, 5))
                
                return True
                
            except TimeoutException:
                print(f"{Fore.YELLOW}[RECAPTCHA WARNING]{Style.RESET_ALL} Checkbox bulunamadı")
                driver.switch_to.default_content()
                return False
                
        except Exception as e:
            print(f"{Fore.RED}[RECAPTCHA ERROR]{Style.RESET_ALL} Recaptcha çözme hatası: {e}")
            try:
                driver.switch_to.default_content()
            except:
                pass
            return False
    
    def _simulate_human_behavior(self, driver):
        """İnsan benzeri davranış simüle et"""
        import random
        
        try:
            # Random scroll
            scroll_positions = [0.25, 0.5, 0.75, 1.0]
            for pos in scroll_positions:
                driver.execute_script(f"window.scrollTo(0, document.body.scrollHeight * {pos});")
                time.sleep(random.uniform(0.5, 1.5))
            
            # Random mouse movement
            driver.execute_script("""
                var event = new MouseEvent('mousemove', {
                    'view': window,
                    'bubbles': true,
                    'cancelable': true,
                    'clientX': Math.random() * window.innerWidth,
                    'clientY': Math.random() * window.innerHeight
                });
                document.dispatchEvent(event);
            """)
            
            # Random bekleme
            time.sleep(random.uniform(1, 3))
            
        except Exception as e:
            print(f"{Fore.YELLOW}[HUMAN SIMULATION WARNING]{Style.RESET_ALL} {e}")
    
    def _test_and_extract_page_selenium(self, url):
        """Selenium ile sayfa test et ve blog linklerini çıkar"""
        try:
            driver = self._get_selenium_driver()
            if not driver:
                return {
                    'working': False,
                    'blog_links': [],
                    'total_links': 0
                }
            
            print(f"{Fore.CYAN}[SELENIUM TEST]{Style.RESET_ALL} Sayfa test ediliyor: {url}")
            
            # Random bekleme
            import random
            time.sleep(random.uniform(2, 4))
            
            # Sayfayı yükle
            driver.get(url)
            
            # Recaptcha kontrolü ve çözme
            if self._handle_recaptcha(driver):
                print(f"{Fore.GREEN}[RECAPTCHA SOLVED]{Style.RESET_ALL} Recaptcha çözüldü")
            else:
                print(f"{Fore.YELLOW}[RECAPTCHA SKIP]{Style.RESET_ALL} Recaptcha bulunamadı veya çözülemedi")
            
            # Human-like behavior
            self._simulate_human_behavior(driver)
            
            # Sayfanın yüklenmesini bekle
            try:
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
            except TimeoutException:
                print(f"{Fore.YELLOW}[SELENIUM WARNING]{Style.RESET_ALL} Sayfa yüklenme timeout")
                return {
                    'working': False,
                    'blog_links': [],
                    'total_links': 0
                }
            
            # JavaScript ile linkleri bul
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
            
            # Blog linklerini filtrele
            blog_links = set()
            for link in all_links:
                if self.is_valid_url(link) and self._is_blog_post_link(link):
                    clean_link = link.split('#')[0]
                    blog_links.add(clean_link)
            
            print(f"{Fore.GREEN}[SELENIUM SUCCESS]{Style.RESET_ALL} {len(blog_links)} blog yazısı bulundu")
            
            return {
                'working': True,
                'blog_links': list(blog_links),
                'total_links': len(all_links)
            }
            
        except Exception as e:
            print(f"{Fore.RED}[SELENIUM ERROR]{Style.RESET_ALL} Sayfa test hatası: {e}")
            return {
                'working': False,
                'blog_links': [],
                'total_links': 0
            }
    
    def _smart_pagination_scrape(self, url, max_pages=20):
        """Akıllı pagination scraping - Next butonuna tıklayarak"""
        try:
            driver = self._get_selenium_driver()
            if not driver:
                return {
                    'success': False,
                    'blog_links': [],
                    'pages_scraped': 0,
                    'error': 'Selenium driver başlatılamadı'
                }
            
            print(f"{Fore.CYAN}[SMART PAGINATION]{Style.RESET_ALL} Akıllı pagination scraping başlatılıyor: {url}")
            
            all_blog_links = set()
            pages_scraped = 0
            current_url = url
            
            # İlk sayfayı yükle
            driver.get(current_url)
            time.sleep(3)
            
            # Recaptcha kontrolü
            if self._handle_recaptcha(driver):
                print(f"{Fore.GREEN}[RECAPTCHA SOLVED]{Style.RESET_ALL} Recaptcha çözüldü")
            
            while pages_scraped < max_pages:
                print(f"{Fore.YELLOW}[PAGE {pages_scraped + 1}]{Style.RESET_ALL} Sayfa işleniyor: {current_url}")
                
                # Full scroll yap
                self._full_scroll_page(driver)
                
                # Bu sayfadaki tüm linkleri al
                page_links = self._extract_all_links_from_page(driver)
                
                # Blog linklerini filtrele
                blog_links = set()
                for link in page_links:
                    if self.is_valid_url(link) and self._is_blog_post_link(link):
                        clean_link = link.split('#')[0]
                        blog_links.add(clean_link)
                
                all_blog_links.update(blog_links)
                pages_scraped += 1
                
                print(f"{Fore.GREEN}[PAGE SUCCESS]{Style.RESET_ALL} Sayfa {pages_scraped}: {len(blog_links)} blog yazısı bulundu")
                
                # Next butonunu bul ve tıkla
                next_button = self._find_next_button(driver)
                if next_button:
                    try:
                        # Next butonuna tıkla
                        driver.execute_script("arguments[0].click();", next_button)
                        print(f"{Fore.CYAN}[NEXT CLICK]{Style.RESET_ALL} Next butonuna tıklandı")
                        
                        # Sayfa yüklenmesini bekle
                        time.sleep(3)
                        
                        # URL'nin değişip değişmediğini kontrol et
                        new_url = driver.current_url
                        if new_url == current_url:
                            print(f"{Fore.YELLOW}[PAGINATION END]{Style.RESET_ALL} URL değişmedi, pagination bitti")
                            break
                        
                        current_url = new_url
                        
                        # Human-like behavior
                        self._simulate_human_behavior(driver)
                        
                    except Exception as e:
                        print(f"{Fore.RED}[NEXT ERROR]{Style.RESET_ALL} Next buton tıklama hatası: {e}")
                        break
                else:
                    print(f"{Fore.YELLOW}[PAGINATION END]{Style.RESET_ALL} Next butonu bulunamadı, pagination bitti")
                    break
            
            print(f"{Fore.GREEN}[SMART PAGINATION COMPLETE]{Style.RESET_ALL} {pages_scraped} sayfa tarandı, {len(all_blog_links)} blog yazısı bulundu")
            
            return {
                'success': True,
                'blog_links': list(all_blog_links),
                'pages_scraped': pages_scraped,
                'total_blog_posts': len(all_blog_links)
            }
            
        except Exception as e:
            print(f"{Fore.RED}[SMART PAGINATION ERROR]{Style.RESET_ALL} Hata: {e}")
            return {
                'success': False,
                'blog_links': [],
                'pages_scraped': 0,
                'error': str(e)
            }
    
    def _full_scroll_page(self, driver):
        """Sayfayı tamamen scroll et"""
        try:
            # Sayfanın sonuna kadar scroll et
            last_height = driver.execute_script("return document.body.scrollHeight")
            
            while True:
                # En alta scroll et
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                
                # Bekle
                time.sleep(2)
                
                # Yeni yükseklik hesapla
                new_height = driver.execute_script("return document.body.scrollHeight")
                
                if new_height == last_height:
                    break
                
                last_height = new_height
            
            # En üste geri dön
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
    
    def _find_next_button(self, driver):
        """Next butonunu bul (gelişmiş)"""
        try:
            # Önce pagination container'ını bul
            pagination_containers = driver.find_elements(By.CSS_SELECTOR, ".pagination, .pager, .page-navigation, .pagination-wrapper")
            
            if pagination_containers:
                print(f"{Fore.CYAN}[PAGINATION CONTAINER]{Style.RESET_ALL} {len(pagination_containers)} pagination container bulundu")
                
                for container in pagination_containers:
                    # Container içindeki tüm linkleri bul
                    links = container.find_elements(By.TAG_NAME, "a")
                    
                    for link in links:
                        # Disabled değil mi kontrol et
                        class_attr = link.get_attribute("class") or ""
                        if "disabled" in class_attr.lower():
                            continue
                        
                        # Text içeriğini kontrol et
                        text = link.text.strip().lower()
                        href = link.get_attribute("href") or ""
                        
                        # Next buton kriterleri
                        is_next = (
                            text in ['next', '»', '>', 'sonraki', 'ileri'] or
                            'rel="next"' in link.get_attribute("outerHTML") or
                            'aria-label="Next"' in link.get_attribute("outerHTML") or
                            (text.isdigit() and int(text) > 1)  # Sayısal next (2, 3, 4...)
                        )
                        
                        if is_next:
                            print(f"{Fore.GREEN}[NEXT FOUND]{Style.RESET_ALL} Next butonu bulundu: '{text}' - {href}")
                            return link
            
            # Pagination container bulunamazsa genel arama yap
            print(f"{Fore.YELLOW}[PAGINATION FALLBACK]{Style.RESET_ALL} Pagination container bulunamadı, genel arama yapılıyor...")
            
            # Farklı Next buton selector'larını dene
            next_selectors = [
                "a[rel='next']",
                "a[aria-label='Next']",
                "a[aria-label='next']",
                "a:contains('Next')",
                "a:contains('»')",
                "a:contains('>')",
                "a:contains('sonraki')",
                "a:contains('ileri')"
            ]
            
            for selector in next_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        # Disabled değil mi kontrol et
                        class_attr = element.get_attribute("class") or ""
                        if "disabled" in class_attr.lower():
                            continue
                        
                        text = element.text.strip().lower()
                        if text in ['next', '»', '>', 'sonraki', 'ileri']:
                            print(f"{Fore.GREEN}[NEXT FOUND]{Style.RESET_ALL} Next butonu bulundu (fallback): {selector}")
                            return element
                except:
                    continue
            
            print(f"{Fore.YELLOW}[NEXT NOT FOUND]{Style.RESET_ALL} Next butonu bulunamadı")
            return None
            
        except Exception as e:
            print(f"{Fore.RED}[NEXT ERROR]{Style.RESET_ALL} Next buton arama hatası: {e}")
            return None
    
    async def _next_button_scrape(self, url, max_pages=20):
        """Next butonuna tıklayarak pagination scraping"""
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
            current_url = url
            
            # İlk sayfayı yükle
            driver.get(current_url)
            time.sleep(3)
            
            # Recaptcha kontrolü
            if self._handle_recaptcha(driver):
                print(f"{Fore.GREEN}[RECAPTCHA SOLVED]{Style.RESET_ALL} Recaptcha çözüldü")
            
            while pages_scraped < max_pages:
                print(f"{Fore.YELLOW}[PAGE {pages_scraped + 1}]{Style.RESET_ALL} Sayfa işleniyor: {current_url}")
                
                # Full scroll yap
                self._full_scroll_page(driver)
                
                # Bu sayfadaki tüm linkleri al
                page_links = self._extract_all_links_from_page(driver)
                
                # Blog linklerini filtrele ve articles tablosuna kaydet
                blog_links = set()
                for link in page_links:
                    if self.is_valid_url(link) and self._is_blog_post_link(link):
                        clean_link = link.split('#')[0]
                        blog_links.add(clean_link)
                        
                        # Article'ı database'e kaydet (title olmadan)
                        try:
                            from urllib.parse import urlparse
                            domain = urlparse(clean_link).netloc
                            
                            # Basit title çıkarma (URL'den)
                            title = clean_link.split('/')[-1].replace('-', ' ').replace('_', ' ').title()
                            
                            # Article'ı kaydet
                            article_id = self.supabase.save_article(
                                title=title,
                                url=clean_link,
                                domain=domain
                            )
                            
                            if article_id:
                                articles_saved += 1
                                # Hemen keyword üret
                                try:
                                    keyword_generator = AsyncKeywordGenerator()
                                    keywords = await keyword_generator.generate_keywords_async(clean_link, title)
                                    
                                    if keywords and len(keywords) > 0:
                                        # İlk keyword'ü articles tablosuna kaydet
                                        first_keyword = keywords[0].get('keyword', '')
                                        self.supabase.update_article_keyword(article_id, first_keyword)
                                        print(f"{Fore.GREEN}[ARTICLE KEYWORD]{Style.RESET_ALL} {title}: {first_keyword}")
                                    
                                except Exception as e:
                                    print(f"{Fore.YELLOW}[KEYWORD WARNING]{Style.RESET_ALL} Keyword üretilemedi {title}: {e}")
                                    
                        except Exception as e:
                            print(f"{Fore.YELLOW}[ARTICLE WARNING]{Style.RESET_ALL} Article kaydedilemedi {clean_link}: {e}")
                
                all_blog_links.update(blog_links)
                pages_scraped += 1
                
                print(f"{Fore.GREEN}[PAGE SUCCESS]{Style.RESET_ALL} Sayfa {pages_scraped}: {len(blog_links)} blog yazısı bulundu")
                
                # Pagination container'ını bul
                pagination_container = self._find_pagination_container(driver)
                if not pagination_container:
                    print(f"{Fore.YELLOW}[PAGINATION END]{Style.RESET_ALL} Pagination container bulunamadı")
                    break
                
                # Next butonunu bul
                next_button = self._find_next_button_in_container(pagination_container)
                if not next_button:
                    print(f"{Fore.YELLOW}[PAGINATION END]{Style.RESET_ALL} Next butonu bulunamadı")
                    break
                
                # Next butonuna tıkla
                try:
                    # Butonun görünür olduğundan emin ol
                    driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                    time.sleep(1)
                    
                    # Butonun tıklanabilir olduğundan emin ol
                    if next_button.is_enabled() and next_button.is_displayed():
                        driver.execute_script("arguments[0].click();", next_button)
                        print(f"{Fore.CYAN}[NEXT CLICK]{Style.RESET_ALL} Next butonuna tıklandı")
                        
                        # Sayfa yüklenmesini bekle
                        time.sleep(3)
                        
                        # URL'nin değişip değişmediğini kontrol et
                        new_url = driver.current_url
                        if new_url == current_url:
                            print(f"{Fore.YELLOW}[PAGINATION END]{Style.RESET_ALL} URL değişmedi, pagination bitti")
                            break
                        
                        current_url = new_url
                        
                        # Human-like behavior
                        self._simulate_human_behavior(driver)
                        
                    else:
                        print(f"{Fore.YELLOW}[PAGINATION END]{Style.RESET_ALL} Next butonu tıklanamıyor (disabled veya görünmez)")
                        break
                        
                except Exception as e:
                    print(f"{Fore.RED}[NEXT ERROR]{Style.RESET_ALL} Next buton tıklama hatası: {e}")
                    break
            
            print(f"{Fore.GREEN}[NEXT BUTTON COMPLETE]{Style.RESET_ALL} {pages_scraped} sayfa tarandı, {len(all_blog_links)} blog yazısı bulundu, {articles_saved} article kaydedildi")
            
            return {
                'success': True,
                'blog_links': list(all_blog_links),
                'pages_scraped': pages_scraped,
                'total_blog_posts': len(all_blog_links),
                'articles_saved': articles_saved
            }
            
        except Exception as e:
            print(f"{Fore.RED}[NEXT BUTTON ERROR]{Style.RESET_ALL} Hata: {e}")
            return {
                'success': False,
                'blog_links': [],
                'pages_scraped': 0,
                'error': str(e)
            }
    
    def _find_pagination_container(self, driver):
        """Pagination container'ını bul (sayfanın her yerinde)"""
        try:
            # Farklı pagination container selector'larını dene
            container_selectors = [
                ".pagination",
                ".pager", 
                ".page-navigation",
                ".pagination-wrapper",
                ".pagination-container",
                ".pagination-nav",
                ".pagination-list",
                "ul.pagination",
                "nav.pagination",
                ".pagination ul",
                ".pagination-container",
                ".pagination-wrapper",
                ".page-numbers",
                ".wp-pagenavi",
                ".pagination-box",
                ".pagination-bar",
                ".pagination-menu",
                ".pagination-controls",
                ".pagination-buttons",
                ".pagination-links"
            ]
            
            print(f"{Fore.CYAN}[PAGINATION SEARCH]{Style.RESET_ALL} Pagination container aranıyor...")
            
            for selector in container_selectors:
                try:
                    containers = driver.find_elements(By.CSS_SELECTOR, selector)
                    print(f"{Fore.CYAN}[PAGINATION DEBUG]{Style.RESET_ALL} {selector} selector ile {len(containers)} container bulundu")
                    
                    for i, container in enumerate(containers):
                        # Container içinde sayfa linkleri var mı kontrol et
                        page_links = container.find_elements(By.TAG_NAME, "a")
                        print(f"{Fore.CYAN}[PAGINATION DEBUG]{Style.RESET_ALL} Container {i+1}: {len(page_links)} link bulundu")
                        
                        if len(page_links) > 0:
                            # Linklerin pagination linki olup olmadığını kontrol et
                            pagination_links = 0
                            for link in page_links:
                                href = link.get_attribute("href") or ""
                                text = link.text.strip()
                                
                                # Pagination link kriterleri
                                is_pagination = (
                                    "page" in href.lower() or
                                    "p=" in href.lower() or
                                    text.isdigit() or
                                    text in ['next', 'prev', '»', '«', '>', '<', 'sonraki', 'önceki']
                                )
                                
                                if is_pagination:
                                    pagination_links += 1
                            
                            if pagination_links > 0:
                                print(f"{Fore.GREEN}[PAGINATION CONTAINER FOUND]{Style.RESET_ALL} Container bulundu: {selector} (Container {i+1}) - {pagination_links} pagination link")
                                return container
                            
                except Exception as e:
                    print(f"{Fore.YELLOW}[PAGINATION DEBUG]{Style.RESET_ALL} {selector} selector hatası: {e}")
                    continue
            
            # Eğer hiçbir selector bulamazsa, tüm linkleri kontrol et
            print(f"{Fore.YELLOW}[PAGINATION FALLBACK]{Style.RESET_ALL} Standart selector'lar bulunamadı, tüm linkler kontrol ediliyor...")
            
            all_links = driver.find_elements(By.TAG_NAME, "a")
            pagination_links = []
            
            for link in all_links:
                href = link.get_attribute("href") or ""
                text = link.text.strip()
                
                # Pagination link kriterleri
                is_pagination = (
                    "page" in href.lower() or
                    "p=" in href.lower() or
                    text.isdigit() or
                    text in ['next', 'prev', '»', '«', '>', '<', 'sonraki', 'önceki']
                )
                
                if is_pagination:
                    pagination_links.append(link)
            
            if len(pagination_links) > 0:
                print(f"{Fore.GREEN}[PAGINATION FALLBACK FOUND]{Style.RESET_ALL} {len(pagination_links)} pagination link bulundu")
                # İlk pagination link'in parent container'ını döndür
                parent = pagination_links[0].find_element(By.XPATH, "./..")
                return parent
            
            print(f"{Fore.YELLOW}[PAGINATION CONTAINER NOT FOUND]{Style.RESET_ALL} Pagination container bulunamadı")
            return None
            
        except Exception as e:
            print(f"{Fore.RED}[PAGINATION CONTAINER ERROR]{Style.RESET_ALL} Container arama hatası: {e}")
            return None
    
    def _find_next_button_in_container(self, container):
        """Container içinde Next butonunu bul (gelişmiş)"""
        try:
            # Container içindeki tüm linkleri bul
            links = container.find_elements(By.TAG_NAME, "a")
            print(f"{Fore.CYAN}[NEXT BUTTON SEARCH]{Style.RESET_ALL} Container içinde {len(links)} link bulundu")
            
            # Önce açık Next butonlarını ara
            for i, link in enumerate(links):
                # Disabled değil mi kontrol et
                class_attr = link.get_attribute("class") or ""
                if "disabled" in class_attr.lower():
                    print(f"{Fore.YELLOW}[NEXT BUTTON DEBUG]{Style.RESET_ALL} Link {i+1}: Disabled - {link.text.strip()}")
                    continue
                
                # Text içeriğini kontrol et
                text = link.text.strip()
                href = link.get_attribute("href") or ""
                outer_html = link.get_attribute("outerHTML") or ""
                
                print(f"{Fore.CYAN}[NEXT BUTTON DEBUG]{Style.RESET_ALL} Link {i+1}: '{text}' - {href}")
                
                # Next buton kriterleri (daha geniş)
                is_next = (
                    text.lower() in ['next', '»', '>', 'sonraki', 'ileri', 'forward', 'continue'] or
                    'rel="next"' in outer_html or
                    'aria-label="Next"' in outer_html or
                    'aria-label="next"' in outer_html or
                    'aria-label="Next Page"' in outer_html or
                    'aria-label="next page"' in outer_html or
                    'title="Next"' in outer_html or
                    'title="next"' in outer_html or
                    'title="Next Page"' in outer_html or
                    'title="next page"' in outer_html
                )
                
                if is_next:
                    print(f"{Fore.GREEN}[NEXT BUTTON FOUND]{Style.RESET_ALL} Next butonu bulundu: '{text}' - {href}")
                    return link
            
            # Eğer açık Next butonu bulunamazsa, sayısal butonları kontrol et
            print(f"{Fore.YELLOW}[NEXT BUTTON FALLBACK]{Style.RESET_ALL} Açık Next butonu bulunamadı, sayısal butonlar kontrol ediliyor...")
            
            for i, link in enumerate(links):
                # Disabled değil mi kontrol et
                class_attr = link.get_attribute("class") or ""
                if "disabled" in class_attr.lower():
                    continue
                
                text = link.text.strip()
                href = link.get_attribute("href") or ""
                
                # Sayısal buton kontrolü
                if text.isdigit():
                    current_page = int(text)
                    print(f"{Fore.CYAN}[NEXT BUTTON DEBUG]{Style.RESET_ALL} Sayısal buton: {current_page}")
                    
                    # Bu buton aktif sayfa mı kontrol et
                    if "active" in class_attr.lower() or "current" in class_attr.lower():
                        print(f"{Fore.CYAN}[NEXT BUTTON DEBUG]{Style.RESET_ALL} Aktif sayfa: {current_page}")
                        continue
                    
                    # Bu buton next sayfa mı kontrol et (aktif sayfadan büyük)
                    # Aktif sayfayı bul
                    active_page = 1
                    for other_link in links:
                        other_class = other_link.get_attribute("class") or ""
                        other_text = other_link.text.strip()
                        if other_text.isdigit() and ("active" in other_class.lower() or "current" in other_class.lower()):
                            active_page = int(other_text)
                            break
                    
                    if current_page > active_page:
                        print(f"{Fore.GREEN}[NEXT BUTTON FOUND]{Style.RESET_ALL} Next sayfa butonu bulundu: {current_page} (Aktif: {active_page})")
                        return link
            
            print(f"{Fore.YELLOW}[NEXT BUTTON NOT FOUND]{Style.RESET_ALL} Container içinde Next butonu bulunamadı")
            return None
            
        except Exception as e:
            print(f"{Fore.RED}[NEXT BUTTON ERROR]{Style.RESET_ALL} Next buton arama hatası: {e}")
            return None
    
    def _is_blog_post_link(self, url: str):
        """URL'nin blog yazısı linki olup olmadığını kontrol et"""
        try:
            if not url or not isinstance(url, str):
                return False
            
            url = url.lower().strip()
            
            # Blog yazısı olmayan URL'ler
            exclude_patterns = [
                '/page/', '/paged/', '/p/',
                '/category/', '/tag/', '/tags/',
                '/author/', '/date/', '/archive/',
                '/search', '/filter', '/sort',
                '/feed', '/rss', '/sitemap',
                '/admin', '/wp-admin', '/login',
                '/register', '/signup', '/signin',
                '/contact', '/about', '/privacy',
                '/terms', '/policy', '/legal',
                '/help', '/support', '/faq',
                '/shop', '/store', '/cart',
                '/checkout', '/payment', '/billing',
                '/account', '/profile', '/dashboard',
                '/api/', '/ajax/', '/json/',
                '.pdf', '.doc', '.docx', '.xls', '.xlsx',
                '.ppt', '.pptx', '.zip', '.rar',
                '.jpg', '.jpeg', '.png', '.gif', '.svg',
                '.css', '.js', '.xml', '.txt',
                'javascript:', 'mailto:', 'tel:',
                '#', '?utm_', '?ref=', '?source=',
                '/wp-content/', '/wp-includes/',
                '/static/', '/assets/', '/media/',
                '/uploads/', '/files/', '/downloads/'
            ]
            
            # Exclude pattern'leri kontrol et
            for pattern in exclude_patterns:
                if pattern in url:
                    return False
            
            # Blog yazısı olabilecek URL'ler
            include_patterns = [
                '/blog/', '/blogs/', '/post/', '/posts/',
                '/article/', '/articles/', '/news/', '/news/',
                '/story/', '/stories/', '/tutorial/', '/tutorials/',
                '/guide/', '/guides/', '/how-to/', '/tips/',
                '/review/', '/reviews/', '/opinion/', '/opinions/',
                '/update/', '/updates/', '/announcement/', '/announcements/'
            ]
            
            # Include pattern'leri kontrol et
            for pattern in include_patterns:
                if pattern in url:
                    return True
            
            # Eğer hiçbir pattern uymazsa, URL uzunluğuna bak
            # Kısa URL'ler genellikle blog yazısı değildir
            if len(url) < 30:
                return False
            
            # URL'de tarih pattern'i var mı kontrol et (blog yazıları genellikle tarih içerir)
            import re
            date_patterns = [
                r'/\d{4}/\d{2}/',  # /2023/12/
                r'/\d{4}-\d{2}/',  # /2023-12/
                r'/\d{4}/\d{2}/\d{2}/',  # /2023/12/25/
                r'/\d{4}-\d{2}-\d{2}/',  # /2023-12-25/
            ]
            
            for pattern in date_patterns:
                if re.search(pattern, url):
                    return True
            
            # Son kontrol: URL'de blog yazısı gibi görünen kelimeler var mı
            blog_keywords = [
                'blog', 'post', 'article', 'news', 'story',
                'tutorial', 'guide', 'review', 'opinion',
                'update', 'announcement', 'how-to', 'tips'
            ]
            
            for keyword in blog_keywords:
                if keyword in url:
                    return True
            
            return False
            
        except Exception as e:
            print(f"{Fore.YELLOW}[BLOG LINK WARNING]{Style.RESET_ALL} Blog link kontrol hatası: {e}")
            return False
    
    def extract_links(self, url):
        """Belirli bir URL'den tüm linkleri çıkar"""
        try:
            with self.lock:
                self.progress_counter += 1
                print(f"{Fore.YELLOW}[INFO]{Style.RESET_ALL} İşleniyor ({self.progress_counter}): {url}")
            
            # Önce normal requests ile dene
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # Farklı User-Agent'ler dene
                    if attempt == 1:
                        self.session.headers.update({
                            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                        })
                    elif attempt == 2:
                        self.session.headers.update({
                            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                        })
                    
                    response = self.session.get(url, timeout=15, allow_redirects=True)
                    
                    if response.status_code == 403:
                        print(f"{Fore.YELLOW}[WARNING]{Style.RESET_ALL} 403 Forbidden - Deneme {attempt + 1}/{max_retries}")
                        if attempt < max_retries - 1:
                            time.sleep(2)  # 2 saniye bekle
                            continue
                        else:
                            print(f"{Fore.YELLOW}[FALLBACK]{Style.RESET_ALL} Selenium ile deneniyor...")
                            # Selenium ile dene
                            selenium_links = self._extract_links_selenium(url)
                            if selenium_links:
                                return selenium_links
                            else:
                                print(f"{Fore.RED}[BLOCKED]{Style.RESET_ALL} Site bot trafiğini engelliyor")
                                return set()
                    
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.content, 'html5lib')
                    links = set()
                    
                    # Tüm <a> taglerini bul
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        absolute_url = urljoin(url, href)
                        absolute_url = absolute_url.split('#')[0]  # Fragment'ları kaldır
                        
                        if self.is_valid_url(absolute_url):
                            links.add(absolute_url)
                    
                    with self.lock:
                        print(f"{Fore.GREEN}[SUCCESS]{Style.RESET_ALL} {len(links)} link bulundu")
                    return links
                    
                except requests.exceptions.RequestException as e:
                    if attempt < max_retries - 1:
                        print(f"{Fore.YELLOW}[RETRY]{Style.RESET_ALL} Deneme {attempt + 1}/{max_retries} - {e}")
                        time.sleep(2)
                        continue
                    else:
                        print(f"{Fore.YELLOW}[FALLBACK]{Style.RESET_ALL} Selenium ile deneniyor...")
                        # Selenium ile dene
                        selenium_links = self._extract_links_selenium(url)
                        if selenium_links:
                            return selenium_links
                        else:
                            with self.lock:
                                print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} İstek hatası: {e}")
                            return set()
            
        except Exception as e:
            with self.lock:
                print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} Genel hata: {e}")
            return set()
    
    def __del__(self):
        """Destructor - Selenium driver'ı kapat"""
        if hasattr(self, '_driver') and self._driver:
            try:
                self._driver.quit()
            except:
                pass
    
    def scrape_links(self):
        """Ana link scraping fonksiyonu"""
        print(f"{Fore.CYAN}[START]{Style.RESET_ALL} Link scraping başlatılıyor...")
        print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} Hedef URL: {self.base_url}")
        print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} Maksimum derinlik: {self.max_depth}")
        print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} Bekleme süresi: {self.delay} saniye")
        print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} Paralel worker: {self.max_workers}")
        print("-" * 50)
        
        # Ana sayfayı işle
        current_level = [self.base_url]
        
        for depth in range(self.max_depth + 1):
            print(f"\n{Fore.MAGENTA}[DEPTH {depth}]{Style.RESET_ALL} İşleniyor...")
            next_level = set()
            
            # Paralel işleme
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # URL'leri filtrele
                urls_to_process = [url for url in current_level if url not in self.visited_urls]
                
                if not urls_to_process:
                    print(f"{Fore.YELLOW}[INFO]{Style.RESET_ALL} Daha fazla link bulunamadı, işlem tamamlandı.")
                    break
                
                # Paralel olarak işle
                future_to_url = {executor.submit(self._process_url, url): url for url in urls_to_process}
                
                for future in as_completed(future_to_url):
                    url = future_to_url[future]
                    try:
                        links = future.result()
                        
                        # Sadece iç linkleri toplam listeye ekle
                        internal_links = set()
                        for link in links:
                            if self.is_same_domain(link):
                                internal_links.add(link)
                        
                        with self.lock:
                            self.all_links.update(internal_links)
                        
                        # İçerik sayfası olan linkleri bir sonraki seviyeye ekle
                        for link in internal_links:
                            if (self.is_content_page(link) and
                                link not in self.visited_urls):
                                next_level.add(link)
                                
                    except Exception as e:
                        with self.lock:
                            print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} URL işleme hatası {url}: {e}")
            
            current_level = list(next_level)
            
            if not current_level:
                print(f"{Fore.YELLOW}[INFO]{Style.RESET_ALL} Daha fazla link bulunamadı, işlem tamamlandı.")
                break
        
        print(f"\n{Fore.GREEN}[COMPLETED]{Style.RESET_ALL} Toplam {len(self.all_links)} benzersiz link bulundu!")
        return self.all_links
    
    def _process_url(self, url):
        """URL'yi işle"""
        with self.lock:
            if url in self.visited_urls:
                return set()
            self.visited_urls.add(url)
        
        # Rate limiting
        time.sleep(self.delay)
        
        return self.extract_links(url)
    
    def filter_links(self, link_type=None):
        """Linkleri türlerine göre filtrele"""
        if not link_type:
            return {link for link in self.all_links if self.is_same_domain(link)}
        
        filtered_links = set()
        
        for link in self.all_links:
            if link_type == 'internal' and self.is_same_domain(link):
                filtered_links.add(link)
            elif link_type == 'external' and not self.is_same_domain(link):
                filtered_links.add(link)
            elif link_type == 'images' and any(link.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']):
                filtered_links.add(link)
            elif link_type == 'pdf' and link.lower().endswith('.pdf'):
                filtered_links.add(link)
            elif link_type == 'css' and link.lower().endswith('.css'):
                filtered_links.add(link)
            elif link_type == 'js' and link.lower().endswith('.js'):
                filtered_links.add(link)
        
        return filtered_links
    
    def print_summary(self):
        """Özet bilgileri yazdır"""
        internal_links = self.filter_links('internal')
        print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}LINK SCRAPING ÖZETİ{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"Ana URL: {self.base_url}")
        print(f"Domain: {self.domain}")
        print(f"Ziyaret edilen sayfa sayısı: {len(self.visited_urls)}")
        print(f"Toplam bulunan iç link: {len(internal_links)}")
        print(f"İçerik sayfaları: {len([link for link in internal_links if self.is_content_page(link)])}")
        print(f"Teknik dosyalar: {len([link for link in internal_links if not self.is_content_page(link)])}")
        print(f"Resim linkleri: {len(self.filter_links('images'))}")
        print(f"PDF linkleri: {len(self.filter_links('pdf'))}")
        print(f"CSS linkleri: {len(self.filter_links('css'))}")
        print(f"JavaScript linkleri: {len(self.filter_links('js'))}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")

# =============================================================================
# ASYNC KEYWORD GENERATOR
# =============================================================================

class AsyncKeywordGenerator:
    def __init__(self, api_key: str = None, max_concurrent: int = 5):
        """Asenkron keyword generator'ı başlat"""
        self.api_key = api_key or "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"
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        
    async def generate_keywords_async(self, url: str, title: str = None, content: str = None) -> List[Dict[str, any]]:
        """Asenkron keyword üretimi"""
        async with self.semaphore:
            try:
                prompt = self._create_prompt(url, title, content)
                
                async with aiohttp.ClientSession() as session:
                    headers = {
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    }
                    
                    data = {
                        "model": "openai/gpt-3.5-turbo",
                        "messages": [
                            {
                                "role": "system",
                                "content": "Sen bir SEO uzmanısın. Verilen URL, başlık ve içerik için en uygun keyword'leri üretiyorsun. Sadece JSON formatında yanıt ver."
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "temperature": 0.7,
                        "max_tokens": 500
                    }
                    
                    async with session.post(self.base_url, headers=headers, json=data, timeout=30) as response:
                        response.raise_for_status()
                        result = await response.json()
                        content = result['choices'][0]['message']['content']
                        
                        keywords = self._parse_keywords(content)
                        print(f"{Fore.GREEN}[ASYNC KEYWORDS]{Style.RESET_ALL} {len(keywords)} keyword üretildi: {url[:50]}...")
                        return keywords
                        
            except Exception as e:
                print(f"{Fore.RED}[ASYNC KEYWORD ERROR]{Style.RESET_ALL} {url[:50]}... - {e}")
                return self._fallback_keywords(url, title)
    
    async def generate_keywords_batch(self, url_data_list: List[Tuple[str, str, str]]) -> List[List[Dict[str, any]]]:
        """Toplu asenkron keyword üretimi"""
        print(f"{Fore.CYAN}[BATCH KEYWORDS]{Style.RESET_ALL} {len(url_data_list)} URL için paralel keyword üretimi başlatılıyor...")
        
        tasks = []
        for url, title, content in url_data_list:
            task = self.generate_keywords_async(url, title, content)
            tasks.append(task)
        
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()
        
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"{Fore.YELLOW}[BATCH WARNING]{Style.RESET_ALL} URL {i+1} hatası: {result}")
                valid_results.append([])
            else:
                valid_results.append(result)
        
        total_keywords = sum(len(result) for result in valid_results)
        print(f"{Fore.GREEN}[BATCH COMPLETE]{Style.RESET_ALL} {len(url_data_list)} URL işlendi, {total_keywords} keyword üretildi")
        print(f"{Fore.CYAN}[PERFORMANCE]{Style.RESET_ALL} Süre: {end_time - start_time:.2f}s, Hız: {len(url_data_list)/(end_time - start_time):.2f} URL/s")
        
        return valid_results
    
    def _create_prompt(self, url: str, title: str = None, content: str = None) -> str:
        """Prompt oluştur"""
        prompt = f"""
Aşağıdaki web sayfası için SEO keyword'leri üret:

URL: {url}
Başlık: {title or 'Belirtilmemiş'}
İçerik: {content[:500] + '...' if content and len(content) > 500 else content or 'Belirtilmemiş'}

Lütfen aşağıdaki JSON formatında yanıt ver:
{{
    "keywords": [
        {{"keyword": "anahtar kelime 1", "relevance_score": 0.9, "category": "primary"}},
        {{"keyword": "anahtar kelime 2", "relevance_score": 0.8, "category": "secondary"}},
        {{"keyword": "anahtar kelime 3", "relevance_score": 0.7, "category": "longtail"}}
    ]
}}

Kurallar:
1. Türkçe keyword'ler kullan
2. relevance_score 0.1-1.0 arasında olsun
3. category: primary, secondary, longtail
4. En az 1, en fazla 5 keyword üret
5. Sadece JSON formatında yanıt ver
"""
        return prompt
    
    def _parse_keywords(self, content: str) -> List[Dict[str, any]]:
        """AI yanıtından keyword'leri parse et"""
        try:
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                raise ValueError("JSON bulunamadı")
            
            json_str = content[start_idx:end_idx]
            data = json.loads(json_str)
            
            keywords = []
            for kw in data.get('keywords', []):
                keywords.append({
                    'keyword': kw.get('keyword', ''),
                    'relevance_score': float(kw.get('relevance_score', 0.5)),
                    'source': 'ai_generated',
                    'category': kw.get('category', 'secondary')
                })
            
            return keywords
            
        except Exception as e:
            print(f"{Fore.YELLOW}[PARSE WARNING]{Style.RESET_ALL} JSON parse hatası: {e}")
            return self._fallback_keywords("", "")
    
    def _fallback_keywords(self, url: str, title: str = None) -> List[Dict[str, any]]:
        """Fallback keyword'ler"""
        keywords = []
        
        if url:
            url_parts = url.split('/')
            for part in url_parts:
                if part and len(part) > 2 and not part.startswith('http'):
                    keywords.append({
                        'keyword': part.replace('-', ' ').replace('_', ' '),
                        'relevance_score': 0.6,
                        'source': 'url_extracted',
                        'category': 'secondary'
                    })
        
        if title:
            title_words = title.lower().split()
            for word in title_words:
                if len(word) > 3:
                    keywords.append({
                        'keyword': word,
                        'relevance_score': 0.8,
                        'source': 'title_extracted',
                        'category': 'primary'
                    })
        
        default_keywords = [
            {'keyword': 'web sayfası', 'relevance_score': 0.5, 'source': 'default', 'category': 'secondary'},
            {'keyword': 'içerik', 'relevance_score': 0.4, 'source': 'default', 'category': 'secondary'}
        ]
        
        keywords.extend(default_keywords)
        return keywords[:10]

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
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s]', ' ', text)
        
        return text.strip()
    
    def is_stopword_or_short(self, word: str) -> bool:
        """Stopword veya kısa kelime kontrolü"""
        if not word:
            return True
        
        if len(word) < 3:
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
            
            if re.search(r'\b' + re.escape(keyword_norm) + r'\b', normalized_text, flags=re.IGNORECASE):
                pattern = r'\b' + re.escape(original_keyword) + r'\b'
                
                def replacer(match):
                    used_keywords.add(keyword_norm)
                    return f'[{match.group(0)}]({url})'
                
                original_text, n = re.subn(pattern, replacer, original_text, count=1, flags=re.IGNORECASE)
                
                if n > 0:
                    print(f"{Fore.GREEN}[LINKIFIED]{Style.RESET_ALL} '{original_keyword}' -> {url}")
        
        return original_text
    
    def linkify_file(self, input_file: str, output_file: str = None) -> str:
        """Dosyayı linkify et"""
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            linkified_content = self.linkify_text_with_db(content)
            
            if not output_file:
                output_file = input_file.replace('.md', '_linkified.md')
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(linkified_content)
            
            print(f"{Fore.GREEN}[LINKIFIER]{Style.RESET_ALL} Dosya linkify edildi: {output_file}")
            return output_file
            
        except Exception as e:
            print(f"{Fore.RED}[LINKIFIER ERROR]{Style.RESET_ALL} Dosya işleme hatası: {e}")
            return None
    
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
# ENHANCED SCRAPER
# =============================================================================

class EnhancedScraper:
    def __init__(self, base_url, max_depth=2, delay=1, max_workers=10):
        """Enhanced scraper'ı başlat"""
        self.base_url = base_url
        self.domain = self.base_url.split('/')[2]
        self.max_depth = max_depth
        self.delay = delay
        self.max_workers = max_workers
        
        self.scraper = LinkScraper(base_url, max_depth, delay, max_workers)
        self.supabase = SupabaseClient()
        self.keyword_gen = AsyncKeywordGenerator()
        
        self.session_id = None
        
    def start_scraping_session(self):
        """Scraping oturumunu başlat"""
        print(f"{Fore.CYAN}[ENHANCED SCRAPER]{Style.RESET_ALL} Oturum başlatılıyor...")
        
        self.session_id = self.supabase.create_scraping_session(
            self.base_url, 
            self.domain, 
            self.max_depth
        )
        
        if not self.session_id:
            print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} Supabase oturumu oluşturulamadı!")
            return False
        
        return True
    
    async def scrape_and_save_async(self):
        """Asenkron scraping ve kaydetme"""
        if not self.start_scraping_session():
            return False
        
        print(f"{Fore.CYAN}[ENHANCED SCRAPER]{Style.RESET_ALL} Asenkron scraping başlatılıyor...")
        
        # Sadece içerik sayfalarını çek
        page_urls = self._get_page_content_urls()
        print(f"{Fore.GREEN}[ENHANCED SCRAPER]{Style.RESET_ALL} {len(page_urls)} sayfa içeriği bulundu")
        
        # Her sayfa için içerik çıkar
        page_contents = []
        for url in page_urls:
            content = self._extract_page_content(url)
            if content:
                page_contents.append((url, content.get('title', ''), content.get('content', '')))
        
        # Toplu keyword üretimi
        if page_contents:
            keywords_results = await self.keyword_gen.generate_keywords_batch(page_contents)
            
            # Her sayfa için kaydet
            processed_count = 0
            for i, (url, title, content) in enumerate(page_contents):
                try:
                    # Link'i kaydet
                    link_id = self.supabase.save_link(
                        url=url,
                        title=title,
                        domain=self.domain,
                        content_type='page_content',
                        content_length=len(content)
                    )
                    
                    if link_id and i < len(keywords_results):
                        # Keyword'leri kaydet
                        keywords = keywords_results[i]
                        if keywords:
                            self.supabase.save_keywords(link_id, keywords)
                        
                        # Oturuma ekle
                        self.supabase.add_link_to_session(self.session_id, link_id)
                        
                        processed_count += 1
                        print(f"{Fore.GREEN}[SUCCESS]{Style.RESET_ALL} Sayfa işlendi: {url}")
                    
                except Exception as e:
                    print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} Sayfa işleme hatası: {e}")
                    continue
        
        # Oturumu tamamla
        self.supabase.update_session_status(
            self.session_id, 
            'completed', 
            len(page_urls), 
            processed_count
        )
        
        print(f"\n{Fore.GREEN}[COMPLETED]{Style.RESET_ALL} {processed_count} sayfa içeriği işlendi ve Supabase'e kaydedildi!")
        return True
    
    def _get_page_content_urls(self) -> list:
        """Sadece sayfa içeriklerini içeren URL'leri getir"""
        try:
            page_urls = [self.base_url]
            
            response = self.scraper.session.get(self.base_url, timeout=10)
            if response.status_code != 200:
                return page_urls
            
            soup = BeautifulSoup(response.content, 'html5lib')
            
            content_urls = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                full_url = urljoin(self.base_url, href)
                
                if self._is_content_page(full_url):
                    content_urls.append(full_url)
            
            page_urls.extend(list(set(content_urls)))
            return page_urls[:20]  # Maksimum 20 sayfa ile sınırla
            
        except Exception as e:
            print(f"{Fore.YELLOW}[URL WARNING]{Style.RESET_ALL} URL çekme hatası: {e}")
            return [self.base_url]
    
    def _is_content_page(self, url: str) -> bool:
        """URL'nin içerik sayfası olup olmadığını kontrol et"""
        if not url or self.domain not in url:
            return False
        
        url_lower = url.lower()
        path = url.split('/')[3:] if len(url.split('/')) > 3 else []
        
        # Teknik dosya uzantıları
        technical_extensions = [
            '.css', '.js', '.json', '.xml', '.txt', '.pdf', '.doc', '.docx',
            '.xls', '.xlsx', '.ppt', '.pptx', '.zip', '.rar', '.tar', '.gz',
            '.jpg', '.jpeg', '.png', '.gif', '.svg', '.ico', '.webp', '.bmp',
            '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mp3', '.wav',
            '.ogg', '.aac', '.flac', '.m4a', '.wma', '.woff', '.woff2', '.ttf'
        ]
        
        for ext in technical_extensions:
            if url_lower.endswith(ext):
                return False
        
        # Admin ve yönetim paneli
        admin_patterns = [
            '/admin/', '/wp-admin/', '/administrator/', '/login/', '/logout/',
            '/register/', '/signup/', '/signin/', '/signout/', '/dashboard/',
            '/panel/', '/control/', '/manage/', '/settings/', '/config/',
            '/user/', '/users/', '/profile/', '/account/', '/my-account/'
        ]
        
        for pattern in admin_patterns:
            if pattern in url_lower:
                return False
        
        # API ve teknik endpoint'ler
        api_patterns = [
            '/api/', '/ajax/', '/rest/', '/graphql/', '/feed/', '/rss/',
            '/sitemap', '/robots.txt', '/manifest.json', '/sw.js',
            '/service-worker.js', '/.well-known/', '/oauth/', '/auth/',
            '/token/', '/jwt/', '/webhook/', '/callback/', '/redirect/'
        ]
        
        for pattern in api_patterns:
            if pattern in url_lower:
                return False
        
        # Ana sayfa
        if url_lower == f"https://{self.domain}" or url_lower == f"https://{self.domain}/":
            return True
        
        # İçerik sayfaları
        content_patterns = [
            '/about', '/contact', '/services', '/products', '/blog', '/news',
            '/help', '/faq', '/privacy', '/terms', '/support', '/company',
            '/team', '/careers', '/jobs', '/portfolio', '/gallery', '/testimonials',
            '/reviews', '/pricing', '/plans', '/features', '/benefits',
            '/solutions', '/solutions/', '/case-studies', '/whitepapers',
            '/resources', '/downloads', '/guides', '/tutorials', '/how-to'
        ]
        
        for pattern in content_patterns:
            if pattern in url_lower:
                return True
        
        # Blog ve makale sayfaları
        blog_patterns = [
            '/post/', '/posts/', '/article/', '/articles/', '/story/',
            '/stories/', '/entry/', '/entries/', '/content/', '/page/'
        ]
        
        for pattern in blog_patterns:
            if pattern in url_lower:
                return True
        
        # Basit sayfa yapısı
        if len(path) <= 3 and '?' not in url and not any(char in url_lower for char in ['#', '&', '=']):
            return True
        
        return False
    
    def _extract_page_content(self, url: str) -> dict:
        """Sayfa içeriğini çıkar"""
        try:
            response = self.scraper.session.get(url, timeout=10)
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.content, 'html5lib')
            
            # Başlık çıkar
            # Title çıkarma kaldırıldı (performans için)
            
            # Ana içerik alanlarını bul
            content = ""
            content_selectors = [
                'article', '.content', '.post-content', '.entry-content', 
                'main', '.main-content', '.page-content', '.article-content'
            ]
            
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    content = content_elem.get_text().strip()
                    break
            
            # Eğer içerik bulunamazsa, body'den al
            if not content:
                body = soup.find('body')
                if body:
                    content = body.get_text().strip()
            
            # İçerik çok kısa ise atla
            if len(content) < 100:
                return None
            
            return {
                'title': title,
                'content': content,
                'url': url
            }
            
        except Exception as e:
            print(f"{Fore.YELLOW}[CONTENT WARNING]{Style.RESET_ALL} İçerik çıkarma hatası: {e}")
            return None

# =============================================================================
# MAIN SYSTEM
# =============================================================================

class UnifiedLinkSystem:
    def __init__(self):
        """Unified link system'i başlat"""
        self.scraper = None
        self.enhanced_scraper = None
        self.linkifier = TextLinkifier()
        self.supabase = SupabaseClient()
    
    def _clean_url(self, url):
        """URL'yi temizle ve düzelt"""
        if not url:
            return url
            
        # Çift https:// sorununu düzelt
        if url.startswith('https://https://'):
            url = url.replace('https://https://', 'https://')
        elif url.startswith('http://http://'):
            url = url.replace('http://http://', 'http://')
        
        # Eksik protokol ekle
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        return url
    
    def scrape_website(self, url: str, max_depth: int = 2, delay: float = 1.0, max_workers: int = 10):
        """Web sitesini scrape et"""
        print(f"{Fore.CYAN}[UNIFIED SYSTEM]{Style.RESET_ALL} Website scraping başlatılıyor...")
        
        self.scraper = LinkScraper(url, max_depth, delay, max_workers)
        links = self.scraper.scrape_links()
        self.scraper.print_summary()
        
        return links
    
    def scrape_blog_deep(self, url: str, max_pages: int = 10, delay: float = 0.2, max_workers: int = 3):
        """Blog sayfalarını akıllıca scrape et (boş sayfa bulunca dur)"""
        print(f"{Fore.CYAN}[UNIFIED SYSTEM]{Style.RESET_ALL} Akıllı blog scraping başlatılıyor...")
        
        all_blog_links = set()
        working_pages = []
        empty_pages_count = 0
        max_empty_pages = 2  # 2 boş sayfa bulunca dur
        
        # 1. Ana sayfayı test et
        print(f"{Fore.YELLOW}[BLOG TEST]{Style.RESET_ALL} Ana sayfa test ediliyor: {url}")
        result = self._test_and_extract_page(url)
        
        if result['working']:
            working_pages.append(url)
            all_blog_links.update(result['blog_links'])
            print(f"{Fore.GREEN}[BLOG SUCCESS]{Style.RESET_ALL} {url}: {len(result['blog_links'])} blog yazısı")
        else:
            print(f"{Fore.RED}[BLOG ERROR]{Style.RESET_ALL} Ana sayfa çalışmıyor!")
            return list(all_blog_links)
        
        # 2. Pagination pattern'ini bul
        pagination_pattern = self._detect_pagination_pattern(url)
        print(f"{Fore.CYAN}[PAGINATION PATTERN]{Style.RESET_ALL} Bulunan pattern: {pagination_pattern}")
        
        # 3. Sayfa sayfa git (boş sayfa bulunca dur)
        current_page = 2
        while current_page <= max_pages and empty_pages_count < max_empty_pages:
            page_url = self._generate_page_url(url, pagination_pattern, current_page)
            print(f"{Fore.YELLOW}[BLOG TEST]{Style.RESET_ALL} Sayfa {current_page} test ediliyor: {page_url}")
            
            result = self._test_and_extract_page(page_url)
            
            if result['working'] and len(result['blog_links']) > 0:
                # Sayfa çalışıyor ve blog yazısı var
                working_pages.append(page_url)
                all_blog_links.update(result['blog_links'])
                empty_pages_count = 0  # Reset counter
                print(f"{Fore.GREEN}[BLOG SUCCESS]{Style.RESET_ALL} Sayfa {current_page}: {len(result['blog_links'])} blog yazısı")
            else:
                # Sayfa boş veya çalışmıyor
                empty_pages_count += 1
                print(f"{Fore.YELLOW}[BLOG EMPTY]{Style.RESET_ALL} Sayfa {current_page}: Boş veya engellendi ({empty_pages_count}/{max_empty_pages})")
                
                if empty_pages_count >= max_empty_pages:
                    print(f"{Fore.CYAN}[BLOG STOP]{Style.RESET_ALL} {max_empty_pages} boş sayfa bulundu, tarama durduruluyor")
                    break
            
            current_page += 1
            
            # Sayfa arası bekleme (anti-detection)
            import random
            time.sleep(random.uniform(1, 3))
        
        print(f"{Fore.CYAN}[BLOG SUMMARY]{Style.RESET_ALL} {len(working_pages)} sayfa çalışıyor, {current_page-1} sayfa kontrol edildi")
        print(f"{Fore.GREEN}[BLOG COMPLETE]{Style.RESET_ALL} Toplam {len(all_blog_links)} blog yazısı bulundu")
        return list(all_blog_links)
    
    def _test_and_extract_page(self, page_url):
        """Sayfayı test et ve blog linklerini çıkar"""
        try:
            # Önce basit test
            scraper = LinkScraper(page_url, 0, 0.1, 1)
            page_links = scraper.scrape_links()
            
            if len(page_links) > 0:
                # Blog yazı linklerini filtrele
                blog_links = []
                for link in page_links:
                    if self._is_blog_post_link(link):
                        blog_links.append(link)
                
                return {
                    'url': page_url,
                    'working': True,
                    'blog_links': blog_links,
                    'total_links': len(page_links)
                }
            else:
                return {
                    'url': page_url,
                    'working': False,
                    'blog_links': [],
                    'total_links': 0
                }
                
        except Exception as e:
            print(f"{Fore.RED}[BLOG ERROR]{Style.RESET_ALL} {page_url}: {e}")
            return {
                'url': page_url,
                'working': False,
                'blog_links': [],
                'total_links': 0
            }
    
    def _detect_pagination_pattern(self, base_url):
        """Pagination pattern'ini otomatik tespit et"""
        try:
            scraper = LinkScraper(base_url, 0, 0.1, 1)
            initial_links = scraper.scrape_links()
            
            print(f"{Fore.CYAN}[PAGINATION DEBUG]{Style.RESET_ALL} Ana sayfada {len(initial_links)} link bulundu")
            
            # Farklı pagination pattern'lerini dene (öncelik sırasına göre)
            patterns = [
                '/page/',  # /page/2/category/all
                '/p/',     # /p/2/category/all
                '/paged/', # /paged/2/category/all
                '?page=',  # ?page=2&category=all
                '?p=',     # ?p=2&category=all
                '&page=',  # &page=2&category=all
                '&p='      # &p=2&category=all
            ]
            
            for pattern in patterns:
                for link in initial_links:
                    if pattern in link.lower() and ('/blog' in link.lower() or '/blogs' in link.lower()):
                        print(f"{Fore.GREEN}[PAGINATION FOUND]{Style.RESET_ALL} Pattern bulundu: {pattern} - Örnek: {link}")
                        return pattern
            
            # Varsayılan pattern
            print(f"{Fore.YELLOW}[PAGINATION DEFAULT]{Style.RESET_ALL} Varsayılan pattern kullanılıyor: /page/")
            return '/page/'
            
        except Exception as e:
            print(f"{Fore.YELLOW}[PAGINATION WARNING]{Style.RESET_ALL} Pattern tespit edilemedi: {e}")
            return '/page/'
    
    def _generate_page_url(self, base_url, pattern, page_num):
        """Sayfa URL'si oluştur (otomatik category tespiti)"""
        if '?' in pattern or '&' in pattern:
            return f"{base_url}{pattern}{page_num}"
        else:
            # Category parametrelerini otomatik tespit et
            category_suffix = self._detect_category_suffix(base_url, pattern)
            return f"{base_url.rstrip('/')}{pattern}{page_num}{category_suffix}"
    
    def _detect_category_suffix(self, base_url, pattern):
        """Category suffix'ini otomatik tespit et"""
        try:
            scraper = LinkScraper(base_url, 0, 0.1, 1)
            initial_links = scraper.scrape_links()
            
            # Pagination linklerini bul
            pagination_links = []
            for link in initial_links:
                if pattern in link.lower() and ('/blog' in link.lower() or '/blogs' in link.lower()):
                    pagination_links.append(link)
            
            if pagination_links:
                # İlk pagination linkini analiz et
                sample_link = pagination_links[0]
                print(f"{Fore.CYAN}[CATEGORY DEBUG]{Style.RESET_ALL} Örnek pagination link: {sample_link}")
                
                # Pattern'den sonraki kısmı al
                pattern_index = sample_link.lower().find(pattern.lower())
                if pattern_index != -1:
                    after_pattern = sample_link[pattern_index + len(pattern):]
                    
                    # Sayıdan sonraki kısmı al (category parametreleri)
                    import re
                    match = re.search(r'(\d+)(.*)', after_pattern)
                    if match:
                        category_part = match.group(2)
                        if category_part:
                            print(f"{Fore.GREEN}[CATEGORY FOUND]{Style.RESET_ALL} Category suffix: {category_part}")
                            return category_part
            
            # Varsayılan (boş)
            return ""
            
        except Exception as e:
            print(f"{Fore.YELLOW}[CATEGORY WARNING]{Style.RESET_ALL} Category tespit edilemedi: {e}")
            return ""
    
    def _discover_blog_list_pages(self, url: str, max_pages: int):
        """Blog liste sayfalarını akıllıca bul (boş sayfa bulunca dur)"""
        blog_list_pages = [url]
        
        try:
            # Ana sayfayı tara (depth=0, sadece bu sayfa)
            scraper = LinkScraper(url, 0, 0.1, 1)
            initial_links = scraper.scrape_links()
            
            print(f"{Fore.CYAN}[PAGINATION DEBUG]{Style.RESET_ALL} Ana sayfada {len(initial_links)} link bulundu")
            
            # 1. Önce mevcut pagination linklerini bul
            found_pagination_links = []
            for link in initial_links:
                if self._is_pagination_link(link):
                    found_pagination_links.append(link)
            
            print(f"{Fore.CYAN}[PAGINATION DEBUG]{Style.RESET_ALL} Bulunan pagination linkler: {len(found_pagination_links)}")
            
            # 2. Eğer pagination linkleri bulunduysa, onları kullan
            if found_pagination_links:
                # Pagination linklerini sırala
                sorted_pagination = self._sort_pagination_links(found_pagination_links)
                blog_list_pages.extend(sorted_pagination[:max_pages-1])
                print(f"{Fore.GREEN}[PAGINATION SUCCESS]{Style.RESET_ALL} {len(sorted_pagination)} pagination sayfası bulundu")
            else:
                # 3. Eğer bulunamadıysa, pattern matching ile oluştur
                print(f"{Fore.YELLOW}[PAGINATION WARNING]{Style.RESET_ALL} Pagination linkleri bulunamadı, pattern matching deneniyor...")
                blog_list_pages.extend(self._generate_pagination_patterns(url, max_pages-1))
            
            print(f"{Fore.CYAN}[BLOG DEBUG]{Style.RESET_ALL} Toplam {len(blog_list_pages)} liste sayfası: {blog_list_pages[:5]}...")
            
        except Exception as e:
            print(f"{Fore.RED}[PAGINATION ERROR]{Style.RESET_ALL} Pagination bulunamadı: {e}")
            # Fallback: pattern matching
            blog_list_pages.extend(self._generate_pagination_patterns(url, max_pages-1))
        
        return blog_list_pages[:max_pages]
    
    def _is_pagination_link(self, url: str):
        """URL'nin pagination linki olup olmadığını kontrol et"""
        try:
            url_lower = url.lower()
            
            # Pagination göstergeleri
            pagination_indicators = [
                '/page/', '/p/', '/paged/', '/pagenum/', '/pagenumber/',
                '?page=', '&page=', '?p=', '&p=', '?paged=', '&paged='
            ]
            
            # Blog sayfası mı?
            is_blog_page = '/blog' in url_lower or '/blogs' in url_lower
            
            # Pagination göstergesi var mı?
            has_pagination = any(indicator in url_lower for indicator in pagination_indicators)
            
            # Teknik dosya değil
            technical_extensions = ['.css', '.js', '.json', '.xml', '.txt', '.pdf', '.jpg', '.png', '.gif', '.svg']
            is_not_technical = not any(url_lower.endswith(ext) for ext in technical_extensions)
            
            return is_blog_page and has_pagination and is_not_technical
            
        except:
            return False
    
    def _sort_pagination_links(self, pagination_links):
        """Pagination linklerini sayfa numarasına göre sırala"""
        try:
            def extract_page_number(url):
                import re
                # /page/2, /page/3, ?page=4, ?p=5 gibi pattern'leri bul
                patterns = [
                    r'/page/(\d+)',
                    r'/p/(\d+)',
                    r'[?&]page=(\d+)',
                    r'[?&]p=(\d+)',
                    r'[?&]paged=(\d+)'
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, url.lower())
                    if match:
                        return int(match.group(1))
                return 0
            
            # Sayfa numarasına göre sırala
            sorted_links = sorted(pagination_links, key=extract_page_number)
            return sorted_links
            
        except Exception as e:
            print(f"{Fore.YELLOW}[PAGINATION WARNING]{Style.RESET_ALL} Sıralama hatası: {e}")
            return pagination_links
    
    def _generate_pagination_patterns(self, base_url: str, max_pages: int):
        """Pagination pattern'leri oluştur"""
        generated_pages = []
        
        try:
            # Farklı pagination pattern'leri dene
            patterns = [
                f"{base_url.rstrip('/')}/page/",
                f"{base_url.rstrip('/')}/p/",
                f"{base_url.rstrip('/')}/paged/",
                f"{base_url}?page=",
                f"{base_url}?p=",
                f"{base_url}&page=",
                f"{base_url}&p="
            ]
            
            for pattern in patterns:
                for page_num in range(2, max_pages + 2):  # 2'den başla (1 zaten var)
                    if '?' in pattern or '&' in pattern:
                        generated_url = f"{pattern}{page_num}"
                    else:
                        generated_url = f"{pattern}{page_num}"
                    
                    generated_pages.append(generated_url)
                    
                    if len(generated_pages) >= max_pages:
                        break
                
                if generated_pages:
                    break  # İlk pattern çalıştıysa dur
            
            print(f"{Fore.CYAN}[PAGINATION GENERATED]{Style.RESET_ALL} {len(generated_pages)} pattern oluşturuldu")
            return generated_pages
            
        except Exception as e:
            print(f"{Fore.RED}[PAGINATION ERROR]{Style.RESET_ALL} Pattern oluşturma hatası: {e}")
            return []
    
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
    
    def _is_blog_post(self, url: str):
        """URL'nin blog yazısı olup olmadığını kontrol et"""
        try:
            url_lower = url.lower()
            blog_indicators = [
                '/blog/', '/blogs/', '/post/', '/posts/', '/article/', '/articles/',
                '/story/', '/stories/', '/entry/', '/entries/'
            ]
            
            # Blog yazısı göstergeleri
            has_blog_indicator = any(indicator in url_lower for indicator in blog_indicators)
            
            # Teknik dosya değil
            technical_extensions = ['.css', '.js', '.json', '.xml', '.txt', '.pdf', '.jpg', '.png', '.gif']
            is_not_technical = not any(url_lower.endswith(ext) for ext in technical_extensions)
            
            # Pagination değil
            is_not_pagination = '/page/' not in url_lower
            
            return has_blog_indicator and is_not_technical and is_not_pagination
            
        except:
            return False
    
    async def enhanced_scrape(self, url: str, max_depth: int = 2, delay: float = 1.0, max_workers: int = 10):
        """Enhanced scraping (keyword'lerle birlikte)"""
        print(f"{Fore.CYAN}[UNIFIED SYSTEM]{Style.RESET_ALL} Enhanced scraping başlatılıyor...")
        
        self.enhanced_scraper = EnhancedScraper(url, max_depth, delay, max_workers)
        success = await self.enhanced_scraper.scrape_and_save_async()
        
        return success
    
    def linkify_text(self, text: str) -> str:
        """Metni linkify et"""
        print(f"{Fore.CYAN}[UNIFIED SYSTEM]{Style.RESET_ALL} Text linkify başlatılıyor...")
        
        linkified = self.linkifier.linkify_text_with_db(text)
        
        print(f"{Fore.GREEN}[UNIFIED SYSTEM]{Style.RESET_ALL} Text linkify tamamlandı!")
        return linkified
    
    def search_keywords(self, keyword: str):
        """Keyword ile arama yap"""
        print(f"{Fore.CYAN}[UNIFIED SYSTEM]{Style.RESET_ALL} Keyword arama: '{keyword}'")
        
        results = self.supabase.search_links_by_keyword(keyword)
        
        if results:
            print(f"{Fore.GREEN}[SEARCH RESULTS]{Style.RESET_ALL} {len(results)} sonuç bulundu:")
            for result in results:
                link_data = result.get('links', {})
                print(f"  - {link_data.get('url', 'N/A')} (Score: {result.get('relevance_score', 'N/A')})")
        else:
            print(f"{Fore.YELLOW}[SEARCH]{Style.RESET_ALL} Sonuç bulunamadı")
        
        return results
    
    def get_domain_stats(self, domain: str):
        """Domain istatistiklerini getir"""
        print(f"{Fore.CYAN}[UNIFIED SYSTEM]{Style.RESET_ALL} Domain istatistikleri: {domain}")
        
        links = self.supabase.get_links_by_domain(domain)
        
        if links:
            print(f"  - Toplam link: {len(links)}")
            
            content_types = {}
            for link in links:
                content_type = link.get('content_type', 'unknown')
                content_types[content_type] = content_types.get(content_type, 0) + 1
            
            print(f"  - İçerik türü dağılımı:")
            for content_type, count in content_types.items():
                print(f"    * {content_type}: {count}")
        else:
            print(f"  - Henüz veri bulunamadı")

# =============================================================================
# API ENDPOINTS (FastAPI)
# =============================================================================

from fastapi import FastAPI, HTTPException, Depends, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict, Any
from enum import Enum

# FastAPI app
app = FastAPI(
    title="Unified Link System API",
    description="Tüm link scraping, keyword generation ve text linkify işlemleri için API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Models
class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

class ScrapingRequest(BaseModel):
    url: HttpUrl
    max_depth: int = 2
    delay: float = 1.0
    max_workers: int = 10
    save_to_db: bool = True

class ScrapingSessionResponse(BaseModel):
    id: int
    base_url: str
    domain: str
    scraping_depth: int
    status: str
    total_links_found: Optional[int] = None
    total_pages_visited: Optional[int] = None
    started_at: str
    completed_at: Optional[str] = None

class LinkResponse(BaseModel):
    id: int
    url: str
    title: Optional[str] = None
    domain: str
    content_type: str
    status_code: Optional[int] = None
    content_length: Optional[int] = None
    is_processed: bool
    created_at: str

class KeywordResponse(BaseModel):
    id: int
    keyword: str
    relevance_score: float
    source: str
    category: str
    created_at: str

class KeywordGenerationRequest(BaseModel):
    url: HttpUrl
    title: Optional[str] = None
    content: Optional[str] = None
    max_keywords: int = 10

class LinkifyRequest(BaseModel):
    text: str
    max_links: int = 10

class LinkifyResponse(BaseModel):
    original_text: str
    linkified_text: str
    links_added: int
    matched_keywords: List[str]
    total_keywords: int

class BatchLinkifyRequest(BaseModel):
    texts: List[str]
    max_links_per_text: int = 5

class BatchLinkifyResponse(BaseModel):
    results: List[LinkifyResponse]
    total_processed: int
    total_links_added: int

class SearchResponse(BaseModel):
    keyword: str
    results: List[LinkResponse]
    total_found: int

class StatsResponse(BaseModel):
    domain: str
    total_links: int
    total_keywords: int
    content_type_distribution: Dict[str, int]
    keyword_distribution: Dict[str, int]
    last_scraping: Optional[str] = None

class PaginatedResponse(BaseModel):
    items: List[LinkResponse]
    total: int
    page: int
    limit: int
    pages: int
    has_next: bool
    has_prev: bool

# Dependency injection
def get_unified_system():
    return UnifiedLinkSystem()

# Health Check
@app.get("/health", response_model=APIResponse)
async def health_check():
    """API sağlık kontrolü"""
    return APIResponse(
        success=True,
        message="Unified Link System API çalışıyor",
        data={"status": "healthy", "timestamp": datetime.now().isoformat()}
    )

# Supabase Health Check
@app.get("/health/supabase", response_model=APIResponse)
async def supabase_health_check(system: UnifiedLinkSystem = Depends(get_unified_system)):
    """Supabase bağlantı kontrolü"""
    try:
        if not system.supabase.supabase:
            return APIResponse(
                success=False,
                message="Supabase bağlantısı yok",
                data={"supabase": "disconnected"}
            )
        
        # Test query
        result = system.supabase.supabase.table('links').select('id').limit(1).execute()
        
        return APIResponse(
            success=True,
            message="Supabase bağlantısı başarılı",
            data={
                "supabase": "connected",
                "test_query": "success",
                "timestamp": datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        return APIResponse(
            success=False,
            message=f"Supabase bağlantı hatası: {str(e)}",
            data={"supabase": "error", "error": str(e)}
        )

# Scraping Endpoints
@app.post("/api/v1/scraping/start", response_model=APIResponse)
async def start_scraping(
    request: ScrapingRequest,
    background_tasks: BackgroundTasks,
    system: UnifiedLinkSystem = Depends(get_unified_system)
):
    """Scraping işlemini başlat"""
    try:
        # Enhanced scraping başlat
        print(f"[API] Enhanced scraping başlatılıyor: {request.url}")
        
        # Background task olarak çalıştır
        background_tasks.add_task(
            run_enhanced_scraping_task,
            str(request.url),
            request.max_depth,
            request.delay,
            request.max_workers
        )
        
        return APIResponse(
            success=True,
            message="Enhanced scraping başlatıldı",
            data={"url": str(request.url), "status": "started"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/scraping/simple", response_model=APIResponse)
async def simple_scraping(
    url: str,
    max_depth: int = Query(2, ge=1, le=5),
    delay: float = Query(1.0, ge=0.1, le=10.0),
    max_workers: int = Query(10, ge=1, le=50),
    save_to_db: bool = Query(False, description="Supabase'e kaydet"),
    system: UnifiedLinkSystem = Depends(get_unified_system)
):
    """Basit scraping (senkron)"""
    try:
        # URL'yi temizle
        clean_url = system._clean_url(url)
        print(f"{Fore.CYAN}[URL DEBUG]{Style.RESET_ALL} Orijinal: {url}")
        print(f"{Fore.CYAN}[URL DEBUG]{Style.RESET_ALL} Temizlenmiş: {clean_url}")
        
        links = system.scrape_website(clean_url, max_depth, delay, max_workers)
        
        # Supabase'e kaydet (eğer isteniyorsa)
        saved_count = 0
        if save_to_db and system.supabase.supabase:
            print(f"{Fore.CYAN}[SUPABASE]{Style.RESET_ALL} Linkler Supabase'e kaydediliyor...")
            domain = str(url).split('/')[2]
            
            for link in list(links)[:20]:  # İlk 20 link'i kaydet
                try:
                    link_id = system.supabase.save_link(
                        url=link,
                        domain=domain,
                        content_type='scraped',
                        content_length=0
                    )
                    if link_id:
                        saved_count += 1
                except Exception as e:
                    print(f"{Fore.YELLOW}[SUPABASE WARNING]{Style.RESET_ALL} Link kaydedilemedi {link}: {e}")
                    continue
        
        return APIResponse(
            success=True,
            message=f"{len(links)} link bulundu, {saved_count} Supabase'e kaydedildi",
            data={
                "total_links": len(links), 
                "saved_to_db": saved_count,
                "links": list(links)[:10]  # İlk 10 link
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/scraping/blog-deep", response_model=APIResponse)
async def blog_deep_scraping(
    url: str,
    max_pages: int = Query(10, ge=1, le=50, description="Maksimum sayfa sayısı"),
    delay: float = Query(0.5, ge=0.1, le=5.0, description="Sayfa arası bekleme süresi"),
    max_workers: int = Query(5, ge=1, le=10, description="Paralel worker sayısı"),
    save_to_db: bool = Query(False, description="Supabase'e kaydet"),
    system: UnifiedLinkSystem = Depends(get_unified_system)
):
    """Blog sayfalarını derinlemesine scrape et"""
    try:
        # URL'yi temizle
        clean_url = system._clean_url(url)
        print(f"{Fore.CYAN}[URL DEBUG]{Style.RESET_ALL} Orijinal: {url}")
        print(f"{Fore.CYAN}[URL DEBUG]{Style.RESET_ALL} Temizlenmiş: {clean_url}")
        
        # Blog deep scraping (hızlandırılmış)
        blog_links = system.scrape_blog_deep(clean_url, max_pages, delay, max_workers)
        
        # Supabase'e kaydet (eğer isteniyorsa)
        saved_count = 0
        if save_to_db and system.supabase.supabase:
            print(f"{Fore.CYAN}[SUPABASE]{Style.RESET_ALL} Blog linkleri Supabase'e kaydediliyor...")
            domain = clean_url.split('/')[2]
            
            for link in blog_links[:50]:  # İlk 50 blog linkini kaydet
                try:
                    link_id = system.supabase.save_link(
                        url=link,
                        domain=domain,
                        content_type='blog_post',
                        content_length=0
                    )
                    if link_id:
                        saved_count += 1
                except Exception as e:
                    print(f"{Fore.YELLOW}[SUPABASE WARNING]{Style.RESET_ALL} Blog link kaydedilemedi {link}: {e}")
                    continue
        
        return APIResponse(
            success=True,
            message=f"{len(blog_links)} blog yazısı bulundu, {saved_count} Supabase'e kaydedildi",
            data={
                "total_blog_posts": len(blog_links),
                "saved_to_db": saved_count,
                "blog_links": blog_links[:20]  # İlk 20 blog linki
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/scraping/blog-fast", response_model=APIResponse)
async def blog_fast_scraping(
    url: str,
    max_pages: int = Query(5, ge=1, le=20, description="Maksimum sayfa sayısı"),
    delay: float = Query(0.3, ge=0.1, le=2.0, description="Sayfa arası bekleme süresi"),
    max_workers: int = Query(8, ge=1, le=15, description="Paralel worker sayısı"),
    save_to_db: bool = Query(False, description="Supabase'e kaydet"),
    system: UnifiedLinkSystem = Depends(get_unified_system)
):
    """Blog sayfalarını hızlı scrape et (optimized)"""
    try:
        # URL'yi temizle
        clean_url = system._clean_url(url)
        print(f"{Fore.CYAN}[FAST BLOG]{Style.RESET_ALL} Hızlı blog scraping başlatılıyor...")
        
        # Hızlı blog scraping
        blog_links = system.scrape_blog_deep(clean_url, max_pages, delay, max_workers)
        
        # Supabase'e kaydet (eğer isteniyorsa)
        saved_count = 0
        if save_to_db and system.supabase.supabase:
            print(f"{Fore.CYAN}[SUPABASE]{Style.RESET_ALL} Blog linkleri Supabase'e kaydediliyor...")
            domain = clean_url.split('/')[2]
            
            for link in blog_links[:30]:  # İlk 30 blog linkini kaydet
                try:
                    link_id = system.supabase.save_link(
                        url=link,
                        domain=domain,
                        content_type='blog_post',
                        content_length=0
                    )
                    if link_id:
                        saved_count += 1
                except Exception as e:
                    print(f"{Fore.YELLOW}[SUPABASE WARNING]{Style.RESET_ALL} Blog link kaydedilemedi {link}: {e}")
                    continue
        
        return APIResponse(
            success=True,
            message=f"{len(blog_links)} blog yazısı bulundu, {saved_count} Supabase'e kaydedildi (HIZLI MOD)",
            data={
                "total_blog_posts": len(blog_links),
                "saved_to_db": saved_count,
                "blog_links": blog_links[:15],  # İlk 15 blog linki
                "mode": "fast"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/scraping/recaptcha-bypass", response_model=APIResponse)
async def recaptcha_bypass_scraping(
    url: str,
    max_pages: int = Query(5, ge=1, le=20, description="Maksimum sayfa sayısı"),
    delay: float = Query(2.0, ge=1.0, le=10.0, description="Sayfa arası bekleme süresi"),
    save_to_db: bool = Query(False, description="Supabase'e kaydet"),
    system: UnifiedLinkSystem = Depends(get_unified_system)
):
    """Recaptcha bypass ile blog scraping"""
    try:
        # URL'yi temizle
        clean_url = system._clean_url(url)
        print(f"{Fore.CYAN}[RECAPTCHA BYPASS]{Style.RESET_ALL} Recaptcha bypass scraping başlatılıyor...")
        
        # Selenium ile scraping (recaptcha bypass)
        all_blog_links = set()
        working_pages = []
        empty_pages_count = 0
        max_empty_pages = 2
        
        # 1. Ana sayfayı test et
        print(f"{Fore.YELLOW}[RECAPTCHA TEST]{Style.RESET_ALL} Ana sayfa test ediliyor: {clean_url}")
        result = system._test_and_extract_page_selenium(clean_url)
        
        if result['working']:
            working_pages.append(clean_url)
            all_blog_links.update(result['blog_links'])
            print(f"{Fore.GREEN}[RECAPTCHA SUCCESS]{Style.RESET_ALL} {clean_url}: {len(result['blog_links'])} blog yazısı")
        else:
            print(f"{Fore.RED}[RECAPTCHA ERROR]{Style.RESET_ALL} Ana sayfa çalışmıyor!")
            return APIResponse(
                success=False,
                message="Ana sayfa erişilemiyor",
                data={"error": "Ana sayfa testi başarısız"}
            )
        
        # 2. Pagination pattern'ini bul
        pagination_pattern = system._detect_pagination_pattern(clean_url)
        print(f"{Fore.CYAN}[RECAPTCHA PATTERN]{Style.RESET_ALL} Bulunan pattern: {pagination_pattern}")
        
        # 3. Sayfa sayfa git (Selenium ile)
        current_page = 2
        while current_page <= max_pages and empty_pages_count < max_empty_pages:
            page_url = system._generate_page_url(clean_url, pagination_pattern, current_page)
            print(f"{Fore.YELLOW}[RECAPTCHA TEST]{Style.RESET_ALL} Sayfa {current_page} test ediliyor: {page_url}")
            
            result = system._test_and_extract_page_selenium(page_url)
            
            if result['working'] and len(result['blog_links']) > 0:
                working_pages.append(page_url)
                all_blog_links.update(result['blog_links'])
                empty_pages_count = 0
                print(f"{Fore.GREEN}[RECAPTCHA SUCCESS]{Style.RESET_ALL} Sayfa {current_page}: {len(result['blog_links'])} blog yazısı")
            else:
                empty_pages_count += 1
                print(f"{Fore.YELLOW}[RECAPTCHA EMPTY]{Style.RESET_ALL} Sayfa {current_page}: Boş veya engellendi ({empty_pages_count}/{max_empty_pages})")
                
                if empty_pages_count >= max_empty_pages:
                    print(f"{Fore.CYAN}[RECAPTCHA STOP]{Style.RESET_ALL} {max_empty_pages} boş sayfa bulundu, tarama durduruluyor")
                    break
            
            current_page += 1
            time.sleep(delay)
        
        # Supabase'e kaydet
        saved_count = 0
        if save_to_db and system.supabase.supabase:
            print(f"{Fore.CYAN}[SUPABASE]{Style.RESET_ALL} Blog linkleri Supabase'e kaydediliyor...")
            domain = clean_url.split('/')[2]
            
            for link in list(all_blog_links)[:50]:
                try:
                    link_id = system.supabase.save_link(
                        url=link,
                        domain=domain,
                        content_type='blog_post_recaptcha',
                        content_length=0
                    )
                    if link_id:
                        saved_count += 1
                except Exception as e:
                    print(f"{Fore.YELLOW}[SUPABASE WARNING]{Style.RESET_ALL} Blog link kaydedilemedi {link}: {e}")
                    continue
        
        return APIResponse(
            success=True,
            message=f"{len(all_blog_links)} blog yazısı bulundu, {saved_count} Supabase'e kaydedildi (RECAPTCHA BYPASS)",
            data={
                "total_blog_posts": len(all_blog_links),
                "saved_to_db": saved_count,
                "working_pages": len(working_pages),
                "blog_links": list(all_blog_links)[:20],
                "mode": "recaptcha_bypass"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/scraping/smart-pagination", response_model=APIResponse)
async def smart_pagination_scraping(
    url: str,
    max_pages: int = Query(20, ge=1, le=50, description="Maksimum sayfa sayısı"),
    save_to_db: bool = Query(False, description="Supabase'e kaydet"),
    system: UnifiedLinkSystem = Depends(get_unified_system)
):
    """Akıllı pagination scraping - Next butonuna tıklayarak"""
    try:
        # URL'yi temizle
        clean_url = system._clean_url(url)
        print(f"{Fore.CYAN}[SMART PAGINATION API]{Style.RESET_ALL} Akıllı pagination scraping başlatılıyor...")
        
        # Smart pagination scraping
        result = system._smart_pagination_scrape(clean_url, max_pages)
        
        if not result['success']:
            return APIResponse(
                success=False,
                message=f"Smart pagination scraping başarısız: {result.get('error', 'Bilinmeyen hata')}",
                data={"error": result.get('error', 'Bilinmeyen hata')}
            )
        
        # Supabase'e kaydet
        saved_count = 0
        if save_to_db and system.supabase.supabase:
            print(f"{Fore.CYAN}[SUPABASE]{Style.RESET_ALL} Blog linkleri Supabase'e kaydediliyor...")
            domain = clean_url.split('/')[2]
            
            for link in result['blog_links'][:100]:  # İlk 100 linki kaydet
                try:
                    link_id = system.supabase.save_link(
                        url=link,
                        domain=domain,
                        content_type='blog_post_smart_pagination',
                        content_length=0
                    )
                    if link_id:
                        saved_count += 1
                except Exception as e:
                    print(f"{Fore.YELLOW}[SUPABASE WARNING]{Style.RESET_ALL} Blog link kaydedilemedi {link}: {e}")
                    continue
        
        return APIResponse(
            success=True,
            message=f"{result['total_blog_posts']} blog yazısı bulundu, {saved_count} Supabase'e kaydedildi (SMART PAGINATION)",
            data={
                "total_blog_posts": result['total_blog_posts'],
                "saved_to_db": saved_count,
                "pages_scraped": result['pages_scraped'],
                "blog_links": result['blog_links'][:20],  # İlk 20 blog linki
                "mode": "smart_pagination"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/scraping/next-button-scraping", response_model=APIResponse)
async def next_button_scraping(
    url: str,
    max_pages: int = Query(20, ge=1, le=50, description="Maksimum sayfa sayısı"),
    save_to_db: bool = Query(False, description="Supabase'e kaydet"),
    system: UnifiedLinkSystem = Depends(get_unified_system)
):
    """Next butonuna tıklayarak pagination scraping"""
    try:
        # URL'yi temizle
        clean_url = system._clean_url(url)
        print(f"{Fore.CYAN}[NEXT BUTTON SCRAPING]{Style.RESET_ALL} Next buton scraping başlatılıyor...")
        
        # Next buton scraping
        scraper = LinkScraper(clean_url, 0, 0.1, 1)
        result = await scraper._next_button_scrape(clean_url, max_pages)
        
        if not result['success']:
            return APIResponse(
                success=False,
                message=f"Next buton scraping başarısız: {result.get('error', 'Bilinmeyen hata')}",
                data={"error": result.get('error', 'Bilinmeyen hata')}
            )
        
        # Articles tablosuna kaydet (zaten _next_button_scrape içinde yapılıyor)
        saved_count = result.get('articles_saved', 0)
        if save_to_db:
            print(f"{Fore.CYAN}[SUPABASE]{Style.RESET_ALL} Articles tablosuna kaydedildi: {saved_count}")
        
        return APIResponse(
            success=True,
            message=f"{result['total_blog_posts']} blog yazısı bulundu, {saved_count} Supabase'e kaydedildi (NEXT BUTTON)",
            data={
                "total_blog_posts": result['total_blog_posts'],
                "saved_to_db": saved_count,
                "pages_scraped": result['pages_scraped'],
                "blog_links": result['blog_links'][:20],  # İlk 20 blog linki
                "mode": "next_button"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Link Endpoints
@app.get("/api/v1/links", response_model=PaginatedResponse)
async def get_links(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    domain: Optional[str] = None,
    system: UnifiedLinkSystem = Depends(get_unified_system)
):
    """Linkleri listele"""
    try:
        if domain:
            links = system.supabase.get_links_by_domain(domain)
        else:
            # Tüm linkleri getir (basit implementasyon)
            links = []
        
        # Sayfalama
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_links = links[start_idx:end_idx]
        
        return PaginatedResponse(
            items=[LinkResponse(**link) for link in paginated_links],
            total=len(links),
            page=page,
            limit=limit,
            pages=(len(links) + limit - 1) // limit,
            has_next=end_idx < len(links),
            has_prev=page > 1
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Keyword Endpoints
@app.post("/api/v1/keywords/generate", response_model=List[KeywordResponse])
async def generate_keywords(
    request: KeywordGenerationRequest,
    system: UnifiedLinkSystem = Depends(get_unified_system)
):
    """Keyword üret"""
    try:
        # Async keyword generation
        keywords = await system.keyword_gen.generate_keywords_async(
            str(request.url),
            request.title,
            request.content
        )
        
        # Limit uygula
        keywords = keywords[:request.max_keywords]
        
        return [KeywordResponse(
            id=0,
            keyword=kw['keyword'],
            relevance_score=kw['relevance_score'],
            source=kw['source'],
            category=kw.get('category', 'secondary'),
            created_at=datetime.now().isoformat()
        ) for kw in keywords]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/keywords/search", response_model=SearchResponse)
async def search_keywords(
    keyword: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
    system: UnifiedLinkSystem = Depends(get_unified_system)
):
    """Keyword ile arama yap"""
    try:
        results = system.search_keywords(keyword)
        
        # Limit uygula
        results = results[:limit]
        
        return SearchResponse(
            keyword=keyword,
            results=[LinkResponse(**item) for item in results],
            total_found=len(results)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/keywords/generate-batch", response_model=APIResponse)
async def generate_keywords_batch(
    limit: int = Query(50, ge=1, le=100, description="Maksimum link sayısı"),
    system: UnifiedLinkSystem = Depends(get_unified_system)
):
    """Database'deki linklerin keyword'lerini toplu olarak üret"""
    try:
        print(f"{Fore.CYAN}[BATCH KEYWORD GENERATION]{Style.RESET_ALL} Toplu keyword üretimi başlatılıyor...")
        
        # Database'den linkleri çek
        links = system.supabase.get_links(limit=limit)
        print(f"{Fore.CYAN}[BATCH KEYWORD]{Style.RESET_ALL} {len(links)} link bulundu")
        
        if not links:
            return APIResponse(
                success=False,
                message="Database'de link bulunamadı",
                data={"error": "No links found in database"}
            )
        
        # Keyword üretimi için URL'leri hazırla
        url_data_list = []
        for link in links:
            url_data_list.append((link['url'], link.get('title', ''), ''))
        
        print(f"{Fore.CYAN}[BATCH KEYWORD]{Style.RESET_ALL} {len(url_data_list)} URL için keyword üretiliyor...")
        
        # Batch keyword generation
        keyword_generator = AsyncKeywordGenerator()
        all_keywords = await keyword_generator.generate_keywords_batch(url_data_list)
        
        # Keyword'leri database'e kaydet
        saved_count = 0
        for i, keywords in enumerate(all_keywords):
            if keywords and len(keywords) > 0:
                try:
                    link_id = links[i]['id']
                    system.supabase.save_keywords(link_id, keywords)
                    saved_count += 1
                    print(f"{Fore.GREEN}[BATCH KEYWORD SUCCESS]{Style.RESET_ALL} Link {i+1}: {len(keywords)} keyword kaydedildi")
                except Exception as e:
                    print(f"{Fore.YELLOW}[BATCH KEYWORD WARNING]{Style.RESET_ALL} Link {i+1} keyword kaydedilemedi: {e}")
                    continue
        
        return APIResponse(
            success=True,
            message=f"{saved_count} link için keyword üretildi ve kaydedildi",
            data={
                "total_links": len(links),
                "processed_links": saved_count,
                "total_keywords": sum(len(keywords) for keywords in all_keywords if keywords)
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Linkify Endpoints
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

@app.post("/api/v1/linkify/batch", response_model=BatchLinkifyResponse)
async def batch_linkify(
    request: BatchLinkifyRequest,
    system: UnifiedLinkSystem = Depends(get_unified_system)
):
    """Toplu linkify işlemi"""
    try:
        results = []
        total_links_added = 0
        
        for text in request.texts:
            linkified_text = system.linkify_text(text)
            stats = system.linkifier.get_linkification_stats(text)
            
            results.append(LinkifyResponse(
                original_text=text,
                linkified_text=linkified_text,
                links_added=stats['links_added'],
                matched_keywords=stats['matched_keywords'],
                total_keywords=stats['total_keywords']
            ))
            
            total_links_added += stats['links_added']
        
        return BatchLinkifyResponse(
            results=results,
            total_processed=len(request.texts),
            total_links_added=total_links_added
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Stats Endpoints
@app.get("/api/v1/stats/domain/{domain}", response_model=StatsResponse)
async def get_domain_stats(
    domain: str,
    system: UnifiedLinkSystem = Depends(get_unified_system)
):
    """Domain istatistiklerini getir"""
    try:
        system.get_domain_stats(domain)
        
        # Basit stats response
        return StatsResponse(
            domain=domain,
            total_links=0,
            total_keywords=0,
            content_type_distribution={},
            keyword_distribution={},
            last_scraping=None
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Background Tasks
async def run_enhanced_scraping_task(url: str, max_depth: int, delay: float, max_workers: int):
    """Background enhanced scraping task"""
    print(f"[ENHANCED SCRAPING] Başlatılıyor: {url}")
    
    try:
        system = UnifiedLinkSystem()
        success = await system.enhanced_scrape(url, max_depth, delay, max_workers)
        
        if success:
            print(f"[ENHANCED SCRAPING] Başarıyla tamamlandı: {url}")
        else:
            print(f"[ENHANCED SCRAPING] Başarısız: {url}")
            
    except Exception as e:
        print(f"[ENHANCED SCRAPING] Hata: {e}")

# =============================================================================
# CLI INTERFACE
# =============================================================================

def main():
    """Ana fonksiyon"""
    parser = argparse.ArgumentParser(
        description='Unified Link System - Tüm sistemi tek dosyada',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Örnekler:
  python unified_link_system.py --scrape https://example.com
  python unified_link_system.py --enhanced-scrape https://example.com
  python unified_link_system.py --linkify "Bu bir test metnidir"
  python unified_link_system.py --search "blog"
  python unified_link_system.py --stats example.com
  python unified_link_system.py --api --host 0.0.0.0 --port 8000
        """
    )
    
    parser.add_argument('--scrape', help='Website scraping')
    parser.add_argument('--enhanced-scrape', help='Enhanced scraping (keyword\'lerle)')
    parser.add_argument('--linkify', help='Text linkify')
    parser.add_argument('--search', help='Keyword search')
    parser.add_argument('--stats', help='Domain statistics')
    parser.add_argument('--depth', type=int, default=2, help='Max depth (default: 2)')
    parser.add_argument('--delay', type=float, default=1.0, help='Delay between requests (default: 1.0)')
    parser.add_argument('--workers', type=int, default=10, help='Max workers (default: 10)')
    
    # API seçenekleri
    parser.add_argument('--api', action='store_true', help='API server başlat')
    parser.add_argument('--host', default='0.0.0.0', help='API host (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=8000, help='API port (default: 8000)')
    parser.add_argument('--reload', action='store_true', help='Auto reload (development)')
    parser.add_argument('--workers-api', type=int, default=1, help='API workers (default: 1)')
    parser.add_argument('--log-level', default='info', help='Log level (default: info)')
    
    args = parser.parse_args()
    
    print(f"{Fore.CYAN}Unified Link System v1.0{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    
    # API server başlat
    if args.api:
        print(f"{Fore.GREEN}[API MODE]{Style.RESET_ALL} API server başlatılıyor...")
        print(f"Host: {args.host}")
        print(f"Port: {args.port}")
        print(f"Reload: {args.reload}")
        print(f"Workers: {args.workers_api}")
        print(f"Log Level: {args.log_level}")
        print(f"{Fore.YELLOW}[DOCS]{Style.RESET_ALL} Swagger UI: http://{args.host}:{args.port}/docs")
        print(f"{Fore.YELLOW}[DOCS]{Style.RESET_ALL} ReDoc: http://{args.host}:{args.port}/redoc")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        
        import uvicorn
        uvicorn.run(
            app,
            host=args.host,
            port=args.port,
            reload=args.reload,
            workers=args.workers_api if not args.reload else 1,
            log_level=args.log_level
        )
        return
    
    # CLI modu
    system = UnifiedLinkSystem()
    
    try:
        if args.scrape:
            # Website scraping
            if not args.scrape.startswith(('http://', 'https://')):
                args.scrape = 'https://' + args.scrape
            
            links = system.scrape_website(args.scrape, args.depth, args.delay, args.workers)
            print(f"\n{Fore.GREEN}[COMPLETED]{Style.RESET_ALL} {len(links)} link bulundu!")
            
        elif args.enhanced_scrape:
            # Enhanced scraping
            if not args.enhanced_scrape.startswith(('http://', 'https://')):
                args.enhanced_scrape = 'https://' + args.enhanced_scrape
            
            success = asyncio.run(system.enhanced_scrape(args.enhanced_scrape, args.depth, args.delay, args.workers))
            if success:
                print(f"\n{Fore.GREEN}[COMPLETED]{Style.RESET_ALL} Enhanced scraping tamamlandı!")
            else:
                print(f"\n{Fore.RED}[FAILED]{Style.RESET_ALL} Enhanced scraping başarısız!")
                
        elif args.linkify:
            # Text linkify
            linkified = system.linkify_text(args.linkify)
            print(f"\n{Fore.CYAN}[ORIGINAL]{Style.RESET_ALL}")
            print(args.linkify)
            print(f"\n{Fore.CYAN}[LINKIFIED]{Style.RESET_ALL}")
            print(linkified)
            
        elif args.search:
            # Keyword search
            results = system.search_keywords(args.search)
            
        elif args.stats:
            # Domain stats
            system.get_domain_stats(args.stats)
            
        else:
            parser.print_help()
            
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[INTERRUPTED]{Style.RESET_ALL} İşlem kullanıcı tarafından durduruldu.")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Fore.RED}[ERROR]{Style.RESET_ALL} Hata oluştu: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
