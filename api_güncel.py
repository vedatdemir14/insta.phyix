from flask import Flask, request, jsonify, g, has_request_context
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
        def as_dict(self):
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

# Embedding-based linkleme sistemi
try:
    from linkify_embedding import linkify_with_embeddings, EmbeddingLinkifier
    EMBEDDING_AVAILABLE = True
except (ImportError, Exception) as e:
    EMBEDDING_AVAILABLE = False
    print(f"⚠️ Embedding-based linkleme sistemi yüklenemedi: {e}")
    print("💡 VPS'te model yoksa bu normaldir. Model yüklemek için:")
    print("   1. Fine-tuned model: python train_health_embedding.py")
    print("   2. Base model: İlk kullanımda otomatik indirilir (internet gerekli)")

app = Flask(__name__)

def _ensure_token_usage_store():
    """Ensure per-request token usage store exists and return it."""
    if not has_request_context():
        return None
    if not hasattr(g, "token_usage") or not isinstance(getattr(g, "token_usage"), dict):
        g.token_usage = {"input_tokens": 0, "output_tokens": 0}
    return g.token_usage

@app.before_request
def _initialize_token_usage():
    """Initialize token usage tracking for each incoming request."""
    _ensure_token_usage_store()

def _extract_usage_numbers(usage_obj):
    """Extract prompt/input and completion/output token counts from various usage objects."""
    if usage_obj is None:
        return 0, 0
    if isinstance(usage_obj, dict):
        data = usage_obj
    else:
        data = {}
        for attr in ("prompt_tokens", "input_tokens", "completion_tokens", "output_tokens"):
            if hasattr(usage_obj, attr):
                data[attr] = getattr(usage_obj, attr)
    prompt_tokens = data.get("prompt_tokens")
    if prompt_tokens is None:
        prompt_tokens = data.get("input_tokens")
    completion_tokens = data.get("completion_tokens")
    if completion_tokens is None:
        completion_tokens = data.get("output_tokens")
    return int(prompt_tokens or 0), int(completion_tokens or 0)

def _record_token_usage(prompt_tokens=0, completion_tokens=0):
    """Accumulate token usage for the active request."""
    store = _ensure_token_usage_store()
    if store is None:
        app.logger.warning("⚠️ Token usage store not available (no request context)")
        return
    # Token sayılarını topla (0'dan büyükse)
    if prompt_tokens and prompt_tokens > 0:
        store["input_tokens"] = store.get("input_tokens", 0) + int(prompt_tokens)
    if completion_tokens and completion_tokens > 0:
        store["output_tokens"] = store.get("output_tokens", 0) + int(completion_tokens)

def _current_token_usage():
    """Return the current token usage structure including totals."""
    store = _ensure_token_usage_store()
    if store is None:
        return None
    input_tokens = int(store.get("input_tokens", 0))
    output_tokens = int(store.get("output_tokens", 0))
    usage = {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens
    }
    # Kullanıcı talepleri için kısa isimler de ekle
    usage["input"] = usage["input_tokens"]
    usage["output"] = usage["output_tokens"]
    usage["total"] = usage["total_tokens"]
    return usage

@app.after_request
def _inject_token_usage(response):
    """Append token usage information to JSON responses."""
    try:
        if response.is_json:
            data = response.get_json(silent=True)
            usage = _current_token_usage()
            if isinstance(data, dict) and usage is not None:
                data["token_usage"] = usage
                response.set_data(json.dumps(data, ensure_ascii=False))
                response.mimetype = "application/json"
                app.logger.info(
                    "🎯 Token kullanımı | Input: %s | Output: %s | Total: %s",
                    usage.get("input_tokens", 0),
                    usage.get("output_tokens", 0),
                    usage.get("total_tokens", 0)
                )
    except Exception as exc:
        app.logger.warning(f"Token usage injection failed: {exc}")
    return response

# ==================== API Keys and Constants ====================
SUPABASE_TABLE = os.getenv('SUPABASE_TABLE')
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_API_KEY = os.getenv('SUPABASE_API_KEY')
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
GPT_MODEL = os.getenv('GPT_MODEL')
DEEPL_KEY = os.getenv('DEEPL_KEY')
SERP_API_KEY = os.getenv('SERP_API_KEY')
USE_GPT_MOCK = os.getenv('USE_GPT_MOCK', '').lower() in ('true', '1', 'yes')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
UNSPLASH_ACCESS_KEY = os.getenv('UNSPLASH_ACCESS_KEY')

# Embedding sistemi için environment variables set et
# (linkify_embedding.py modül seviyesinde os.getenv() kullanıyor)
if SUPABASE_URL:
    os.environ['SUPABASE_URL'] = SUPABASE_URL
if SUPABASE_API_KEY:
    os.environ['SUPABASE_API_KEY'] = SUPABASE_API_KEY
if SUPABASE_TABLE:
    os.environ['SUPABASE_TABLE'] = SUPABASE_TABLE

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
        """Async keyword generator'ı başlat (OpenAI)"""
        self.api_key = api_key or OPENAI_API_KEY
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
       
        if self.api_key:
            self.client = AsyncOpenAI(
                api_key=self.api_key,
                base_url="https://api.openai.com/v1"
            )
        else:
            self.client = None
            print("⚠️ OpenAI API key bulunamadı")
   
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
                    temperature=0.7
                )
               
                # Token usage bilgisini kaydet
                usage_attr = getattr(response, "usage", None)
                app.logger.debug(f"AsyncOpenAI response usage attribute: {usage_attr}")
               
                if usage_attr:
                    prompt_tokens, completion_tokens = _extract_usage_numbers(usage_attr)
                    _record_token_usage(prompt_tokens, completion_tokens)
                    app.logger.info(f"📊 Async token usage: input={prompt_tokens}, output={completion_tokens}")
                else:
                    app.logger.warning("⚠️ No token usage found in AsyncOpenAI response")
               
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
        # Pagination tipi cache (domain bazında)
        self.pagination_cache = {}
   
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
               
                from selenium.webdriver.chrome.service import Service
                import os
               
                # Docker container içinde mi kontrol et
                is_docker = os.path.exists('/.dockerenv') or os.path.exists('/app')
               
                if is_docker:
                    # Docker container içinde - direkt path kullan
                    # Google Chrome genellikle /usr/bin/google-chrome-stable veya /usr/bin/google-chrome konumunda kurulur
                    # Önce google-chrome-stable'ı dene, yoksa google-chrome'u dene
                    chrome_binary_path = None
                    possible_paths = ['/usr/bin/google-chrome-stable', '/usr/bin/google-chrome', '/opt/google/chrome/chrome']
                    for path in possible_paths:
                        if os.path.exists(path):
                            chrome_binary_path = path
                            break
                   
                    if not chrome_binary_path:
                        raise Exception("Google Chrome binary bulunamadı. Olası konumlar: " + ", ".join(possible_paths))
                   
                    chrome_driver_path = '/usr/bin/chromedriver'
                   
                    # Docker için ek Chrome argümanları
                    chrome_options.add_argument('--headless=new')
                    chrome_options.add_argument('--single-process')
                    chrome_options.add_argument('--disable-software-rasterizer')
                    chrome_options.add_argument('--disable-background-timer-throttling')
                    chrome_options.add_argument('--disable-backgrounding-occluded-windows')
                    chrome_options.add_argument('--disable-renderer-backgrounding')
                    chrome_options.add_argument('--disable-features=TranslateUI')
                    chrome_options.add_argument('--disable-ipc-flooding-protection')
                   
                    # Chrome binary path'ini ayarla
                    chrome_options.binary_location = chrome_binary_path
                   
                    # Chrome driver service
                    service = Service(chrome_driver_path)
                    print(f"🐳 Docker mode: Using {chrome_binary_path} and {chrome_driver_path}")
                else:
                    # Local'de - webdriver_manager kullan
                    from webdriver_manager.chrome import ChromeDriverManager
                    service = Service(ChromeDriverManager().install())
                    print(f"💻 Local mode: Using webdriver_manager")
               
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
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
        """Pagination container'ını bul (sayfanın her yerinde) - hata toleranslı - Button ve link desteği"""
        try:
            container_selectors = [
                "nav.pagination.dynamic-pagination",  # Medical Park gibi button-based pagination
                "nav.pagination", ".pagination", ".pager", ".page-navigation", ".pagination-wrapper",
                ".pagination-container", ".pagination-nav", ".pagination-list",
                "ul.pagination", ".pagination ul",
                ".page-numbers", ".wp-pagenavi", ".pagination-box",
                ".pagination-bar", ".pagination-menu", ".pagination-controls",
                ".pagination-buttons", ".pagination-links"
            ]
           
            for selector in container_selectors:
                try:
                    containers = driver.find_elements(By.CSS_SELECTOR, selector)
                    for i, container in enumerate(containers):
                        try:
                            # Hem link hem de button elementlerini kontrol et
                            links = container.find_elements(By.TAG_NAME, "a")
                            buttons = container.find_elements(By.TAG_NAME, "button")
                            total_elements = len(links) + len(buttons)
                           
                            if total_elements >= 3:  # En az 3 element olmalı (link veya button)
                                print(f"✅ Pagination container bulundu: {selector} (Container {i+1}) - {len(links)} link, {len(buttons)} button")
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
        """Container içinde Next butonunu bul (gelişmiş) - Button ve link desteği"""
        try:
            # Önce link elementlerini kontrol et
            links = container.find_elements(By.TAG_NAME, "a")
            # Sonra button elementlerini kontrol et (Medical Park gibi button-based pagination için)
            buttons = container.find_elements(By.TAG_NAME, "button")
           
            # Next buton metinleri ve semboller
            next_texts = ['next', 'sonraki', 'ileri', '»', '›', '>', '→', 'next page', 'sonraki sayfa']
           
            # Önce link elementlerini kontrol et
            for link in links:
                try:
                    text = link.text.strip().lower()
                    href = link.get_attribute('href') or ''
                    rel = link.get_attribute('rel') or ''
                    aria_label = link.get_attribute('aria-label') or ''
                    title = link.get_attribute('title') or ''
                   
                    # Disabled kontrolü
                    if 'disabled' in (link.get_attribute('class') or '').lower():
                        continue
                   
                    # Text kontrolü
                    if any(next_text in text for next_text in next_texts):
                        print(f"✅ Next link bulundu: '{text}' - {href}")
                        return link
                   
                    # Rel kontrolü
                    if 'next' in rel.lower():
                        print(f"✅ Next link bulundu (rel): '{rel}' - {href}")
                        return link
                   
                    # Aria-label kontrolü
                    if any(next_text in aria_label.lower() for next_text in next_texts):
                        print(f"✅ Next link bulundu (aria-label): '{aria_label}' - {href}")
                        return link
                   
                    # Title kontrolü
                    if any(next_text in title.lower() for next_text in next_texts):
                        print(f"✅ Next link bulundu (title): '{title}' - {href}")
                        return link
                   
                except Exception as e:
                    continue
           
            # Button elementlerini kontrol et (Medical Park gibi durumlar için)
            for button in buttons:
                try:
                    text = button.text.strip()
                    data_page = button.get_attribute('data-page')
                    disabled = button.get_attribute('disabled')
                    class_name = button.get_attribute('class') or ''
                   
                    # Disabled kontrolü
                    if disabled is not None or 'disabled' in class_name.lower() or 'active' in class_name.lower():
                        continue
                   
                    # Text kontrolü - › veya » karakterleri
                    if any(next_char in text for next_char in ['›', '»', '>']):
                        print(f"✅ Next button bulundu: '{text}' - data-page: {data_page}")
                        return button
                   
                    # data-page kontrolü - Eğer mevcut sayfadan büyükse ve aktif değilse
                    if data_page:
                        try:
                            page_num = int(data_page)
                            # › veya » karakteri içeriyorsa ve sayfa numarası geçerliyse
                            if '›' in text or '»' in text:
                                print(f"✅ Next button bulundu (data-page): {data_page} - '{text}'")
                                return button
                        except ValueError:
                            pass
                   
                except Exception as e:
                    continue
           
            print("⚠️ Next butonu bulunamadı")
            return None
           
        except Exception as e:
            print(f"⚠️ Next buton arama hatası: {e}")
            return None
   
    def detect_pagination_type(self, url, driver=None):
        """
        Pagination tipini otomatik tespit et
        Döndürür: 'url', 'button', 'infinite', 'single'
       
        Args:
            url: Taranacak URL
            driver: Selenium driver (None ise yeni driver oluşturur)
       
        Returns:
            str: Pagination tipi ('url', 'button', 'infinite', 'single')
        """
        from urllib.parse import urlparse
       
        # Domain'i al
        parsed = urlparse(url)
        domain = parsed.netloc
       
        # Cache'de var mı kontrol et
        if domain in self.pagination_cache:
            cached_type = self.pagination_cache[domain]
            print(f"💾 Cache'den pagination tipi: {cached_type} (Domain: {domain})")
            return cached_type
       
        print(f"🔍 Pagination tipi tespit ediliyor: {url}")
       
        # Driver yoksa oluştur
        use_external_driver = driver is not None
        if not driver:
            driver = self._get_selenium_driver()
            if not driver:
                print("⚠️ Driver oluşturulamadı, varsayılan olarak 'button' döndürülüyor")
                return 'button'
       
        try:
            # 1. ÖNCE URL'Yİ KONTROL ET (en hızlı, sayfa yüklemeden)
            from urllib.parse import parse_qs
            query_params = parse_qs(parsed.query)
           
            # URL'de sayfa parametresi var mı?
            page_params = ['page', 'p', 'paged', 'sayfa', 'pagenum', 'pagenumber']
            if any(param in query_params for param in page_params):
                detected_type = 'url'
                print(f"✅ URL-based pagination tespit edildi (URL'de ?page= parametresi var)")
                self.pagination_cache[domain] = detected_type
                if not use_external_driver:
                    driver.quit()
                    self.driver = None
                return detected_type
           
            # 2. SAYFAYI YÜKLE VE PAGINATION CONTAINER ARA
            print("📄 Sayfa yükleniyor...")
            driver.get(url)
            time.sleep(3)
           
            # Scroll yap (lazy loading için)
            self._full_scroll_page(driver)
           
            # Pagination container var mı?
            container = self._find_pagination_container(driver)
            if container:
                # Next button var mı?
                next_button = self._find_next_button_in_container(container)
                if next_button:
                    detected_type = 'button'
                    print(f"✅ Button-based pagination tespit edildi (Next button bulundu)")
                    self.pagination_cache[domain] = detected_type
                    if not use_external_driver:
                        driver.quit()
                        self.driver = None
                    return detected_type
           
            # 3. INFINITE SCROLL KONTROLÜ
            print("🔄 Infinite scroll kontrol ediliyor...")
            initial_links = len(self._extract_all_links_from_page(driver))
            initial_height = driver.execute_script("return document.body.scrollHeight")
           
            # Scroll yap
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
           
            new_links = len(self._extract_all_links_from_page(driver))
            new_height = driver.execute_script("return document.body.scrollHeight")
           
            # İçerik yüklendi mi?
            if new_links > initial_links or new_height > initial_height:
                detected_type = 'infinite'
                print(f"✅ Infinite scroll tespit edildi (Scroll sonrası yeni içerik yüklendi: {new_links - initial_links} yeni link)")
                self.pagination_cache[domain] = detected_type
                if not use_external_driver:
                    driver.quit()
                    self.driver = None
                return detected_type
           
            # 4. HİÇBİRİ YOKSA - BUTTON-BASED (Varsayılan)
            detected_type = 'button'
            print(f"⚠️ Pagination bulunamadı - Varsayılan olarak 'button' kullanılıyor")
            self.pagination_cache[domain] = detected_type
            if not use_external_driver:
                driver.quit()
                self.driver = None
            return detected_type
           
        except Exception as e:
            print(f"⚠️ Pagination tespit hatası: {e}")
            # Hata durumunda varsayılan olarak button döndür
            detected_type = 'button'
            self.pagination_cache[domain] = detected_type
            if not use_external_driver and driver:
                try:
                    driver.quit()
                    self.driver = None
                except:
                    pass
            return detected_type
   
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
                            # Element tag'ini kontrol et
                            tag_name = next_button.tag_name.lower()
                           
                            if tag_name == 'a':
                                # Link element - href'den URL al
                                next_url = next_button.get_attribute('href')
                                if next_url and next_url != current_url:
                                    current_url = next_url
                                    driver.get(current_url)
                                    time.sleep(3)
                                else:
                                    print("⚠️ Next link bulunamadı veya aynı URL")
                                    break
                            elif tag_name == 'button':
                                # Button element - tıklayıp sayfa değişimini bekle (Medical Park gibi)
                                data_page = next_button.get_attribute('data-page')
                                print(f"🔄 Next button tıklanıyor - data-page: {data_page}")
                               
                                # Button'a tıkla
                                driver.execute_script("arguments[0].click();", next_button)
                               
                                # Sayfa yüklenmesini bekle
                                time.sleep(3)
                               
                                # URL değişti mi kontrol et
                                new_url = driver.current_url
                                if new_url != current_url:
                                    current_url = new_url
                                    print(f"✅ Sayfa değişti: {current_url}")
                                else:
                                    # URL değişmediyse sayfa yüklenmesini bekle
                                    try:
                                        WebDriverWait(driver, 10).until(
                                            lambda d: d.execute_script("return document.readyState") == "complete"
                                        )
                                        time.sleep(2)  # Ek bekleme
                                        current_url = driver.current_url
                                        print(f"✅ Sayfa yüklendi: {current_url}")
                                    except TimeoutException:
                                        print("⚠️ Sayfa yüklenmesi zaman aşımına uğradı")
                                        break
                            else:
                                print(f"⚠️ Bilinmeyen element tipi: {tag_name}")
                                break
                               
                        except Exception as e:
                            print(f"❌ Next buton tıklama hatası: {e}")
                            import traceback
                            print(f"Traceback: {traceback.format_exc()}")
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
   
    async def pagination_url_scrape(self, base_url, start_page=1, end_page=None, generate_keywords: bool = True, force: bool = False):
        """URL-based pagination scraping (Florence Nightingale gibi ?page=8 formatı)"""
        try:
            from urllib.parse import urlparse, urlencode, parse_qs, urlunparse
           
            # Base URL'den domain al
            parsed = urlparse(base_url)
            domain = parsed.netloc
           
            # Domain kontrolü (force mode'da atla)
            if not force:
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
            else:
                print(f"🔄 Force mode: Domain kontrolü atlanıyor")
           
            driver = self._get_selenium_driver()
            if not driver:
                return {
                    'success': False,
                    'blog_links': [],
                    'pages_scraped': 0,
                    'error': 'Selenium driver başlatılamadı'
                }
           
            print(f"🚀 URL-based pagination scraping başlatılıyor: {base_url}")
            print(f"📄 Sayfa aralığı: {start_page} - {end_page if end_page else 'sonsuz'}")
           
            all_blog_links = set()
            pages_scraped = 0
            articles_saved = 0
            saved_articles = []
            current_page = start_page
            max_pages_without_new_links = 3  # 3 sayfa üst üste yeni link bulunamazsa dur
            consecutive_empty_pages = 0
           
            # Base URL'den query parametrelerini al
            parsed_url = urlparse(base_url)
            query_params = parse_qs(parsed_url.query)
           
            while True:
                # Sayfa numarasını query parametresine ekle
                query_params['page'] = [str(current_page)]
                new_query = urlencode(query_params, doseq=True)
                current_url = urlunparse((
                    parsed_url.scheme,
                    parsed_url.netloc,
                    parsed_url.path,
                    parsed_url.params,
                    new_query,
                    parsed_url.fragment
                ))
               
                print(f"📄 Sayfa {current_page} işleniyor: {current_url}")
               
                try:
                    driver.get(current_url)
                    time.sleep(3)
                   
                    # Full scroll yap
                    self._full_scroll_page(driver)
                   
                    # Bu sayfadaki tüm linkleri al
                    page_links = self._extract_all_links_from_page(driver)
                    print(f"🔍 Toplam {len(page_links)} link bulundu")
                   
                    # Blog linklerini filtrele
                    blog_links = set()
                    new_links_count = 0
                   
                    for link in page_links:
                        if self._is_blog_post_link(link):
                            clean_link = link.split('#')[0]
                           
                            # Yeni link mi kontrol et
                            if clean_link not in all_blog_links:
                                blog_links.add(clean_link)
                                all_blog_links.add(clean_link)
                                new_links_count += 1
                                print(f"✅ Yeni blog link: {clean_link}")
                               
                                # Article'ı database'e kaydet
                                try:
                                    link_domain = urlparse(clean_link).netloc
                                    parts = [p for p in clean_link.rstrip('/').split('/') if p]
                                    last_seg = parts[-1] if parts else ''
                                    title = last_seg.replace('-', ' ').replace('_', ' ').title()
                                   
                                    article_id = self.supabase.save_article(
                                        title=title,
                                        url=clean_link,
                                        domain=link_domain,
                                        keyword=None
                                    )
                                   
                                    if article_id:
                                        articles_saved += 1
                                        print(f"✅ Article kaydedildi: {title} (ID: {article_id})")
                                        saved_articles.append((article_id, clean_link, title))
                                    else:
                                        print(f"❌ Article kaydedilemedi: {title}")
                                       
                                except Exception as e:
                                    print(f"❌ Article kaydetme hatası {clean_link}: {e}")
                   
                    print(f"✅ Sayfa {current_page}: {len(blog_links)} blog yazısı bulundu ({new_links_count} yeni)")
                   
                    # Yeni link yoksa sayacı artır
                    if new_links_count == 0:
                        consecutive_empty_pages += 1
                        print(f"⚠️ Sayfa {current_page}'de yeni link bulunamadı ({consecutive_empty_pages}/{max_pages_without_new_links})")
                    else:
                        consecutive_empty_pages = 0
                   
                    pages_scraped += 1
                   
                    # End page kontrolü
                    if end_page and current_page >= end_page:
                        print(f"✅ Belirtilen son sayfaya ulaşıldı: {end_page}")
                        break
                   
                    # Yeni link bulunamadıysa dur
                    if consecutive_empty_pages >= max_pages_without_new_links:
                        print(f"⚠️ {max_pages_without_new_links} sayfa üst üste yeni link bulunamadı, scraping durduruluyor")
                        break
                   
                    # Sonraki sayfaya geç
                    current_page += 1
                   
                except Exception as e:
                    print(f"❌ Sayfa {current_page} işleme hatası: {e}")
                    consecutive_empty_pages += 1
                   
                    if consecutive_empty_pages >= max_pages_without_new_links:
                        print(f"⚠️ {max_pages_without_new_links} sayfa üst üste hata, scraping durduruluyor")
                        break
                   
                    current_page += 1
                    continue
           
            # Toplu keyword üretimi
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
            print(f"❌ URL-based pagination scraping hatası: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return {
                'success': False,
                'blog_links': [],
                'pages_scraped': 0,
                'error': str(e)
            }
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
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
                            # Element tag'ini kontrol et
                            tag_name = next_button.tag_name.lower()
                           
                            if tag_name == 'a':
                                # Link element - href'den URL al
                                next_url = next_button.get_attribute('href')
                                if next_url and next_url != current_url:
                                    current_url = next_url
                                    driver.get(current_url)
                                    time.sleep(3)
                                else:
                                    print("⚠️ Next link bulunamadı veya aynı URL")
                                    break
                            elif tag_name == 'button':
                                # Button element - tıklayıp sayfa değişimini bekle (Medical Park gibi)
                                data_page = next_button.get_attribute('data-page')
                                print(f"🔄 Next button tıklanıyor - data-page: {data_page}")
                               
                                # Button'a tıkla
                                driver.execute_script("arguments[0].click();", next_button)
                               
                                # Sayfa yüklenmesini bekle
                                time.sleep(3)
                               
                                # URL değişti mi kontrol et
                                new_url = driver.current_url
                                if new_url != current_url:
                                    current_url = new_url
                                    print(f"✅ Sayfa değişti: {current_url}")
                                else:
                                    # URL değişmediyse sayfa yüklenmesini bekle
                                    try:
                                        WebDriverWait(driver, 10).until(
                                            lambda d: d.execute_script("return document.readyState") == "complete"
                                        )
                                        time.sleep(2)  # Ek bekleme
                                        current_url = driver.current_url
                                        print(f"✅ Sayfa yüklendi: {current_url}")
                                    except TimeoutException:
                                        print("⚠️ Sayfa yüklenmesi zaman aşımına uğradı")
                                        break
                            else:
                                print(f"⚠️ Bilinmeyen element tipi: {tag_name}")
                                break
                               
                        except Exception as e:
                            print(f"❌ Next buton tıklama hatası: {e}")
                            import traceback
                            print(f"Traceback: {traceback.format_exc()}")
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

# Edatlar, bağlaçlar, zarflar ve linklenmemesi gereken kelimeler
STOPWORDS = set([
    # Bağlaçlar
    "ve", "de", "da", "ile", "gibi", "veya", "ama", "fakat", "çünkü", "ki",
    "ya", "ya da", "hem", "hem de", "ancak", "lakin", "ise", "ise de",
    # Edatlar
    "için", "gibi", "kadar", "dolayı", "nedeniyle", "sayesinde", "karşın", "rağmen",
    "doğru", "karşı", "yönünde", "doğrultusunda", "hakkında", "üzerine", "üzerinde",
    "altında", "üstünde", "yanında", "önünde", "arkasında", "içinde", "dışında",
    # Zarflar
    "daha", "çok", "az", "en", "çok", "pek", "oldukça", "fazla", "az", "biraz",
    "sonrası", "öncesi", "sonra", "önce", "şimdi", "henüz", "hala", "artık",
    "yine", "tekrar", "gene", "bir daha", "daha önce", "daha sonra",
    # İşaret zamirleri
    "bu", "şu", "o", "onu", "ona", "onun", "onlar", "onların", "onlara", "onları",
    "bunlar", "şunlar", "bunun", "şunun", "buna", "şuna",
    # Soru kelimeleri
    "nedir", "nasil", "neden", "ne", "kim", "nelerdir", "nasıl", "niçin", "niye",
    # Genel kelimeler - tek başına linklenmemeli
    "belirtileri", "tedavisi", "tedavi", "yapilir", "bulasir", "hastaligi",
    "hastalik", "hastaliklari", "kanseri", "kanser", "nedenleri", "nakli",
    "sismesi", "iltihabi", "cerrahisi", "bakim", "bakimi", "virusu", "sendromu",
    "biyopsisi", "biyopsi", "idrar", "kulak", "orta", "yemek", "karaciger",
    "kemik", "kalp", "solunum", "nelerdir", "neler", "bir", "değil",
    # Olumsuzluk ve soru ekleri
    "mi", "mı", "mu", "mü"
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


def remove_turkish_inflection(text):
    """Türkçe çekim eklerini kaldır (iyelik, hal, çoğul ekleri)"""
    if not text or len(text) < 3:
        return text
   
    # Kelimeleri ayır ve her birini işle
    words = text.split()
    processed_words = []
   
    for word in words:
        original_word = word
        word_lower = word.lower()
       
        # Çoğul ekleri: -lar, -ler (en sonda)
        if len(word_lower) > 4:
            if word_lower.endswith('lar') or word_lower.endswith('ler'):
                word = word[:-3]
                word_lower = word.lower()
       
        # İyelik ekleri ve hal ekleri (daha uzun olanlar önce kontrol edilmeli)
        # İyelik ekleri: -ın, -in, -un, -ün, -ım, -im, -um, -üm, -ı, -i, -u, -ü
        # Hal ekleri: -a, -e, -ı, -i, -u, -ü, -da, -de, -ta, -te, -dan, -den, -tan, -ten, -na, -ne
        # İyelik + hal kombinasyonları: -ına, -ine, -una, -üne, -ında, -inde, -unda, -ünde
       
        # Önce uzun kombinasyonları kontrol et
        if len(word_lower) > 5:
            # İyelik + yönelme: -ına, -ine, -una, -üne
            if word_lower.endswith(('ina', 'ine', 'una', 'une')):
                word = word[:-3]
                word_lower = word.lower()
            # İyelik + bulunma: -ında, -inde, -unda, -ünde
            elif word_lower.endswith(('inda', 'inde', 'unda', 'unde')):
                word = word[:-4]
                word_lower = word.lower()
            # İyelik + ayrılma: -ından, -inden, -undan, -ünden
            elif word_lower.endswith(('indan', 'inden', 'undan', 'unden')):
                word = word[:-5]
                word_lower = word.lower()
       
        # Tek başına iyelik ekleri (kelime 4+ karakter ise)
        if len(word_lower) > 4:
            # -ın, -in, -un, -ün
            if word_lower.endswith(('in', 'un')) and word_lower[-3] in 'aeiou':
                word = word[:-2]
                word_lower = word.lower()
            # -ım, -im, -um, -üm
            elif word_lower.endswith(('im', 'um')) and word_lower[-3] in 'aeiou':
                word = word[:-2]
                word_lower = word.lower()
       
        # Hal ekleri (kelime 3+ karakter ise)
        if len(word_lower) > 3:
            # -dan, -den, -tan, -ten (ayrılma)
            if word_lower.endswith(('dan', 'den', 'tan', 'ten')):
                word = word[:-3]
                word_lower = word.lower()
            # -da, -de, -ta, -te (bulunma)
            elif word_lower.endswith(('da', 'de', 'ta', 'te')):
                word = word[:-2]
                word_lower = word.lower()
            # -na, -ne (yönelme, iyelikli)
            elif word_lower.endswith(('na', 'ne')):
                word = word[:-2]
                word_lower = word.lower()
       
        # Kısa hal ekleri (kelime 3+ karakter ise, son kontrol)
        if len(word_lower) > 3:
            # -a, -e (yönelme)
            if word_lower.endswith(('a', 'e')) and word_lower[-2] not in 'aeiou':
                word = word[:-1]
                word_lower = word.lower()
            # -ı, -i, -u, -ü (belirtme/iyelik)
            elif word_lower.endswith(('i', 'u')) and word_lower[-2] not in 'aeiou':
                word = word[:-1]
                word_lower = word.lower()
       
        # Eğer kelime çok kısaldıysa (2 karakter veya daha az), orijinalini kullan
        if len(word) < 3:
            word = original_word
       
        processed_words.append(word)
   
    return ' '.join(processed_words)


def get_article_titles_from_db(domain=None):
    """Database'den article'ları getir - domain filtresi ile (pagination ile tüm verileri çeker)"""
    headers = {
        "apikey": SUPABASE_API_KEY,
        "Authorization": f"Bearer {SUPABASE_API_KEY}",
        "Content-Type": "application/json",
        "Prefer": "count=exact"  # Toplam sayıyı almak için
    }
   
    all_articles = []
    page_size = 1000  # Supabase'in varsayılan limit'i
    offset = 0
    max_iterations = 100  # Güvenlik için maksimum iterasyon sayısı
   
    try:
        # Domain filtresi varsa ekle
        if domain:
            # Domain'i temizle (http:// veya https:// olmadan)
            clean_domain = domain.replace('http://', '').replace('https://', '').split('/')[0].strip()
           
            # www. olmadan da dene (florence.com.tr ve www.florence.com.tr için)
            domain_variants = [clean_domain]
            if clean_domain.startswith('www.'):
                domain_variants.append(clean_domain.replace('www.', ''))
            else:
                domain_variants.append('www.' + clean_domain)
           
            print(f"🔍 Fetching articles for domain variants: {domain_variants} (with pagination)")
           
            # Her iki domain formatını da dene
            for domain_variant in domain_variants:
                base_url = f"{SUPABASE_URL}/rest/v1/{SUPABASE_TABLE}?select=keyword,url,domain&domain=eq.{domain_variant}"
               
                iteration = 0
                variant_offset = 0
                variant_articles = []
               
                while iteration < max_iterations:
                    url = f"{base_url}&limit={page_size}&offset={variant_offset}"
                    print(f"🔍 Request URL: {url}")
                    response = requests.get(url, headers=headers)
                   
                    print(f"📡 Response status: {response.status_code}")
                    # 200 (OK) ve 206 (Partial Content) başarılı response'lardır
                    if response.status_code not in [200, 206]:
                        print(f"❌ Supabase error: {response.status_code} - {response.text[:500]}")
                        break
                   
                    articles = response.json()
                    print(f"📦 Response data: {len(articles) if articles else 0} articles")
                   
                    if not articles or len(articles) == 0:
                        print(f"⚠️ No articles in response for domain variant: {domain_variant}")
                        break
                   
                    variant_articles.extend(articles)
                    print(f"✅ Added {len(articles)} articles (total: {len(variant_articles)})")
                   
                    if len(articles) < page_size:
                        break
                    variant_offset += page_size
                    iteration += 1
               
                if variant_articles:
                    print(f"✅ Found {len(variant_articles)} articles for domain: {domain_variant}")
                    all_articles.extend(variant_articles)
                    break  # Bir variant'ta bulduysak diğerini denemeye gerek yok
                else:
                    print(f"⚠️ No articles found for domain variant: {domain_variant}")
           
            if not all_articles:
                print(f"⚠️ No articles found for any domain variant")
                return []
        else:
            # Domain yoksa tüm article'ları getir
            base_url = f"{SUPABASE_URL}/rest/v1/{SUPABASE_TABLE}?select=keyword,url,domain"
            print(f"🔍 Fetching all articles (no domain filter, with pagination)")
           
            iteration = 0
            while iteration < max_iterations:
                # Pagination parametreleri ekle
                url = f"{base_url}&limit={page_size}&offset={offset}"
                print(f"🔍 Request URL: {url}")
               
                response = requests.get(url, headers=headers)
                print(f"📡 Response status: {response.status_code}")
               
                # 200 (OK) ve 206 (Partial Content) başarılı response'lardır
                if response.status_code in [200, 206]:
                    articles = response.json()
                    print(f"📦 Response data: {len(articles) if articles else 0} articles")
                   
                    if not articles or len(articles) == 0:
                        # Daha fazla veri yok
                        print(f"⚠️ No more articles to fetch")
                        break
                   
                    all_articles.extend(articles)
                    print(f"📦 Fetched {len(articles)} articles (total so far: {len(all_articles)})")
                   
                    # Eğer bu sayfada page_size'den az veri varsa, son sayfadayız
                    if len(articles) < page_size:
                        break
                   
                    # Sonraki sayfaya geç
                    offset += page_size
                    iteration += 1
                else:
                    print(f"❌ Supabase fetch error: {response.status_code} - {response.text[:500]}")
                    break
       
        print(f"✅ Found {len(all_articles)} total articles from database")
        if domain:
            print(f"📌 Domain filter applied: {domain}")
       
        # Debug: İlk 5 article'ın domain'ini göster
        if all_articles:
            print(f"📋 Sample domains from database: {[a.get('domain', 'N/A') for a in all_articles[:5]]}")
        else:
            print(f"⚠️ No articles found - checking if table exists and has data...")
            # Test query: Tüm article'ları say
            test_url = f"{SUPABASE_URL}/rest/v1/{SUPABASE_TABLE}?select=count"
            test_response = requests.get(test_url, headers=headers)
            print(f"🔍 Test query response: {test_response.status_code}")
            if test_response.status_code == 200:
                print(f"📊 Test query result: {test_response.text[:200]}")
       
        return all_articles
       
    except Exception as e:
        print(f"❌ Supabase connection error: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return all_articles if all_articles else []


def normalize(text):
    # Küçük harfe çevir, baştaki/sondaki boşlukları temizle, noktalama işaretlerini temizle
    text = text.lower().strip()
    # Noktalama işaretlerini boşlukla değiştir (word boundary için)
    text = re.sub(r'[^\w\s]', ' ', text)
    # Fazla boşlukları temizle
    return re.sub(r'\s+', ' ', text).strip()


def is_stopword_or_short(text):
    # Sadece stopword veya 3 harften kısa ise True döner
    words = text.split()
    return (
            all(w in STOPWORDS for w in words) or
            any(len(w) < 3 for w in words)
    )


def _make_openai_request(prompt, temperature=0.7, stream=False):
    """OpenAI API'ye istek yap ve yanıtı döndür"""
    try:
        url = "https://api.openai.com/v1/chat/completions"
       
        payload = {
            "model": GPT_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature
        }
       
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
       
        if stream:
            # Payload'ı kopyala ve stream=True ekle
            streaming_payload = payload.copy()
            streaming_payload['stream'] = True
            # Streaming modda token usage bilgisini almak için stream_options ekle
            streaming_payload['stream_options'] = {"include_usage": True}
           
            response = requests.post(
                url,
                headers=headers,
                json=streaming_payload,
                timeout=(10, 60),  # Hız optimizasyonu: 10s connect, 60s read
                stream=True
            )
            response.raise_for_status()
           
            # Streaming yanıtını topla (SSE format)
            # OpenAI streaming modda usage bilgisi genellikle son chunk'ta gelir
            full_content = ""
            prompt_tokens_collected = 0
            completion_tokens_collected = 0
           
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        data_str = line_str[6:]  # 'data: ' kısmını kaldır
                        if data_str.strip() == '[DONE]':
                            break
                        try:
                            chunk_data = json.loads(data_str)
                           
                            # Content'i topla
                            if 'choices' in chunk_data and len(chunk_data['choices']) > 0:
                                delta = chunk_data['choices'][0].get('delta', {})
                                content = delta.get('content', '')
                                if content:
                                    full_content += content
                           
                            # Token usage bilgisini topla (stream_options ile birlikte gelir)
                            # Usage bilgisi genellikle son chunk'ta gelir, ama her chunk'ta kontrol et
                            usage_info = chunk_data.get('usage')
                            if usage_info:
                                prompt_tokens, completion_tokens = _extract_usage_numbers(usage_info)
                                # En yüksek değerleri al (son chunk genellikle toplam değerleri içerir)
                                if prompt_tokens > prompt_tokens_collected:
                                    prompt_tokens_collected = prompt_tokens
                                if completion_tokens > completion_tokens_collected:
                                    completion_tokens_collected = completion_tokens
                        except json.JSONDecodeError:
                            continue
           
            # Token usage'ı kaydet
            if prompt_tokens_collected or completion_tokens_collected:
                _record_token_usage(prompt_tokens_collected, completion_tokens_collected)
                app.logger.info(f"📊 Streaming token usage: input={prompt_tokens_collected}, output={completion_tokens_collected}")
            else:
                app.logger.warning("⚠️ No token usage found in streaming response - Check if stream_options is set correctly")
           
            return full_content.strip()
        else:
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=(5, 30)  # Hız optimizasyonu: 5s connect, 30s read (daha agresif)
            )
            response.raise_for_status()
           
            data = response.json()
            # Debug: Response'u logla (usage bilgisini görmek için)
            app.logger.debug(f"OpenAI non-streaming response keys: {list(data.keys())}")
           
            # Token usage bilgisini kaydet
            usage_info = data.get("usage")
            if usage_info:
                prompt_tokens, completion_tokens = _extract_usage_numbers(usage_info)
                _record_token_usage(prompt_tokens, completion_tokens)
                app.logger.info(f"📊 Non-streaming token usage: input={prompt_tokens}, output={completion_tokens}")
            else:
                app.logger.warning(f"⚠️ No token usage found in non-streaming response. Response keys: {list(data.keys())}")
           
            if "choices" in data and len(data["choices"]) > 0:
                return data["choices"][0]["message"]["content"].strip()
           
            return ""
    except requests.exceptions.HTTPError as e:
        error_detail = ""
        if hasattr(e.response, 'text'):
            try:
                error_data = e.response.json()
                error_detail = f" - {error_data}"
            except:
                error_detail = f" - {e.response.text[:200]}"
       
        # 503 (Service Unavailable) hatası için özel mesaj
        if e.response.status_code == 503:
            print(f"⚠️ OpenAI API 503: Model aşırı yüklü, tekrar deneniyor...")
            raise requests.exceptions.RequestException(f"503 Service Unavailable - Model overloaded") from e
       
        print(f"⚠️ OpenAI API HTTP error: {e.response.status_code} {e.response.reason}{error_detail}")
        raise
    except Exception as e:
        print(f"⚠️ OpenAI API request error: {e}")
        raise


def _identify_linkable_phrases_with_gpt(text, available_keywords):
    """GPT ile metindeki linklenebilir kelime gruplarını tespit et ve database keyword'leriyle eşleştir - TÜM METNİ ANALİZ EDER"""
    try:
        # available_keywords kontrolü
        if not available_keywords or len(available_keywords) == 0:
            print(f"⚠️ available_keywords boş, GPT phrase tespiti atlanıyor")
            return []
       
        # Mevcut keyword'lerin bir listesini hazırla (GPT-4o-mini 128K token destekliyor, daha fazla keyword göster)
        keywords_preview = [kw[1] for kw in available_keywords[:1000] if len(kw) > 1]  # 200'den 1000'e çıkarıldı, güvenlik kontrolü eklendi
       
        # Metni parçalara böl (GPT-4o-mini 128K token destekliyor, limit artırıldı)
        # Her parça maksimum 20000 karakter (yaklaşık 5000 token), paragraf sınırlarını koru
        # Önce paragraflara böl
        paragraphs = text.split('\n\n')
       
        # Paragrafları birleştirerek 20000 karakterlik parçalar oluştur
        text_chunks = []
        current_chunk = ""
        CHUNK_SIZE = 50000  # Hız optimizasyonu için 50K'ya düşürüldü (GPT-4o-mini için optimal)
       
        for para in paragraphs:
            # Eğer tek bir paragraf CHUNK_SIZE'dan uzunsa, onu da böl
            if len(para) > CHUNK_SIZE:
                # Uzun paragrafı cümlelere böl
                sentences = re.split(r'[.!?]\s+', para)
                current_sentence_chunk = ""
                for sentence in sentences:
                    if len(current_sentence_chunk) + len(sentence) < CHUNK_SIZE:
                        current_sentence_chunk += sentence + ". "
                    else:
                        if current_sentence_chunk:
                            text_chunks.append(current_sentence_chunk.strip())
                        current_sentence_chunk = sentence + ". "
                if current_sentence_chunk:
                    if len(current_chunk) + len(current_sentence_chunk) < CHUNK_SIZE:
                        current_chunk += current_sentence_chunk
                    else:
                        if current_chunk:
                            text_chunks.append(current_chunk.strip())
                        current_chunk = current_sentence_chunk
            else:
                # Paragrafı mevcut chunk'a ekle
                if len(current_chunk) + len(para) + 2 < CHUNK_SIZE:  # +2 for \n\n
                    current_chunk += para + "\n\n"
                else:
                    if current_chunk:
                        text_chunks.append(current_chunk.strip())
                    current_chunk = para + "\n\n"
       
        # Son chunk'ı ekle
        if current_chunk:
            text_chunks.append(current_chunk.strip())
       
        # Eğer hiç chunk yoksa (çok kısa metin), tüm metni kullan
        if not text_chunks:
            text_chunks = [text]
       
        print(f"📝 Metin {len(text_chunks)} parçaya bölündü (toplam {len(text)} karakter)")
       
        # Hız optimizasyonu: Maksimum 3 parça analiz et (çok uzun metinlerde)
        MAX_CHUNKS_TO_ANALYZE = 3  # 5'ten 3'e düşürüldü (hız için)
        if len(text_chunks) > MAX_CHUNKS_TO_ANALYZE:
            print(f"⚠️ Metin çok uzun ({len(text_chunks)} parça), sadece ilk {MAX_CHUNKS_TO_ANALYZE} parça analiz edilecek")
            text_chunks = text_chunks[:MAX_CHUNKS_TO_ANALYZE]
       
        # Tüm parçaları analiz et ve sonuçları birleştir
        all_phrases = set()
       
        for chunk_idx, chunk in enumerate(text_chunks, 1):
            print(f"🔍 Parça {chunk_idx}/{len(text_chunks)} analiz ediliyor... ({len(chunk)} karakter)")
           
            prompt = f"""Türkçe metni analiz et ve linklenebilir kelime gruplarını bul.

Metin (Parça {chunk_idx}/{len(text_chunks)}):
{chunk}

Keyword örnekleri:
{chr(10).join(keywords_preview[:150])}

KURALLAR:
- Sadece İSİMLER linklenmeli (edat/bağlaç/zarf/sıfat değil)
- Keyword'lerle eşleşen veya benzer kelime gruplarını bul
- İç içe link yok - uzun olanı seç
- Örnek: "mide bulantısı" EVET, "sağlıklı" HAYIR

Format: Her satırda bir kelime grubu (tamlamalar önce)
Sadece kelime gruplarını listele."""

            print(f"🤖 GPT ile parça {chunk_idx}/{len(text_chunks)} analiz ediliyor... (streaming)")
           
            # Retry mekanizması - Hızlandırıldı: 2 deneme, kısa timeout
            max_retries = 2  # 3'ten 2'ye düşürüldü (hız için)
            content = ""
            chunk_start_time = time.time()
            MAX_CHUNK_TIME = 30  # Her parça için maksimum 30 saniye
           
            for attempt in range(1, max_retries + 1):
                # Timeout kontrolü - çok uzun sürerse atla
                if time.time() - chunk_start_time > MAX_CHUNK_TIME:
                    print(f"⏱️ Parça {chunk_idx} için zaman aşımı ({MAX_CHUNK_TIME}s), atlanıyor...")
                    break
               
                try:
                    # Streaming kullan
                    content = _make_openai_request(prompt, temperature=0.3, stream=True)
                    break  # Başarılı, döngüden çık
                except requests.exceptions.Timeout as e:
                    print(f"⏱️ Timeout hatası (Attempt {attempt}/{max_retries}), hızlı geçiliyor...")
                    if attempt < max_retries:
                        time.sleep(1)  # Sadece 1 saniye bekle
                        continue
                    else:
                        content = ""
                        break
                except requests.exceptions.RequestException as e:
                    error_str = str(e)
                    # 503 hatası için özel bekleme
                    if "503" in error_str or "overloaded" in error_str.lower():
                        if attempt < max_retries:
                            wait_time = attempt * 2  # 503 için hızlı bekleme (2s, 4s, 6s) - hızlandırıldı
                            print(f"⚠️ Model aşırı yüklü (503), {wait_time} saniye bekleniyor... (Attempt {attempt}/{max_retries})")
                            time.sleep(wait_time)
                            continue
                        else:
                            print(f"⚠️ 503 hatası: Tüm denemeler başarısız, normal istek deneniyor...")
                            # Son deneme: Normal istek
                            try:
                                content = _make_openai_request(prompt, temperature=0.3, stream=False)
                                break
                            except:
                                content = ""
                                break
                    else:
                        # Diğer hatalar için fallback
                        if attempt < max_retries:
                            print(f"⚠️ Streaming hatası, normal istek deneniyor (Attempt {attempt}/{max_retries}): {e}")
                            try:
                                content = _make_openai_request(prompt, temperature=0.3, stream=False)
                                break
                            except:
                                wait_time = attempt * 1  # Hızlandırıldı (1s, 2s, 3s)
                                print(f"⏳ {wait_time} saniye bekleniyor...")
                                time.sleep(wait_time)
                                continue
                        else:
                            print(f"⚠️ Tüm denemeler başarısız")
                            content = ""
                            break
                except Exception as e:
                    print(f"⚠️ Beklenmeyen hata (Attempt {attempt}/{max_retries}): {e}")
                    if attempt < max_retries:
                        wait_time = attempt * 1  # Hızlandırıldı (1s, 2s, 3s)
                        time.sleep(wait_time)
                        continue
                    else:
                        content = ""
                        break
           
            if content:
                # Kelime gruplarını çıkar
                phrases = [line.strip() for line in content.strip().split('\n')
                          if line.strip() and len(line.strip()) > 2 and not line.strip().startswith('#')]
               
                # Temizleme: Numaralandırma, bullet point'ler vs. kaldır
                for phrase in phrases:
                    # Numaralandırma kaldır: "1. kelime grubu" -> "kelime grubu"
                    phrase_clean = re.sub(r'^\d+[\.\)]\s*', '', phrase)
                    # Bullet point kaldır: "- kelime grubu" -> "kelime grubu"
                    phrase_clean = re.sub(r'^[-•*]\s*', '', phrase_clean)
                    phrase_clean = phrase_clean.strip()
                    if phrase_clean and len(phrase_clean) > 2:
                        all_phrases.add(phrase_clean)
               
                print(f"✅ Parça {chunk_idx}: {len(phrases)} phrase bulundu")
            else:
                print(f"⚠️ Parça {chunk_idx}: GPT'den yanıt alınamadı")
       
        # Tüm phrase'ları listeye çevir ve sırala (uzun olanlar önce)
        final_phrases = sorted(list(all_phrases), key=lambda x: (-len(x.split()), -len(x)))
        print(f"✅ GPT toplam {len(final_phrases)} benzersiz linklenebilir phrase tespit etti (tüm metin analiz edildi)")
        if final_phrases:
            print(f"📝 Örnekler: {final_phrases[:10]}")
        return final_phrases
           
    except Exception as e:
        print(f"⚠️ GPT phrase identification hatası: {e}")
        import traceback
        traceback.print_exc()
        return []


def _select_best_urls_batch(keyword_urls_dict, text):
    """Tüm keyword'ler için URL seçimini tek bir GPT çağrısında yap"""
    # Sadece birden fazla URL'si olan ve metinde geçen keyword'leri topla
    keywords_to_process = []
    for keyword_norm, urls in keyword_urls_dict.items():
        if len(urls) > 1:
            keywords_to_process.append((keyword_norm, urls))
   
    if not keywords_to_process:
        return {}
   
    print(f"🤖 GPT ile {len(keywords_to_process)} keyword için toplu URL seçimi yapılıyor... (streaming)")
   
    # Tüm keyword'leri ve URL'lerini formatla
    keyword_url_list = []
    for idx, (keyword_norm, urls) in enumerate(keywords_to_process, 1):
        url_list = "\n".join([f"  {i+1}. {url[1]}" for i, url in enumerate(urls)])
        keyword_url_list.append(f"{idx}. Keyword: '{keyword_norm}'\n   URL'ler:\n{url_list}")
   
    prompt = f"""Aşağıdaki metin için her keyword için en uygun URL'yi seç.

Metin (ilk 2000 karakter):
{text[:2000]}

Keyword'ler ve URL'leri:
{chr(10).join(keyword_url_list)}

GÖREV:
Her keyword için metnin konusu ve içeriğine göre en uygun URL'yi seç.

Format: Her satırda "numara:numara" veya "keyword:numara" formatında yaz.
Örnek:
1:2
2:1
3:3
veya
diyabet:2
kanser:1
tiroid nodulu:3

Sadece seçimleri listele, başka hiçbir şey yazma."""
   
    try:
        # Streaming kullan
        content = _make_openai_request(prompt, temperature=0.1, stream=True).strip()
    except Exception as e:
        print(f"⚠️ Streaming hatası, normal istek deneniyor: {e}")
        # Fallback: Normal istek
        content = _make_openai_request(prompt, temperature=0.1, stream=False).strip()
   
    # GPT yanıtını parse et
    selected_urls = {}
    if content:
        # Keyword mapping oluştur (hem index hem de keyword için)
        keyword_map = {}
        for idx, (keyword_norm, urls) in enumerate(keywords_to_process, 1):
            keyword_map[str(idx)] = (keyword_norm, urls)
            keyword_map[keyword_norm.lower()] = (keyword_norm, urls)
            # Keyword'ün kelimelerini de ekle
            for word in keyword_norm.split():
                if len(word) > 3:
                    keyword_map[word.lower()] = (keyword_norm, urls)
       
        for line in content.split('\n'):
            line = line.strip()
            if ':' in line:
                try:
                    parts = line.split(':', 1)
                    keyword_or_idx = parts[0].strip().lower()
                    num_str = parts[1].strip()
                    num_match = re.search(r'\d+', num_str)
                    if not num_match:
                        continue
                    num = int(num_match.group())
                   
                    # Keyword'ü bul
                    if keyword_or_idx in keyword_map:
                        keyword_norm, urls = keyword_map[keyword_or_idx]
                        if 1 <= num <= len(urls):
                            selected_urls[keyword_norm] = urls[num - 1]
                            print(f"✅ GPT seçti: '{keyword_norm}' -> {urls[num - 1][1]}")
                    else:
                        # Direkt keyword eşleştirmesi dene
                        for keyword_norm, urls in keywords_to_process:
                            if keyword_or_idx in keyword_norm.lower() or keyword_norm.lower() in keyword_or_idx:
                                if 1 <= num <= len(urls):
                                    selected_urls[keyword_norm] = urls[num - 1]
                                    print(f"✅ GPT seçti: '{keyword_norm}' -> {urls[num - 1][1]}")
                                    break
                except:
                    continue
   
    # Seçim yapılamayan keyword'ler için ilk URL'yi kullan
    for keyword_norm, urls in keywords_to_process:
        if keyword_norm not in selected_urls:
            selected_urls[keyword_norm] = urls[0]
            print(f"⚠️ GPT seçim yapamadı, ilk URL kullanılıyor: '{keyword_norm}' -> {urls[0][1]}")
   
    return selected_urls


def _select_best_url_for_keyword(keyword_norm, urls, text):
    """Aynı keyword için birden fazla URL varsa, GPT'ye en uygun olanı seçtir"""
    if len(urls) <= 1:
        return urls[0] if urls else None
   
    # URL'leri formatla
    url_list = "\n".join([f"{i+1}. {url[1]} (keyword: {url[0]})" for i, url in enumerate(urls)])
   
    prompt = f"""Aşağıdaki metin için '{keyword_norm}' keyword'ü ile eşleşen en uygun URL'yi seç.

Metin (ilk 1000 karakter):
{text[:1000]}

Keyword: {keyword_norm}

Mevcut URL'ler:
{url_list}

GÖREV:
Metnin konusu ve içeriğine göre en uygun URL'yi seç. Sadece numarayı yaz (1, 2, 3, vb.).

Cevap:"""
   
    # Retry mekanizması ekle (VPS için)
    max_retries = 3
    timeout_seconds = 60  # VPS için 120 saniye timeout
   
    for attempt in range(1, max_retries + 1):
        try:
            print(f"🤖 GPT URL seçimi yapıyor (Attempt {attempt}/{max_retries}) - Keyword: '{keyword_norm}' (streaming)")
            print(f"⏱️  Timeout: {timeout_seconds} seconds")
           
            try:
                # Streaming kullan
                content = _make_openai_request(prompt, temperature=0.1, stream=True).strip()
            except Exception as e:
                print(f"⚠️ Streaming hatası, normal istek deneniyor: {e}")
                # Fallback: Normal istek
                content = _make_openai_request(prompt, temperature=0.1, stream=False).strip()
           
            if content:
                # Numarayı çıkar
                try:
                    num_match = re.search(r'\d+', content)
                    if not num_match:
                        continue
                    num = int(num_match.group())
                    if 1 <= num <= len(urls):
                        selected_url = urls[num - 1]
                        print(f"✅ GPT seçti: '{selected_url[0]}' -> {selected_url[1]}")
                        return selected_url
                except:
                    pass
           
            # GPT seçim yapamazsa ilk URL'yi kullan
            print(f"⚠️ GPT seçim yapamadı, ilk URL kullanılıyor: {urls[0][1]}")
            return urls[0]
           
        except requests.exceptions.Timeout as e:
            print(f"❌ Timeout error (attempt {attempt}/{max_retries}): {str(e)}")
            if attempt < max_retries:
                wait_time = attempt * 5  # Her denemede bekleme süresini artır (5s, 10s)
                print(f"⏳ Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
                continue
            else:
                print(f"❌ All {max_retries} attempts failed due to timeout, ilk URL kullanılıyor")
                return urls[0]
               
        except requests.exceptions.RequestException as e:
            print(f"❌ Network error with OpenRouter API (attempt {attempt}/{max_retries}): {str(e)}")
            if attempt < max_retries:
                wait_time = attempt * 3
                print(f"⏳ Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
                continue
            else:
                print(f"❌ All {max_retries} attempts failed, ilk URL kullanılıyor")
                return urls[0]
               
        except Exception as e:
            print(f"❌ Unexpected error in _select_best_url_for_keyword (attempt {attempt}/{max_retries}): {str(e)}")
            if attempt < max_retries:
                wait_time = attempt * 2
                print(f"⏳ Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
                continue
            else:
                print(f"❌ All {max_retries} attempts failed, ilk URL kullanılıyor")
                return urls[0]
   
    # Tüm denemeler başarısız olduysa ilk URL'yi kullan
    print(f"⚠️ URL seçim hatası: Tüm denemeler başarısız, ilk URL kullanılıyor")
    return urls[0]


def _validate_links_with_gpt(linked_text, original_text):
    """GPT ile linklerin alakalılığını kontrol et ve alakasız linkleri kaldır - TOPLU"""
    try:
        # Tüm markdown linkleri bul: [text](url)
        link_pattern = r'\[([^\]]+)\]\(([^\)]+)\)'
        links = list(re.finditer(link_pattern, linked_text))
       
        if not links:
            return linked_text
       
        print(f"🔍 GPT ile {len(links)} link toplu kontrol ediliyor... (streaming)")
       
        # Tüm linkleri topla ve context'lerini hazırla
        link_info_list = []
        for idx, match in enumerate(links, 1):
            linked_word = match.group(1)  # Linklenen kelime
            url = match.group(2)  # URL
            start_pos = match.start()
            end_pos = match.end()
           
            # Linkin çevresindeki context'i al (öncesi ve sonrası 200 karakter)
            context_start = max(0, start_pos - 200)
            context_end = min(len(linked_text), end_pos + 200)
            context = linked_text[context_start:context_end]
           
            # URL'den keyword'ü çıkar (domain'den sonraki kısmı)
            url_keyword = url.split('/')[-1] if '/' in url else url
           
            link_info_list.append({
                'index': idx,
                'linked_word': linked_word,
                'url_keyword': url_keyword,
                'context': context,
                'match': match
            })
       
        # Tüm linkleri tek bir prompt'ta GPT'ye sor
        link_descriptions = []
        for info in link_info_list:
            link_descriptions.append(
                f"{info['index']}. Kelime: '{info['linked_word']}' -> Konu: '{info['url_keyword']}'\n"
                f"   Context: {info['context'][:300]}"
            )
       
        prompt = f"""Aşağıdaki metindeki linklerin alakalılığını kontrol et.

TÜM LİNKLER:
{chr(10).join(link_descriptions)}

GÖREV:
Her link için context'e göre alakalı mı değil mi karar ver.

Kurallar:
- "böbrek nakli hastalıkları" cümlesinde "hastalıkları" kelimesi "tiroid nodulu" linkine bağlanmışsa → HAYIR (alakasız)
- "tiroid nodulu belirtileri" cümlesinde "tiroid nodulu" linkine bağlanmışsa → EVET (alakalı)
- "kanser tedavisi" cümlesinde "kanser" kelimesi "kanser tedavisi" linkine bağlanmışsa → EVET (alakalı)
- "sağlık rehberi" cümlesinde "sağlık" kelimesi "tiroid nodulu" linkine bağlanmışsa → HAYIR (alakasız)

Format: Her satırda "numara:EVET" veya "numara:HAYIR" yaz.
Örnek:
1:EVET
2:HAYIR
3:EVET

Sadece sonuçları listele, başka hiçbir şey yazma."""
       
        try:
            # Streaming kullan
            gpt_response = _make_openai_request(prompt, temperature=0.1, stream=True).strip().upper()
        except Exception as e:
            print(f"⚠️ Streaming hatası, normal istek deneniyor: {e}")
            # Fallback: Normal istek
            gpt_response = _make_openai_request(prompt, temperature=0.1, stream=False).strip().upper()
       
        # GPT yanıtını parse et ve alakasız linkleri bul
        links_to_remove = []
        if gpt_response:
            for line in gpt_response.split('\n'):
                line = line.strip()
                if ':' in line:
                    try:
                        parts = line.split(':', 1)
                        idx_match = re.search(r'\d+', parts[0])
                        if not idx_match:
                            continue
                        idx = int(idx_match.group())
                        decision = parts[1].strip()
                       
                        if idx <= len(link_info_list):
                            info = link_info_list[idx - 1]
                            if 'HAYIR' in decision or 'NO' in decision:
                                links_to_remove.append(info['match'])
                                print(f"❌ Alakasız link kaldırıldı: '{info['linked_word']}' -> {info['url_keyword']}")
                    except:
                        continue
       
        # Alakasız linkleri kaldır
        for match in links_to_remove:
            linked_word = match.group(1)
            # Link'i sadece kelimeye çevir (markdown link formatını kaldır)
            linked_text = linked_text.replace(match.group(0), linked_word, 1)
       
        if links_to_remove:
            print(f"✅ {len(links_to_remove)} alakasız link kaldırıldı")
       
        return linked_text
       
    except Exception as e:
        print(f"⚠️ Link validation hatası: {str(e)}")
        # Hata olursa orijinal metni döndür
        return linked_text


def _validate_links_with_gpt_old(linked_text, original_text):
    """GPT ile linklerin alakalılığını kontrol et ve alakasız linkleri kaldır - ESKİ VERSİYON (her link için ayrı çağrı)"""
    try:
        # Tüm markdown linkleri bul: [text](url)
        link_pattern = r'\[([^\]]+)\]\(([^\)]+)\)'
        links = list(re.finditer(link_pattern, linked_text))
       
        if not links:
            return linked_text
       
        print(f"🔍 GPT ile {len(links)} link kontrol ediliyor...")
       
        # Her link için context al ve GPT'e sor
        links_to_remove = []
       
        for match in links:
            linked_word = match.group(1)  # Linklenen kelime
            url = match.group(2)  # URL
            start_pos = match.start()
            end_pos = match.end()
           
            # Linkin çevresindeki context'i al (öncesi ve sonrası 200 karakter)
            context_start = max(0, start_pos - 200)
            context_end = min(len(linked_text), end_pos + 200)
            context = linked_text[context_start:context_end]
           
            # URL'den keyword'ü çıkar (domain'den sonraki kısmı)
            # Örnek: https://www.florence.com.tr/guncel-saglik/tiroid-nodulu -> tiroid-nodulu
            url_keyword = url.split('/')[-1] if '/' in url else url
           
            # GPT'ye sor
            prompt = f"""Aşağıdaki metin parçasında "{linked_word}" kelimesi "{url_keyword}" konulu bir makaleye linklenmiş.

Metin parçası:
{context}

SORU: Bu link bu context'te alakalı ve mantıklı mı?

Örnekler:
- "böbrek nakli hastalıkları" cümlesinde "hastalıkları" kelimesi "tiroid nodulu" linkine bağlanmışsa → HAYIR (alakasız)
- "tiroid nodulu belirtileri" cümlesinde "tiroid nodulu" linkine bağlanmışsa → EVET (alakalı)
- "kanser tedavisi" cümlesinde "kanser" kelimesi "kanser tedavisi" linkine bağlanmışsa → EVET (alakalı)
- "sağlık rehberi" cümlesinde "sağlık" kelimesi "tiroid nodulu" linkine bağlanmışsa → HAYIR (alakasız)

Sadece "EVET" veya "HAYIR" yaz. Başka hiçbir şey yazma."""
           
            try:
                # Streaming kullan
                gpt_response = _make_openai_request(prompt, temperature=0.1, stream=True).strip().upper()
            except Exception as e:
                print(f"⚠️ Streaming hatası, normal istek deneniyor: {e}")
                # Fallback: Normal istek
                gpt_response = _make_openai_request(prompt, temperature=0.1, stream=False).strip().upper()
           
            if gpt_response:
               
                if 'HAYIR' in gpt_response or 'NO' in gpt_response:
                    links_to_remove.append(match)
                    print(f"❌ Alakasız link kaldırıldı: '{linked_word}' -> {url_keyword}")
       
        # Alakasız linkleri kaldır
        for match in links_to_remove:
            linked_word = match.group(1)
            # Link'i sadece kelimeye çevir (markdown link formatını kaldır)
            linked_text = linked_text.replace(match.group(0), linked_word, 1)
       
        if links_to_remove:
            print(f"✅ {len(links_to_remove)} alakasız link kaldırıldı")
       
        return linked_text
       
    except Exception as e:
        print(f"⚠️ Link validation hatası: {str(e)}")
        # Hata olursa orijinal metni döndür
        return linked_text


def linkify_text_with_db(text, domain=None, topic=None):
    """Metni linklerle zenginleştir - domain filtresi ile"""
    linkify_start_time = time.time()
    MAX_TOTAL_TIME = 120  # Toplam linkleme için maksimum 120 saniye
   
    # Domain parametresi zorunlu
    if not domain:
        print(f"⚠️ Domain parameter is required for linkification")
        return text
   
    # Topic kelimelerini normalize et ve linkleme dışında tut
    excluded_keywords = set()
    if topic:
        topic_norm = normalize_turkish(normalize(topic))
        # Topic'ten önemli kelimeleri çıkar (stopword olmayanlar)
        topic_words = [w for w in topic_norm.split() if w not in STOPWORDS and len(w) > 3]
        excluded_keywords.update(topic_words)
        print(f"🚫 Topic kelimeleri linkleme dışında: {topic_words}")
   
    print(f"🔗 Linkifying text with domain filter: {domain}")
   
    articles = get_article_titles_from_db(domain)
    print(f"📊 Database'den {len(articles)} article bulundu (domain: {domain})")
   
    if not articles:
        print(f"⚠️ No articles found for domain: {domain}")
        print(f"💡 Tip: Domain için scraping yapılmamış olabilir. Önce /scrape endpoint'i ile scraping yapın.")
        print(f"💡 Örnek: GET /scrape?url=https://{domain}/guncel-saglik&pagination=url&force=true")
        return text

    original_text = text
    normalized_text = normalize_turkish(normalize(text))

    # İçindekiler bölümünü tespit et ve koruma altına al
    protected_sections = _extract_protected_sections(original_text)
   
    # Markdown başlıklarını tespit et ve koruma altına al
    protected_headings = _extract_markdown_headings(original_text)
   
    # Linklenmiş metinleri (markdown linkleri) tespit et ve koruma altına al
    # Örnek: [text](url) formatındaki linkleri koru
    link_pattern = r'\[([^\]]+)\]\([^\)]+\)'
    link_matches = list(re.finditer(link_pattern, original_text))
    link_replacements = {}
   
    for i, match in enumerate(link_matches):
        placeholder = f"__LINKED_TEXT_{i}__"
        link_replacements[placeholder] = match.group(0)  # Orijinal link formatını sakla
        original_text = original_text.replace(match.group(0), placeholder, 1)
   
    # Korumalı bölümleri geçici olarak değiştir
    temp_text = original_text
    for i, section in enumerate(protected_sections):
        temp_text = temp_text.replace(section, f"__PROTECTED_SECTION_{i}__")
   
    # Markdown başlıklarını geçici olarak değiştir
    heading_replacements = {}
    for i, heading in enumerate(protected_headings):
        placeholder = f"__PROTECTED_HEADING_{i}__"
        heading_replacements[placeholder] = heading
        temp_text = temp_text.replace(heading, placeholder, 1)

    # Aynı keyword için birden fazla URL olabilir - bunları grupla
    keyword_to_urls = {}  # {keyword_norm: [(keyword, url), ...]}
    for article in articles:
        # Keyword None veya boş kontrolü
        keyword = article.get('keyword', '')
        if not keyword or keyword.strip() == '':
            continue
       
        keyword_norm = normalize_turkish(normalize(keyword))
        if not is_stopword_or_short(keyword_norm):
            # Topic kelimelerini hariç tut
            if keyword_norm in excluded_keywords or any(word in excluded_keywords for word in keyword_norm.split()):
                print(f"🚫 Topic kelimesi atlandı: '{keyword}'")
                continue
           
            if keyword_norm not in keyword_to_urls:
                keyword_to_urls[keyword_norm] = []
            keyword_to_urls[keyword_norm].append((keyword, article.get('url', '')))
   
    # Önce metinde hangi keyword'lerin geçtiğini tespit et
    normalized_text = normalize_turkish(normalize(temp_text))
    keywords_in_text = set()
   
    for keyword_norm, urls in keyword_to_urls.items():
        # Keyword'ün metinde geçip geçmediğini kontrol et
        keyword_words = keyword_norm.split()
        # En az bir kelimesi metinde geçiyorsa, keyword metinde var sayılır
        if any(word in normalized_text for word in keyword_words if len(word) > 3):
            keywords_in_text.add(keyword_norm)
   
    print(f"📊 Metinde geçen keyword sayısı: {len(keywords_in_text)} / {len(keyword_to_urls)}")
   
    # Önce metinde geçen ve birden fazla URL'si olan keyword'leri topla
    keywords_needing_selection = {}
    for keyword_norm, urls in keyword_to_urls.items():
        if len(urls) > 1 and keyword_norm in keywords_in_text:
            keywords_needing_selection[keyword_norm] = urls
   
    # Toplu URL seçimi yap (tek GPT çağrısı)
    selected_urls = {}
    if keywords_needing_selection:
        selected_urls = _select_best_urls_batch(keywords_needing_selection, text)
   
    # Tüm keyword'ler için valid_titles listesini oluştur
    valid_titles = []
    for keyword_norm, urls in keyword_to_urls.items():
        if len(urls) == 1:
            # Tek URL varsa direkt ekle
            valid_titles.append((keyword_norm, urls[0][0], urls[0][1]))
        else:
            # Birden fazla URL varsa
            if keyword_norm in keywords_in_text:
                # Metinde geçiyorsa ve seçim yapıldıysa kullan
                if keyword_norm in selected_urls:
                    best_url = selected_urls[keyword_norm]
                    valid_titles.append((keyword_norm, best_url[0], best_url[1]))
                else:
                    # Seçim yapılamadıysa ilk URL'yi kullan
                    valid_titles.append((keyword_norm, urls[0][0], urls[0][1]))
            else:
                # Metinde geçmiyorsa direkt ilk URL'yi kullan (GPT'ye sorma)
                print(f"⚡ Metinde geçmeyen keyword, ilk URL kullanılıyor: '{keyword_norm}'")
                valid_titles.append((keyword_norm, urls[0][0], urls[0][1]))
   
    print(f"✅ Found {len(valid_titles)} valid keywords from {len(articles)} articles")
   
    # Debug: İlk 10 keyword'ü göster
    if valid_titles:
        print(f"📋 Sample keywords: {[kw[1] for kw in valid_titles[:10]]}")
   
    if len(valid_titles) == 0:
        print("⚠️ No valid keywords found for linking")
        print(f"💡 Sebep: {len(articles)} article bulundu ama hiçbiri geçerli keyword içermiyor")
        print(f"💡 Kontrol: Articles'ların keyword alanı dolu mu? Domain doğru mu?")
        return text
   
    # GPT ile metindeki linklenebilir kelime gruplarını tespit et
    # GPT'ye database'deki keyword'leri de ver ki daha akıllı eşleştirme yapsın
    # Timeout koruması: GPT çağrısı çok uzun sürerse atla (normal keyword matching ile devam et)
    gpt_start_time = time.time()
    MAX_GPT_TIME = 30  # GPT phrase tespiti için maksimum 30 saniye (hızlandırıldı)
    identified_phrases = []
   
    # valid_titles kontrolü - GPT çağrısından önce kontrol et
    if not valid_titles or len(valid_titles) == 0:
        print(f"⚠️ valid_titles boş, GPT phrase tespiti atlanıyor")
        identified_phrases = []
    else:
        # Toplam süre kontrolü - zaman kısıtlıysa GPT'yi atla
        elapsed_time = time.time() - linkify_start_time
        if elapsed_time < MAX_TOTAL_TIME - MAX_GPT_TIME:
            try:
                print(f"🤖 GPT phrase tespiti başlatılıyor (max {MAX_GPT_TIME}s)...")
                identified_phrases = _identify_linkable_phrases_with_gpt(text, valid_titles)
                gpt_time = time.time() - gpt_start_time
                if gpt_time > MAX_GPT_TIME:
                    print(f"⚠️ GPT phrase tespiti uzun sürdü ({gpt_time:.1f}s), devam ediliyor...")
            except Exception as e:
                print(f"⚠️ GPT phrase tespiti hatası, normal keyword matching ile devam ediliyor: {e}")
                identified_phrases = []
        else:
            print(f"⏱️ Zaman kısıtlı ({elapsed_time:.1f}s geçti), GPT phrase tespiti atlanıyor, normal keyword matching kullanılıyor")
   
    # Önce uzun keyword'leri (daha spesifik olanlar) önceliklendir
    # Böylece "sağlık rehberi" gibi spesifik keyword'ler "sağlık"tan önce kontrol edilir
    valid_titles.sort(key=lambda x: (-len(x[0].split()), -len(x[0])))  # Önce kelime sayısı, sonra uzunluk

    used_keywords = set()
    used_words = set()  # Linklenmiş kelimeleri takip et (aynı kelime için tek link)
    used_phrases = set()  # GPT'nin tespit ettiği phrase'ları takip et
    matches_found = 0
   
    # GPT ile tespit edilen tamlamaları önceliklendir
    # Önce GPT'nin tespit ettiği tamlamaları kontrol et
    if identified_phrases:
        print(f"🔍 GPT phrases: {identified_phrases[:10]}")
        # GPT phrases'ları normalize et ve keyword'lerle eşleştir
        identified_phrases_normalized = [(normalize_turkish(normalize(phrase)), phrase) for phrase in identified_phrases]
       
        # GPT phrases'ları öncelikli keyword listesine ekle
        prioritized_keywords = []
        for phrase_norm, phrase_orig in identified_phrases_normalized:
            # Bu phrase ile eşleşen keyword'leri bul
            for keyword_norm, keyword_orig, url in valid_titles:
                # Tam eşleşme veya phrase keyword'ün içinde geçiyor mu kontrol et
                if phrase_norm == keyword_norm or phrase_norm in keyword_norm or keyword_norm in phrase_norm:
                    if (keyword_norm, keyword_orig, url) not in prioritized_keywords:
                        prioritized_keywords.append((keyword_norm, keyword_orig, url))
                        used_phrases.add(phrase_norm)  # Bu phrase'ı kullandık
       
        # Öncelikli keyword'leri başa ekle
        remaining_keywords = [k for k in valid_titles if k not in prioritized_keywords]
        valid_titles = prioritized_keywords + remaining_keywords
        print(f"✅ {len(prioritized_keywords)} öncelikli keyword bulundu (GPT phrases)")
   
    # Normalize edilmiş metni bir kez hesapla
    normalized_temp_text = normalize_turkish(normalize(temp_text))
   
    # Debug: Normalize edilmiş metnin ilk 500 karakterini göster
    print(f"📝 Normalized text sample (first 500 chars): {normalized_temp_text[:500]}")
   
    # GPT ile tespit edilen phrase'lar varsa, önce onları linkle
    # Eğer phrase'lar bulunamazsa, phrase içindeki önemli kelimeleri veya normal keyword'leri kullan
    if identified_phrases:
        # GPT phrase'ları ile eşleşen keyword'leri bul
        print(f"🔍 GPT phrase'ları ile eşleşen keyword'ler aranıyor...")
        phrases_to_link = []
        phrase_keywords_used = set()  # Kullanılan keyword'leri takip et
       
        for phrase_orig in identified_phrases:
            # Geçersiz phrase'ları atla
            if not phrase_orig or phrase_orig.strip().startswith('(') or len(phrase_orig.strip()) < 3:
                continue
               
            phrase_norm = normalize_turkish(normalize(phrase_orig))
           
            # Bu phrase ile eşleşen en iyi keyword'ü bul
            best_match = None
            best_score = 0
           
            for keyword_norm, keyword_orig, url in valid_titles:
                # Eşleşme skoru hesapla
                score = 0
                if phrase_norm == keyword_norm:
                    score = 100  # Tam eşleşme
                elif phrase_norm in keyword_norm:
                    score = 80  # Phrase keyword'ün içinde
                elif keyword_norm in phrase_norm:
                    score = 60  # Keyword phrase'ın içinde
                elif len(set(phrase_norm.split()) & set(keyword_norm.split())) > 0:
                    # Ortak kelimeler var
                    common_words = set(phrase_norm.split()) & set(keyword_norm.split())
                    score = len(common_words) * 20
               
                if score > best_score:
                    best_score = score
                    best_match = (keyword_norm, keyword_orig, url, phrase_orig)
           
            if best_match and best_score > 30:  # Minimum eşleşme eşiği
                phrases_to_link.append(best_match)
                phrase_keywords_used.add(best_match[0])  # Keyword'ü kullanıldı olarak işaretle
       
        # GPT phrase'ları ile eşleşen keyword'leri linkle
        sorted_keywords = phrases_to_link
        print(f"✅ {len(sorted_keywords)} GPT phrase için keyword bulundu")
       
        # GPT phrase'larından sonra, phrase içindeki önemli kelimeleri içeren keyword'leri de ekle
        # Ama sadece stopword olmayan ve önemli kelimeler için
        remaining_keywords = []
        phrase_important_words = set()  # GPT phrase'larındaki önemli kelimeler
       
        # Önce GPT phrase'larındaki önemli kelimeleri topla (stopword olmayanlar)
        for phrase_orig in identified_phrases:
            if not phrase_orig or phrase_orig.strip().startswith('(') or len(phrase_orig.strip()) < 3:
                continue
            phrase_norm = normalize_turkish(normalize(phrase_orig))
            phrase_words = phrase_norm.split()
            # Önemli kelimeleri ekle (stopword değil, 4 harften uzun)
            for word in phrase_words:
                word_clean = word.strip()
                if len(word_clean) > 4 and word_clean not in STOPWORDS:
                    phrase_important_words.add(word_clean)
       
        # Bu önemli kelimeleri içeren keyword'leri bul
        # Hem çok kelimeli hem de tek kelime keyword'leri dahil et (ama stopword olmayanlar)
        for keyword_norm, keyword_orig, url in valid_titles:
            if keyword_norm not in phrase_keywords_used:
                keyword_words = set(keyword_norm.split())
               
                # Keyword'de phrase'ın önemli kelimelerinden biri var mı?
                if phrase_important_words & keyword_words:
                    remaining_keywords.append((keyword_norm, keyword_orig, url))
                    phrase_keywords_used.add(keyword_norm)  # Tekrar eklenmesin
       
        if remaining_keywords:
            sorted_keywords = phrases_to_link + remaining_keywords
            print(f"✅ {len(remaining_keywords)} ek keyword eklendi (GPT phrase kelimeleri ile eşleşen: {list(phrase_important_words)[:5]})")
        else:
            sorted_keywords = phrases_to_link
    else:
        # GPT phrase yoksa, normal keyword'leri kullan (uzun olanlar önce)
        if valid_titles and len(valid_titles) > 0:
            single_word_keywords = [(kn, ok, u) for kn, ok, u in valid_titles if len(kn.split()) == 1]
            multi_word_keywords = [(kn, ok, u) for kn, ok, u in valid_titles if len(kn.split()) > 1]
            sorted_keywords = multi_word_keywords + single_word_keywords  # Çok kelimeliler önce
        else:
            sorted_keywords = []
   
    # sorted_keywords kontrolü
    if not sorted_keywords or len(sorted_keywords) == 0:
        print(f"⚠️ sorted_keywords boş, linkleme yapılamıyor")
        matches_found = 0
    else:
        for item in sorted_keywords:
            if len(item) == 4:  # GPT phrase eşleşmesi
                keyword_norm, original_keyword, url, phrase_orig = item
                # GPT phrase'ını metinde ara
                phrase_to_search = phrase_orig
            else:  # Normal keyword
                keyword_norm, original_keyword, url = item
                phrase_to_search = original_keyword
           
            if keyword_norm in used_keywords:
                continue

            # GPT phrase'ını veya keyword'ü normalize et
            phrase_norm = normalize_turkish(normalize(phrase_to_search))
           
            # Debug: İlk 5 keyword için detaylı log
            if len(sorted_keywords) - sorted_keywords.index(item) <= 5:
                print(f"🔍 Debug: Checking keyword '{original_keyword}' (norm: '{keyword_norm}')")
                print(f"   Phrase to search: '{phrase_to_search}' (norm: '{phrase_norm}')")
                print(f"   Normalized text sample (first 200 chars): {normalized_temp_text[:200]}")
           
            # Normalize edilmiş metinde normalize edilmiş phrase/keyword ile arama yap
            # Word boundary kullan ama daha esnek ol (noktalama işaretlerini de dikkate al)
            keyword_pattern = r'\b' + re.escape(phrase_norm) + r'\b'
           
            matched = False
           
            # Debug: İlk 10 keyword için detaylı log
            if len(sorted_keywords) - sorted_keywords.index(item) <= 10:
                print(f"🔍 Searching for keyword: '{original_keyword}' (norm: '{keyword_norm}')")
                print(f"   Pattern: {keyword_pattern}")
                print(f"   Normalized text sample: {normalized_temp_text[:300]}")
           
            # Önce normalize edilmiş metinde kontrol et
            pattern_match_in_normalized = re.search(keyword_pattern, normalized_temp_text, flags=re.IGNORECASE)
           
            # Debug: İlk 5 keyword için
            if len(sorted_keywords) - sorted_keywords.index(item) <= 5:
                print(f"   Pattern match in normalized text: {pattern_match_in_normalized is not None}")
                if pattern_match_in_normalized:
                    print(f"   ✅ Found match: '{pattern_match_in_normalized.group(0)}'")
                else:
                    # Phrase'in kelimelerini tek tek kontrol et
                    phrase_words = phrase_norm.split()
                    for word in phrase_words:
                        word_in_text = word in normalized_temp_text.lower()
                        print(f"   Word '{word}' in text: {word_in_text}")
           
            # Önce tam eşleşme kontrol et
            if pattern_match_in_normalized:
                # Orijinal phrase/keyword'ü normalize et
                original_phrase_norm = normalize_turkish(normalize(phrase_to_search))
               
                # Pattern'leri oluştur - hem orijinal hem normalize edilmiş phrase/keyword ile
                # Orijinal metinde noktalama işaretleri olabilir, bu yüzden daha esnek pattern kullan
                patterns = [
                # Orijinal phrase/keyword - noktalama işaretlerini de dikkate al
                r'(?<![^\W])' + re.escape(phrase_to_search) + r'(?![^\W])',
                # Normalize phrase/keyword - word boundary ile
                r'\b' + re.escape(original_phrase_norm) + r'\b',
                # Orijinal phrase/keyword - basit word boundary
                r'\b' + re.escape(phrase_to_search) + r'\b',
                # Daha esnek: noktalama işaretlerini yok say
                r'(?<![^\W])' + re.escape(re.sub(r'[^\w\s]', '', phrase_to_search)) + r'(?![^\W])',
                ]
               
                # Her iki pattern'i de dene
                for pattern in patterns:
                    # Önce eşleşme var mı kontrol et (link eklemeden)
                    # İÇ İÇE LİNK KONTROLÜ: Zaten linklenmiş metinlerin içinde arama yapma
                    # Markdown link pattern'i: [text](url)
                    link_pattern_check = r'\[([^\]]+)\]\([^\)]+\)'
                   
                    # Eşleşme pozisyonunu kontrol et - eğer bir link içindeyse atla
                    match_result = re.search(pattern, temp_text, flags=re.IGNORECASE)
                    if not match_result:
                        continue  # Eşleşme yoksa, bir sonraki pattern'i dene
                   
                    match_start = match_result.start()
                    match_end = match_result.end()
                   
                    # Bu pozisyonda zaten bir link var mı kontrol et
                    existing_links = list(re.finditer(link_pattern_check, temp_text))
                    is_inside_link = False
                    for link_match in existing_links:
                        link_start = link_match.start()
                        link_end = link_match.end()
                        # Eğer eşleşme bir link içindeyse, atla
                        if match_start >= link_start and match_end <= link_end:
                            is_inside_link = True
                            print(f"⚠️ Skipping '{match_result.group(0)}' - already inside a link")
                            break
                   
                    if is_inside_link:
                        continue
                   
                    matched_text = match_result.group(0)
                    matched_text_norm = normalize_turkish(normalize(matched_text))
                   
                    # STOPWORD KONTROLÜ: Edat, bağlaç, zarf kontrolü
                    matched_words = matched_text_norm.split()
                    if all(word in STOPWORDS for word in matched_words):
                        print(f"⚠️ Skipping '{matched_text}' - all words are stopwords")
                        continue
                   
                    # Eğer bu kelime zaten linklenmişse, atla
                    if matched_text_norm in used_words:
                        continue  # Bu pattern'i atla, diğerine geç
                   
                    # BİRE BİR EŞLEŞME KONTROLÜ: Keyword ile eşleşen metin bire bir aynı olmalı
                    # Çekim eklerini normalize et (iyelik, hal, çoğul ekleri)
                    keyword_without_inflection = remove_turkish_inflection(keyword_norm)
                    matched_text_without_inflection = remove_turkish_inflection(matched_text_norm)
                   
                    # Normalize edilmiş keyword ile normalize edilmiş matched text karşılaştır
                    # Önce çekim ekleri olmadan karşılaştır, sonra normal karşılaştır
                    if keyword_without_inflection != matched_text_without_inflection and keyword_norm != matched_text_norm:
                        # Kısmi eşleşme - sadece tam eşleşme kabul et
                        print(f"⚠️ Skipping '{matched_text}' (norm: '{matched_text_norm}', no-inflection: '{matched_text_without_inflection}') - not exact match with keyword '{original_keyword}' (norm: '{keyword_norm}', no-inflection: '{keyword_without_inflection}')")
                        continue
                    else:
                        # Çekim ekleri normalize edildikten sonra eşleşme var
                        if keyword_without_inflection == matched_text_without_inflection and keyword_norm != matched_text_norm:
                            print(f"✅ Match found (after inflection removal): '{matched_text}' (no-inflection: '{matched_text_without_inflection}') == '{original_keyword}' (no-inflection: '{keyword_without_inflection}')")
                        else:
                            print(f"✅ Exact match found: '{matched_text}' (norm: '{matched_text_norm}') == '{original_keyword}' (norm: '{keyword_norm}')")
                   
                    # Eşleşme var ve kelime daha önce kullanılmamış, link ekle
                    def replacer(match):
                        nonlocal matches_found, matched
                        if not matched and keyword_norm not in used_keywords:
                            matched = True
                            matches_found += 1
                            used_keywords.add(keyword_norm)
                            used_words.add(matched_text_norm)  # Eşleşen metni de kullanıldı olarak işaretle
                            print(f"✅ Link added: '{match.group(0)}' -> {url}")
                        return f'[{match.group(0)}]({url})'
                   
                    temp_text, n = re.subn(pattern, replacer, temp_text, count=1, flags=re.IGNORECASE)
                   
                    if n > 0 and matched:
                        # Normalize edilmiş metni de güncelle
                        normalized_temp_text = normalize_turkish(normalize(temp_text))
                        print(f"✅ Matched phrase/keyword (full): '{phrase_to_search}' -> {url}")
                        break  # Bir eşleşme bulundu, diğer pattern'i denemeye gerek yok
       
        # KISMI EŞLEŞME KALDIRILDI: Sadece bire bir eşleşme kabul ediliyor
        # Eğer tam eşleşme yoksa, phrase içindeki kelimeleri kontrol etme (kaldırıldı)
        if False and not matched and len(item) == 4:  # GPT phrase eşleşmesi - DEVRE DIŞI
            phrase_words = phrase_norm.split()
            # Önemli kelimeleri bul (stopword değil, 3 harften uzun - "leptin" gibi kısa ama önemli kelimeler için)
            important_words = [w for w in phrase_words if len(w) > 3 and w not in STOPWORDS]
           
            # Önce önemli kelimeleri kontrol et
            for word in important_words:
                # Normalize edilmiş metinde kelimeyi bul
                word_pattern = r'\b' + re.escape(word) + r'\b'
               
                if re.search(word_pattern, normalized_temp_text, flags=re.IGNORECASE):
                    # Orijinal phrase'dan bu kelimeyi bul
                    original_word = None
                    for idx, pw in enumerate(phrase_orig.split()):
                        pw_norm = normalize_turkish(normalize(pw))
                        if pw_norm == word:
                            original_word = pw
                            break
                   
                    if not original_word:
                        # Phrase'dan bulamazsa, keyword'den bul
                        keyword_words_list = original_keyword.split()
                        for idx, kw_word in enumerate(keyword_words_list):
                            kw_word_norm = normalize_turkish(normalize(kw_word))
                            if kw_word_norm == word:
                                original_word = kw_word
                                break
                   
                    if not original_word:
                        # Orijinal phrase'daki kelimeleri kontrol et (normalize olmadan)
                        for pw in phrase_orig.split():
                            if normalize_turkish(normalize(pw)) == word:
                                original_word = pw
                                break
                   
                    if not original_word:
                        original_word = word
                   
                    # Aynı kelime daha önce linklenmiş mi kontrol et
                    word_norm = normalize_turkish(normalize(original_word))
                    if word_norm in used_words:
                        continue
                   
                    # Orijinal metinde orijinal kelimeyi bul (hem Türkçe hem İngilizce versiyonlarını dene)
                    patterns_to_try = [
                        r'\b' + re.escape(original_word) + r'\b',  # Orijinal kelime
                        r'\b' + re.escape(word) + r'\b',  # Normalize edilmiş kelime
                    ]
                   
                    # Keyword'deki orijinal kelimeyi de dene
                    if original_keyword and original_keyword != phrase_orig:
                        for kw_word in original_keyword.split():
                            kw_word_norm = normalize_turkish(normalize(kw_word))
                            if kw_word_norm == word:
                                patterns_to_try.append(r'\b' + re.escape(kw_word) + r'\b')
                   
                    for pattern_word in patterns_to_try:
                        if re.search(pattern_word, temp_text, flags=re.IGNORECASE):
                            def replacer_word(match):
                                nonlocal matches_found, matched
                                if word_norm not in used_words and keyword_norm not in used_keywords:
                                    matches_found += 1
                                    used_keywords.add(keyword_norm)
                                    used_words.add(word_norm)
                                    matched = True
                                    print(f"✅ Link added (word match from phrase): '{match.group(0)}' -> {url}")
                                return f'[{match.group(0)}]({url})'
                           
                            temp_text, n = re.subn(pattern_word, replacer_word, temp_text, count=1, flags=re.IGNORECASE)
                            if n > 0 and word_norm in used_words:
                                normalized_temp_text = normalize_turkish(normalize(temp_text))
                                print(f"✅ Matched keyword (word from phrase): '{original_word}' from '{phrase_orig}' -> {url}")
                                matched = True
                                break
                   
                    if matched:
                        break
           
            # KISMI EŞLEŞME KALDIRILDI: Sadece bire bir eşleşme kabul ediliyor
            # Keyword'ün parçalarını kontrol etme (kaldırıldı)
            if False and not matched and len(keyword_norm.split()) > 1:
                # Keyword'ün içindeki önemli kelimeleri kontrol et (stopword olmayanlar)
                keyword_words = keyword_norm.split()
                important_words = [w for w in keyword_words if len(w) > 4 and w not in STOPWORDS]
           
            # Önce önemli kelimeleri kontrol et
            for word in important_words:
                # Normalize edilmiş metinde kelimeyi bul
                word_pattern = r'\b' + re.escape(word) + r'\b'
               
                if re.search(word_pattern, normalized_temp_text, flags=re.IGNORECASE):
                    # Orijinal keyword'den bu kelimeyi bul
                    original_word = None
                    for idx, kw_word in enumerate(keyword_words):
                        if normalize_turkish(normalize(kw_word)) == word:
                            original_word = original_keyword.split()[idx] if idx < len(original_keyword.split()) else kw_word
                            break
                   
                    if not original_word:
                        # Keyword'den bulamazsa, orijinal keyword'ün normalize edilmiş versiyonundan bul
                        for orig_word in original_keyword.split():
                            if normalize_turkish(normalize(orig_word)) == word:
                                original_word = orig_word
                                break
                   
                    if not original_word:
                        original_word = word
                   
                    # Aynı kelime daha önce linklenmiş mi kontrol et
                    word_norm = normalize_turkish(normalize(original_word))
                    if word_norm in used_words:
                        # Bu kelime zaten linklenmiş, atla
                        continue
                   
                    # Orijinal metinde orijinal kelimeyi bul
                    pattern_word = r'\b' + re.escape(original_word) + r'\b'
                   
                    # Orijinal metinde kelime var mı kontrol et
                    if re.search(pattern_word, temp_text, flags=re.IGNORECASE):
                        def replacer_word(match):
                            nonlocal matches_found, matched
                            # Aynı kelime için sadece bir kez link ekle
                            if word_norm not in used_words and keyword_norm not in used_keywords:
                                matches_found += 1
                                used_keywords.add(keyword_norm)
                                used_words.add(word_norm)  # Kelimeyi kullanıldı olarak işaretle
                                matched = True
                                print(f"✅ Link added (word match): '{match.group(0)}' -> {url}")
                            return f'[{match.group(0)}]({url})'
                       
                        temp_text, n = re.subn(pattern_word, replacer_word, temp_text, count=1, flags=re.IGNORECASE)
                        if n > 0:
                            # Eğer link eklendiyse (used_words içinde varsa)
                            if word_norm in used_words:
                                normalized_temp_text = normalize_turkish(normalize(temp_text))
                                print(f"✅ Matched keyword (word match): '{original_word}' from '{original_keyword}' -> {url}")
                                matched = True
                                break
           
            # Eğer hala eşleşme yoksa, keyword'ün ilk kelimesini kontrol et
            # Ama sadece stopword olmayan ve önemli kelimeler için
            if not matched:
                first_word = keyword_norm.split()[0]
                first_word_norm = normalize_turkish(normalize(first_word))
               
                # Stopword kontrolü ve minimum uzunluk
                if first_word_norm not in STOPWORDS and len(first_word_norm) > 4:
                    # İlk kelimeyi bul ve linkle
                    first_word_pattern = r'\b' + re.escape(first_word) + r'\b'
                    if re.search(first_word_pattern, normalized_temp_text, flags=re.IGNORECASE):
                        # Orijinal metinde orijinal keyword'ün ilk kelimesini bul
                        original_first_word = original_keyword.split()[0] if len(original_keyword.split()) > 0 else original_keyword
                        pattern_first = r'\b' + re.escape(original_first_word) + r'\b'
                       
                        # İlk kelime daha önce linklenmiş mi kontrol et
                        if first_word_norm not in used_words:
                            def replacer_first(match):
                                nonlocal matches_found, matched
                                # Aynı kelime için sadece bir kez link ekle
                                if first_word_norm not in used_words and keyword_norm not in used_keywords:
                                    matches_found += 1
                                    used_keywords.add(keyword_norm)
                                    used_words.add(first_word_norm)  # Kelimeyi kullanıldı olarak işaretle
                                    matched = True
                                    print(f"✅ Link added (partial match): '{match.group(0)}' -> {url}")
                                elif first_word_norm in used_words:
                                    # Bu kelime zaten linklenmiş, sadece metni döndür
                                    return match.group(0)
                                return f'[{match.group(0)}]({url})'
                       
                        temp_text, n = re.subn(pattern_first, replacer_first, temp_text, count=1, flags=re.IGNORECASE)
                        if n > 0:
                            # Eğer link eklendiyse (used_words içinde varsa)
                            if first_word_norm in used_words:
                                normalized_temp_text = normalize_turkish(normalize(temp_text))
                                print(f"✅ Matched keyword (partial): '{original_first_word}' from '{original_keyword}' -> {url}")
                                matched = True
   
    # sorted_keywords döngüsü bitti, matches_found zaten tanımlı
    if 'matches_found' not in locals():
        matches_found = 0
   
    print(f"📊 Total links added: {matches_found}")
   
    if matches_found == 0:
        print(f"⚠️ Hiç link eklenmedi! Sebepleri kontrol edin:")
        print(f"   - Valid titles: {len(valid_titles)}")
        print(f"   - Identified phrases: {len(identified_phrases) if identified_phrases else 0}")
        print(f"   - Normalized text length: {len(normalized_temp_text)}")
        print(f"   - Sample keywords: {[kw[1] for kw in valid_titles[:5]] if valid_titles else 'None'}")
   
    # Korumalı bölümleri geri yükle
    final_text = temp_text
    for i, section in enumerate(protected_sections):
        final_text = final_text.replace(f"__PROTECTED_SECTION_{i}__", section)
   
    # Markdown başlıklarını geri yükle
    for placeholder, original_heading in heading_replacements.items():
        final_text = final_text.replace(placeholder, original_heading)
   
    # Linklenmiş metinleri geri yükle
    for placeholder, original_link in link_replacements.items():
        final_text = final_text.replace(placeholder, original_link)
   
    # GPT ile linklerin alakalılığını kontrol et ve alakasız linkleri kaldır
    final_text = _validate_links_with_gpt(final_text, original_text)
   
    print(final_text)
    return final_text


def _extract_markdown_headings(text):
    """Markdown formatındaki başlıkları tespit et ve koruma altına al"""
    protected_headings = []
   
    # Markdown başlık formatları:
    # - # Başlık (H1)
    # - ## Başlık (H2)
    # - ### Başlık (H3)
    # - #### Başlık (H4)
    # - ##### Başlık (H5)
    # - ###### Başlık (H6)
    # - Başlık\n===== (H1 alternatif)
    # - Başlık\n----- (H2 alternatif)
   
    patterns = [
        # # ile başlayan başlıklar (H1-H6) - satır başında olmalı
        # Başlık içeriğindeki tüm karakterleri yakala (satır sonuna kadar)
        r'^(#{1,6})\s+(.+)$',
        # Alternatif format: Başlık altında === veya ---
        r'^(.+?)\n(={3,}|-{3,})$',
    ]
   
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.MULTILINE)
        for match in matches:
            heading_text = match.group(0).strip()
            if heading_text:
                protected_headings.append(heading_text)
   
    # Tekrarları kaldır ve sıralamayı koru (uzun başlıklar önce, çünkü kısa başlıklar uzun başlıkların içinde olabilir)
    # Önce uzunluk sırasına göre sırala (uzun olanlar önce)
    protected_headings.sort(key=len, reverse=True)
   
    seen = set()
    unique_headings = []
    for heading in protected_headings:
        if heading not in seen:
            seen.add(heading)
            unique_headings.append(heading)
   
    return unique_headings


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
    """Unsplash API'den görsel URL'leri çek"""
    try:
        url = "https://api.unsplash.com/search/photos"
        params = {
            "query": query,
            "per_page": count,
            "client_id": UNSPLASH_ACCESS_KEY
        }
       
        print(f"📸 Fetching images from Unsplash for query: '{query}'")
        response = requests.get(url, params=params, timeout=(15, 100))
        response.raise_for_status()
       
        data = response.json()
       
        # API response kontrolü
        if "results" not in data:
            print(f"⚠️ Unsplash API response format error: {list(data.keys())}")
            return []
       
        if len(data.get("results", [])) == 0:
            print(f"⚠️ No images found for query: '{query}'")
            return []
       
        image_urls = []
        for result in data.get("results", []):
            if "urls" in result and "regular" in result["urls"]:
                image_urls.append(result["urls"]["regular"])
       
        print(f"✅ Found {len(image_urls)} images from Unsplash")
        return image_urls
       
    except requests.exceptions.RequestException as e:
        print(f"❌ Unsplash API request error: {str(e)}")
        return []
    except KeyError as e:
        print(f"❌ Unsplash API response format error - missing key: {str(e)}")
        return []
    except Exception as e:
        print(f"❌ Unexpected error in fetch_unsplash_images: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return []


def select_top_3_images(image_urls, query):
    """GPT ile en iyi 3 görseli seç"""
    try:
        # Boş liste kontrolü
        if not image_urls or len(image_urls) == 0:
            print(f"⚠️ No images provided to select_top_3_images")
            return []
       
        # Eğer 3 veya daha az görsel varsa direkt döndür
        if len(image_urls) <= 3:
            print(f"✅ Only {len(image_urls)} images available, returning all")
            return image_urls[:3]
       
        prompt = (
            f"Aşağıda '{query}' konusuyla ilgili {len(image_urls)} görselin URL'leri verilmiştir:\n\n"
            f"{chr(10).join(image_urls)}\n\n"
            f"Lütfen bu listedeki URL'lerden sadece konuyla en alakalı ve en güzel görünen 3 tanesini seç. Medikal ve tıbbi olanları seçmeni istiyorum. "
            f"ve sadece bu 3 URL'yi satır satır olacak şekilde döndür. Başka açıklama yazma."
        )

        # Retry mekanizması - VPS'te timeout sorunlarını önlemek için
        max_retries = 3
        timeout_seconds = 120  # 60'tan 120 saniyeye çıkarıldı (VPS için)
       
        for attempt in range(1, max_retries + 1):
            try:
                print(f"🤖 Asking GPT to select top 3 images from {len(image_urls)} images (Attempt {attempt}/{max_retries})")
                print(f"⏱️  Timeout: {timeout_seconds} seconds")
               
                output = _make_openai_request(prompt, temperature=0.7, stream=True)
                print(f"📝 GPT response received")
               
                # Başarılı yanıt alındı, döngüden çık
                break
               
            except requests.exceptions.Timeout as e:
                print(f"❌ Timeout error (attempt {attempt}/{max_retries}): {str(e)}")
                if attempt < max_retries:
                    wait_time = attempt * 5  # Her denemede bekleme süresini artır (5s, 10s, 15s)
                    print(f"⏳ Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"❌ All {max_retries} attempts failed due to timeout, using fallback")
                    return image_urls[:3]
                   
            except requests.exceptions.RequestException as e:
                error_str = str(e)
                # 503 hatası için daha uzun bekleme
                if "503" in error_str or "overloaded" in error_str.lower():
                    print(f"❌ Model aşırı yüklü (503) (attempt {attempt}/{max_retries})")
                    if attempt < max_retries:
                        wait_time = attempt * 10  # 503 için daha uzun bekleme (10s, 20s, 30s)
                        print(f"⏳ Waiting {wait_time} seconds before retry...")
                        time.sleep(wait_time)
                        continue
                    else:
                        print(f"❌ All {max_retries} attempts failed due to 503, using fallback")
                        return image_urls[:3]
                else:
                    print(f"❌ Network error with OpenAI API (attempt {attempt}/{max_retries}): {str(e)}")
                    if attempt < max_retries:
                        wait_time = attempt * 3
                        print(f"⏳ Waiting {wait_time} seconds before retry...")
                        time.sleep(wait_time)
                        continue
                    else:
                        print(f"❌ All {max_retries} attempts failed, using fallback")
                        return image_urls[:3]
                   
            except Exception as e:
                print(f"❌ Unexpected error in select_top_3_images (attempt {attempt}/{max_retries}): {str(e)}")
                if attempt < max_retries:
                    wait_time = attempt * 2
                    print(f"⏳ Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                    continue
                else:
                    return image_urls[:3]
       
        # Eğer döngüden çıkıldıysa ama output yoksa fallback döndür
        if 'output' not in locals():
            return image_urls[:3]

        # URL'leri çıkar
        urls = [line.strip() for line in output.strip().splitlines() if "http" in line]
       
        # Eğer GPT'den yeterli URL gelmediyse, mevcut URL'lerle eşleştir
        if len(urls) < 3:
            print(f"⚠️ GPT returned only {len(urls)} URLs, trying to match with provided URLs")
            # GPT'nin döndürdüğü URL'lerin ilk kısmını kontrol et
            matched_urls = []
            for url in urls:
                # URL'nin tamamını veya bir kısmını image_urls içinde ara
                for img_url in image_urls:
                    if url in img_url or img_url in url:
                        matched_urls.append(img_url)
                        break
           
            if len(matched_urls) >= 3:
                return matched_urls[:3]
            elif len(matched_urls) > 0:
                # Eksik kalanları ilk listeden ekle
                for img_url in image_urls:
                    if img_url not in matched_urls:
                        matched_urls.append(img_url)
                        if len(matched_urls) >= 3:
                            break
                return matched_urls[:3]
            else:
                # Hiç eşleşme yoksa ilk 3'ü döndür
                print(f"⚠️ No URL matches found, returning first 3 images")
                return image_urls[:3]
       
        return urls[:3]
       
    except Exception as e:
        # Bu catch bloğu retry mekanizması dışındaki beklenmeyen hatalar için
        print(f"❌ Unexpected error in select_top_3_images: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        # Fallback: İlk 3 görseli döndür
        return image_urls[:3] if image_urls else []


# ==================== Content with Images Placement ====================

def place_images_in_content(content, image_urls, main_topic):
    """Place images within content with GPT's help - Linkleri korur"""
   
    if not image_urls or len(image_urls) == 0:
        return content
   
    # ÖNEMLİ: Mevcut text linklerini koru - placeholder'lara çevir
    # Görsel linklerini (![text](url)) korumaya gerek yok, onlar zaten görsel
    import re
    # Sadece text linklerini bul (görsel linklerini hariç tut)
    text_link_pattern = r'(?<!!)\[([^\]]+)\]\([^\)]+\)'  # ! ile başlamayan linkler
    link_matches = list(re.finditer(text_link_pattern, content))
    link_replacements = {}
   
    # Text linklerini placeholder'lara çevir
    temp_content = content
    for i, match in enumerate(link_matches):
        placeholder = f"__TEXT_LINK_{i}__"
        link_replacements[placeholder] = match.group(0)  # Orijinal link formatını sakla
        temp_content = temp_content.replace(match.group(0), placeholder, 1)
   
    prompt = (
        f"Aşağıdaki içeriğe 3 adet resim eklemen gerekiyor. ÖNEMLİ: TÜM METNİ KORU, SADECE GÖRSELLERİ EKLE!\n\n"
        f"İÇERİK (TÜMÜNÜ KORU):\n{temp_content}\n\n"
        f"GÖRSELLER (3 adet - sadece bunları ekle):\n{chr(10).join(image_urls)}\n\n"
        f"GÖREV:\n"
        f"1. İlk görseli içeriğin en başına ekle\n"
        f"2. Diğer iki görselin her birini farklı farklı uygun alt başlıkların hemen üstüne ekle\n"
        f"3. TÜM METNİ OLDUĞU GİBİ KORU - hiçbir metni silme, değiştirme veya kısaltma\n\n"
        f"Görsel formatı: ![kısa alt text](URL)\n\n"
        f"KRİTİK KURALLAR:\n"
        f"- TÜM METNİ KORU - başlıklar, paragraflar, listeler, tablolar, linkler - HEPSİNİ KORU\n"
        f"- Sadece 3 görsel ekle, başka hiçbir şeyi değiştirme\n"
        f"- __TEXT_LINK_X__ placeholder'larını OLDUĞU GİBİ BIRAK - değiştirme, çevirme, silme\n"
        f"- Alt text'ler kısa olmalı (3-5 kelime)\n"
        f"- Mevcut görsel linklerini (![text](url)) de koru\n\n"
        f"ÇIKTI: Orijinal içeriğin TAMAMINI + 3 görseli içeren markdown formatında döndür. Metni kısaltma, değiştirme veya silme!"
    )

    # Retry mekanizması - VPS'te timeout sorunlarını önlemek için
    max_retries = 3
    timeout_seconds = 120  # VPS için 120 saniye timeout
   
    for attempt in range(1, max_retries + 1):
        try:
            print(f"🤖 Adding images to content with GPT (Attempt {attempt}/{max_retries})")
            print(f"⏱️  Timeout: {timeout_seconds} seconds")
           
            result = _make_openai_request(prompt, temperature=0.7, stream=True)
           
            # Text linklerini geri yükle - GPT placeholder'ları değiştirmiş olabilir
            placeholder_found_count = 0
            missing_placeholders = []
           
            for placeholder, original_link in link_replacements.items():
                if placeholder in result:
                    result = result.replace(placeholder, original_link)
                    placeholder_found_count += 1
                else:
                    # Placeholder kaybolmuş - GPT değiştirmiş
                    missing_placeholders.append((placeholder, original_link))
           
            # Kayıp placeholder'ları geri yükle - orijinal içerikten linkleri bul ve ekle
            if missing_placeholders:
                print(f"⚠️ {len(missing_placeholders)} placeholder GPT tarafından değiştirilmiş, orijinal içerikten geri yükleniyor...")
                # Orijinal içerikten linkleri al
                original_links = {}
                for placeholder, original_link in missing_placeholders:
                    # Linklenen kelimeyi bul
                    link_text_match = re.search(r'\[([^\]]+)\]', original_link)
                    if link_text_match:
                        link_word = link_text_match.group(1)
                        original_links[link_word] = original_link
               
                # Result'ta bu kelimeleri bul ve linkleri geri ekle
                for link_word, original_link in original_links.items():
                    # Kelimeyi bul (linklenmemiş halini)
                    # Eğer kelime hala metinde varsa ve linklenmemişse, linki ekle
                    if link_word in result and f"[{link_word}]" not in result:
                        # İlk geçtiği yerde linki ekle
                        result = result.replace(link_word, original_link, 1)
                        print(f"  ✅ Link geri eklendi: {link_word}")
           
            # KRİTİK: Eğer result çok kısaysa (sadece görseller varsa), orijinal içeriği kullan
            # Orijinal içerikteki görselleri result'taki görsellerle değiştir
            if len(result) < len(content) * 0.3:  # Result orijinal içeriğin %30'undan kısaysa
                print(f"⚠️ GPT metni kaybetmiş! (Result: {len(result)} chars, Original: {len(content)} chars)")
                print(f"⚠️ Orijinal içerik kullanılıyor, görseller manuel ekleniyor...")
                # Orijinal içeriği kullan, sadece görselleri ekle
                result = content
                # Görselleri manuel ekle (basit yöntem: ilk görseli başa, diğerlerini başlıklara)
                if image_urls:
                    # İlk görseli başa ekle
                    first_image = f"![{main_topic}]({image_urls[0]})\n\n"
                    result = first_image + result
                   
                    # Diğer görselleri başlıklara ekle (## ile başlayan başlıklar)
                    if len(image_urls) > 1:
                        headings = re.findall(r'^##\s+(.+)$', result, re.MULTILINE)
                        if headings and len(image_urls) > 1:
                            for i, heading in enumerate(headings[:len(image_urls)-1], 1):
                                if i < len(image_urls):
                                    image_markdown = f"![{heading}]({image_urls[i]})\n\n"
                                    result = result.replace(f"## {heading}", f"{image_markdown}## {heading}", 1)
                print(f"✅ Görseller manuel eklendi, orijinal içerik korundu")
           
            print(f"✅ Images placed successfully, {len(link_replacements)} text link korundu ({placeholder_found_count} placeholder, {len(missing_placeholders)} manuel geri yüklendi)")
            return result
           
        except requests.exceptions.Timeout as e:
            print(f"❌ Timeout error (attempt {attempt}/{max_retries}): {str(e)}")
            if attempt < max_retries:
                wait_time = attempt * 5
                print(f"⏳ Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
                continue
            else:
                print(f"❌ All {max_retries} attempts failed due to timeout")
                raise
               
        except requests.exceptions.RequestException as e:
            error_str = str(e)
            # 503 hatası için daha uzun bekleme
            if "503" in error_str or "overloaded" in error_str.lower():
                print(f"❌ Model aşırı yüklü (503) (attempt {attempt}/{max_retries})")
                if attempt < max_retries:
                    wait_time = attempt * 10  # 503 için daha uzun bekleme (10s, 20s, 30s)
                    print(f"⏳ Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"❌ All {max_retries} attempts failed due to 503")
                    raise
            else:
                print(f"❌ Network error with Gemini API (attempt {attempt}/{max_retries}): {str(e)}")
                if attempt < max_retries:
                    wait_time = attempt * 3
                    print(f"⏳ Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"❌ All {max_retries} attempts failed")
                    raise
               
        except Exception as e:
            print(f"❌ Unexpected error (attempt {attempt}/{max_retries}): {str(e)}")
            if attempt < max_retries:
                wait_time = attempt * 2
                print(f"⏳ Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
                continue
            else:
                raise


# ==================== Part 2: Similar Titles Functions ====================

def _normalize_query_for_search(query):
    """Query'yi Google araması için optimize et"""
    # Alt çizgileri boşluklara çevir
    normalized = query.replace('_', ' ').replace('-', ' ')
   
    # Birden fazla boşluğu tek boşluğa indir
    normalized = ' '.join(normalized.split())
   
    # Başlangıç ve bitiş boşluklarını temizle
    normalized = normalized.strip()
   
    return normalized

def fetch_google_results(query):
    print("\n" + "=" * 70)
    print(f"🔍 SEARCHING GOOGLE FOR: {query}")
    print("📍 Location: Istanbul, Turkey")
    print("=" * 70)

    # Query'yi normalize et (alt çizgileri boşluklara çevir)
    normalized_query = _normalize_query_for_search(query)
    if normalized_query != query:
        print(f"📝 Query normalized: '{query}' -> '{normalized_query}'")

    params = {
        "engine": "google",
        "q": normalized_query,  # Normalize edilmiş query kullan
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
       
        # SerpAPI'nin yeni versiyonunda as_dict(), eski versiyonunda get_dict() kullanılıyor
        # Her ikisini de destekleyelim
        if hasattr(search, 'as_dict'):
            results = search.as_dict()
        elif hasattr(search, 'get_dict'):
            results = search.get_dict()
        else:
            # Direkt dictionary döndürüyor olabilir
            results = search if isinstance(search, dict) else {}
       
        urls = []

        # SerpAPI hatalarını kontrol et
        if "error" in results:
            error_msg = results.get("error", "Unknown error")
            print(f"\n❌ SERPAPI ERROR: {error_msg}")
           
            # Eğer "Google hasn't returned any results" hatası varsa, query'yi daha genişletilmiş şekilde tekrar dene
            if "hasn't returned any results" in error_msg.lower():
                print(f"\n🔄 Trying alternative query format...")
               
                # Daha genel bir query oluştur - sadece anahtar kelimeleri al
                words = normalized_query.split()
                if len(words) > 3:
                    # İlk 3-4 kelimeyi al
                    alternative_query = ' '.join(words[:4])
                    print(f"📝 Alternative query: '{alternative_query}'")
                   
                    # Yeni query ile tekrar dene
                    params["q"] = alternative_query
                    try:
                        search_alt = GoogleSearch(params)
                        if hasattr(search_alt, 'as_dict'):
                            results_alt = search_alt.as_dict()
                        elif hasattr(search_alt, 'get_dict'):
                            results_alt = search_alt.get_dict()
                        else:
                            results_alt = search_alt if isinstance(search_alt, dict) else {}
                       
                        if "error" not in results_alt and "organic_results" in results_alt and len(results_alt.get("organic_results", [])) > 0:
                            print(f"✅ Alternative query worked! Found {len(results_alt.get('organic_results', []))} results")
                            results = results_alt
                            normalized_query = alternative_query
                        else:
                            print(f"❌ Alternative query also failed")
                            return []
                    except Exception as e:
                        print(f"❌ Alternative query error: {e}")
                        return []
                else:
                    print(f"❌ Query too short for alternative search")
                    return []
            else:
                print(f"Full error details: {results}")
                return []

        if "organic_results" in results and len(results.get("organic_results", [])) > 0:
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
            print(f"Query: {query}")
            print(f"Response keys: {list(results.keys())}")
            if "error" in results:
                print(f"Error message: {results['error']}")

        return urls

    except Exception as e:
        print(f"\n❌ ERROR in Google search: {str(e)}")
        print(f"Exception type: {type(e).__name__}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
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


def ask_gpt_similar_titles(texts, query, subheading_count, language="turkish"):
    if USE_GPT_MOCK:
        print("\n⚙️ MOCK MODE ACTIVE")
        return "\n".join([f"Başlık {i + 1}" for i in range(subheading_count)])

    print("\n" + "=" * 70)
    print(f"🤖 GENERATING TITLES WITH GPT FOR: {query}")
    print(f"📊 Requested number of titles: {subheading_count}")
    print(f"🌐 Language: {language}")
    print("=" * 70)

    # Language mapping
    language_map = {
        "turkish": "TÜRKÇE",
        "english": "İNGİLİZCE",
        "spanish": "İSPANYOLCA",
        "tr": "TÜRKÇE",
        "en": "İNGİLİZCE",
        "es": "İSPANYOLCA",
        "esp": "İSPANYOLCA"
    }
    language_name = language_map.get(language.lower(), language.upper())

    prompt = f"""
Konu: {query}

Aşağıda verilen sayfalardan alınan içeriklere göre, yalnızca '{query}' konusuna odaklanarak {subheading_count} adet alt başlık öner.

ÖNEMLİ DİL KURALI:
- Başlıkları MUTLAKA {language_name} dilinde ver.
- {language_name} dilinin dilbilgisi kurallarına uygun olmalı.

BAŞLIK FORMATI KURALLARI:
- Başlıklardaki kelimeler büyük harfle başlayacak (Title Case)
- "Sıkça Sorulan Sorular" veya benzeri genel başlıklar VERME

Bu başlıklar:
- Konuyla doğrudan ilgili olmalı
- Birbirinden farklı açıları ele almalı
- SEO dostu olmalı
- {language_name} dilinin dilbilgisi kurallarına uygun olmalı
- Okuyucunun merakını çekecek şekilde olmalı

Sadece başlıkları sırasız ve liste halinde ver. Açıklama ekleme. Başka hiçbir şey yazma, sadece başlıkları listele.
"""

    for i, text in enumerate(texts[:10], 1):  # Limit to first 10 texts
        prompt += f"\n---\nSayfa {i}:\n{text[:2000]}\n"  # Limit each text to 1000 chars

    # Retry mekanizması - VPS'te timeout sorunlarını önlemek için
    max_retries = 3
    timeout_seconds = 120  # 60'tan 120 saniyeye çıkarıldı (VPS için)
   
    for attempt in range(1, max_retries + 1):
        try:
            print(f"\n📤 Sending request to OpenAI API... (Attempt {attempt}/{max_retries})")
            print(f"⏱️  Timeout: {timeout_seconds} seconds")
           
            content = _make_openai_request(prompt, temperature=0.7, stream=True)
           
            if not content or not content.strip():
                print("❌ Empty content received from OpenAI API")
                if attempt < max_retries:
                    print(f"🔄 Retrying... ({attempt + 1}/{max_retries})")
                    time.sleep(2)  # 2 saniye bekle
                    continue
                return None

            print("\n📝 RAW GPT RESPONSE:")
            print("-" * 50)
            print(content)
            print("-" * 50)

            return content

        except requests.exceptions.Timeout as e:
            print(f"❌ Timeout error (attempt {attempt}/{max_retries}): {str(e)}")
            if attempt < max_retries:
                wait_time = attempt * 5  # Her denemede bekleme süresini artır (5s, 10s, 15s)
                print(f"⏳ Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
                continue
            else:
                print(f"❌ All {max_retries} attempts failed due to timeout")
                return None
               
        except requests.exceptions.RequestException as e:
            error_str = str(e)
            # 503 hatası için daha uzun bekleme
            if "503" in error_str or "overloaded" in error_str.lower():
                print(f"❌ Model aşırı yüklü (503) (attempt {attempt}/{max_retries})")
                if attempt < max_retries:
                    wait_time = attempt * 10  # 503 için daha uzun bekleme (10s, 20s, 30s)
                    print(f"⏳ Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"❌ All {max_retries} attempts failed due to 503")
                    return None
            else:
                print(f"❌ Network error with Gemini API (attempt {attempt}/{max_retries}): {str(e)}")
                if attempt < max_retries:
                    wait_time = attempt * 3
                    print(f"⏳ Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"❌ All {max_retries} attempts failed")
                    return None
               
        except Exception as e:
            print(f"❌ Unexpected error in ask_gpt_similar_titles (attempt {attempt}/{max_retries}): {str(e)}")
            if attempt < max_retries:
                wait_time = attempt * 2
                print(f"⏳ Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
                continue
            else:
                return None
   
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

        response = requests.get(url, headers=headers, timeout=(15, 100), verify=True)
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
            domain = data.get('domain', None)  # Domain parametresi
        else:
            user_text = request.form.get('text', '')
            main_topic = request.form.get('topic', '')
            domain = request.form.get('domain', None)  # Domain parametresi

        if not user_text:
            return jsonify({"error": "Missing 'text' field"}), 400

        if not main_topic:
            # If topic is not specified, guess from first sentence or part of content
            main_topic = user_text.split('.')[0] if '.' in user_text else user_text[:50]

        # Process the content
        try:
            # 1. Add links to text (sadece domain varsa)
            if domain:
                app.logger.info(f"Step 1: Adding links to text with domain: {domain}")
                print(f"🔗 Linkleme başlatılıyor - Domain: {domain}, Topic: {main_topic}")
                linked_text = linkify_text_with_db(user_text, domain=domain, topic=main_topic)
               
                # Linkleme kontrolü - eğer hiç link eklenmemişse uyarı ver
                import re
                # Sadece text linklerini say (görsel linklerini hariç tut: ![text](url) değil, [text](url))
                # Görsel linkleri: ![ ile başlayanlar
                text_link_pattern = r'(?<!\!)\[([^\]]+)\]\([^\)]+\)'  # ! ile başlamayan linkler
                link_count = len(re.findall(text_link_pattern, linked_text))
                original_link_count = len(re.findall(text_link_pattern, user_text))
                new_links = link_count - original_link_count
               
                if new_links == 0:
                    print(f"⚠️ Linkleme yapıldı ama yeni link eklenmedi! (Toplam link: {link_count}, Orijinal: {original_link_count})")
                    app.logger.warning(f"No new links added during linkification. Total links: {link_count}, Original: {original_link_count}")
                else:
                    print(f"✅ {new_links} yeni link eklendi (Toplam: {link_count})")
                    app.logger.info(f"Successfully added {new_links} new links (Total: {link_count})")
            else:
                app.logger.warning("Domain parameter missing, skipping linkification")
                print("⚠️ Domain parametresi eksik, linkleme atlanıyor")
                linked_text = user_text

            # 2. Translate main topic
            app.logger.info("Step 2: Translating topic")
            translated_topic = translate_to_english(main_topic)
            app.logger.info(f"Translated topic: {translated_topic}")

            # 3. Fetch images
            app.logger.info("Step 3: Fetching images")
            all_images = fetch_unsplash_images(translated_topic)
            app.logger.info(f"Found {len(all_images)} images")
           
            if not all_images or len(all_images) == 0:
                app.logger.warning("No images found, proceeding without images")
                # Resim olmadan da devam et
                return jsonify({
                    "content_with_images": linked_text,
                    "processing_time_seconds": time.time() - start_time,
                    "warning": "No images found for the given topic" + ("; Domain parameter missing, linkification skipped" if not domain else "")
                })

            # 4. Select best images
            app.logger.info("Step 4: Selecting best images")
            top_images = select_top_3_images(all_images, main_topic)
            app.logger.info(f"Selected {len(top_images)} top images")
           
            if not top_images or len(top_images) == 0:
                app.logger.warning("No images selected, proceeding without images")
                # Resim olmadan da devam et
                return jsonify({
                    "content_with_images": linked_text,
                    "processing_time_seconds": time.time() - start_time,
                    "warning": "Could not select images" + ("; Domain parameter missing, linkification skipped" if not domain else "")
                })

            # 5. Place images in content
            app.logger.info("Step 5: Placing images in content")
            final_content = place_images_in_content(linked_text, top_images, main_topic)

            response_data = {
                "content_with_images": final_content,
                "processing_time_seconds": time.time() - start_time
            }
           
            if not domain:
                response_data["warning"] = "Domain parameter missing, linkification skipped"
           
            return jsonify(response_data)

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
    """
    Embedding tabanlı ML linkleme endpoint'i
    
    Request Body (POST):
    {
        "text": "Metin içeriği...",
        "domain": "www.florence.com.tr",
        "topic": "Ana konu (opsiyonel)"
    }
    
    Query Parameters (GET):
    - text: Metin içeriği
    - domain: Domain adı
    - topic: Ana konu (opsiyonel)
    
    Not: similarity_threshold sabit 0.5 olarak kullanılır.
    """
    start_time = time.time()
    
    # Embedding sistemi kontrolü - modül yüklenemezse hata döner
    # Model yükleme hatası linkify_with_embeddings içinde yakalanacak
    if not EMBEDDING_AVAILABLE:
        return jsonify({
            "error": "Embedding-based linkleme sistemi kullanılamıyor.",
            "message": "linkify_embedding.py modülü yüklenemedi",
            "note": "Modül import edilemedi. Dosyanın mevcut olduğundan ve gerekli paketlerin yüklü olduğundan emin olun."
        }), 503
    
    try:
        # Get parameters
        if request.is_json:
            data = request.get_json()
            user_text = data.get('text', '')
            domain = data.get('domain', None)
            topic = data.get('topic', None)
        else:
            user_text = request.form.get('text', '') or request.args.get('text', '')
            domain = request.form.get('domain', None) or request.args.get('domain', None)
            topic = request.form.get('topic', None) or request.args.get('topic', None)
        
        # Validation
        if not user_text:
            return jsonify({"error": "Missing 'text' field"}), 400
        
        if not domain:
            return jsonify({
                "error": "Missing 'domain' field",
                "message": "Domain is required for embedding-based linkification"
            }), 400
        
        # Topic'i belirle (verilmemişse metinden çıkar)
        if not topic:
            topic = user_text.split('.')[0] if '.' in user_text else user_text[:50]
        
        # Similarity threshold sabit 0.5
        similarity_threshold = 0.5
        
        # Process with embedding-based linkification
        app.logger.info(f"Embedding linkification started - Domain: {domain}, Topic: {topic}, Threshold: {similarity_threshold}")
        print(f"🔗 Embedding linkleme başlatılıyor - Domain: {domain}, Topic: {topic}, Threshold: {similarity_threshold}")
        
        try:
            linked_text = linkify_with_embeddings(
                text=user_text,
                domain=domain,
                topic=topic,
                similarity_threshold=similarity_threshold
            )
        except Exception as e:
            error_msg = str(e)
            # Model yükleme hatası kontrolü
            if "model" in error_msg.lower() or "embedding" in error_msg.lower() or "SentenceTransformer" in error_msg:
                return jsonify({
                    "error": "Embedding model yüklenemedi",
                    "message": error_msg,
                    "note": "Model yüklemek için: python train_health_embedding.py (fine-tuned) veya ilk kullanımda base model otomatik indirilir (internet gerekli). Supabase'de keyword embedding'leri varsa, sadece text phrase embedding'leri için model gerekli."
                }), 503
            else:
                # Diğer hatalar
                return jsonify({
                    "error": "Linkleme işlemi başarısız oldu",
                    "message": error_msg
                }), 500
        
        processing_time = time.time() - start_time
        
        # Count links added
        text_link_pattern = r'(?<!\!)\[([^\]]+)\]\([^\)]+\)'
        link_count = len(re.findall(text_link_pattern, linked_text))
        original_link_count = len(re.findall(text_link_pattern, user_text))
        new_links = link_count - original_link_count
        
        app.logger.info(f"Embedding linkification completed - {new_links} new links added in {processing_time:.2f}s")
        print(f"✅ Embedding linkleme tamamlandı - {new_links} yeni link eklendi ({processing_time:.2f}s)")
        
        return jsonify({
            "linked_text": linked_text,
            "processing_time_seconds": round(processing_time, 2),
            "domain": domain,
            "topic": topic,
            "similarity_threshold": similarity_threshold,
            "links_added": new_links,
            "total_links": link_count,
            "method": "embedding-based"
        })
        
    except Exception as e:
        app.logger.error(f"Error in embedding linkification: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": "Internal server error",
            "message": str(e),
            "processing_time_seconds": round(time.time() - start_time, 2)
        }), 500


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

        # Query'den anlamlı alt text oluştur
        alt_text = query.replace('_', ' ').replace('-', ' ').title()
        return jsonify({
            "selected_image_tags": [f'![{alt_text}]({url})' for url in top_images],
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
        pagination_type = request.args.get("pagination", "auto").lower()  # auto, button, url
        start_page = request.args.get("start_page", type=int, default=1)
        end_page = request.args.get("end_page", type=int, default=None)
       
        if not url:
            return jsonify({"error": "URL parameter is required"}), 400
       
        # URL'yi temizle
        clean_url = url.replace('https://https://', 'https://')
        if not clean_url.startswith(('http://', 'https://')):
            clean_url = 'https://' + clean_url
       
        print(f"🚀 Scraping başlatılıyor: {clean_url}")
        print(f"📋 Pagination tipi: {pagination_type}")
        if pagination_type == "url":
            print(f"📄 Sayfa aralığı: {start_page} - {end_page if end_page else 'sonsuz'}")
       
        # Async fonksiyonu çalıştır
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
       
        try:
            scraper = SeleniumScraper()
           
            # Pagination tipine göre scraping yöntemi seç
            if pagination_type == "auto":
                # Otomatik tespit yap
                print("🤖 Otomatik pagination tespiti yapılıyor...")
                detected_type = scraper.detect_pagination_type(clean_url)
                print(f"✅ Tespit edilen pagination tipi: {detected_type}")
                pagination_type = detected_type  # Tespit edilen tipi kullan
           
            if pagination_type == "url":
                # URL-based pagination (Florence Nightingale gibi ?page=8)
                print("🔗 URL-based pagination kullanılıyor")
                result = loop.run_until_complete(
                    scraper.pagination_url_scrape(
                        clean_url,
                        start_page=start_page,
                        end_page=end_page,
                        generate_keywords=True,
                        force=force
                    )
                )
            elif pagination_type == "infinite":
                # Infinite scroll scraping (henüz implement edilmedi, button-based kullan)
                print("♾️ Infinite scroll tespit edildi, ancak henüz desteklenmiyor. Button-based kullanılıyor.")
                result = loop.run_until_complete(scraper.next_button_scrape(clean_url, generate_keywords=True))
            elif force:
                # Force parametresi varsa domain kontrolünü atla
                print("🔄 Force mode: Domain kontrolü atlanıyor")
                result = loop.run_until_complete(scraper._force_scrape(clean_url, generate_keywords=True))
            else:
                # Default: Next button pagination
                print("🔘 Next button pagination kullanılıyor")
                result = loop.run_until_complete(scraper.next_button_scrape(clean_url, generate_keywords=True))
           
            if result and result.get('success', False):
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
                        "pages_scraped": result.get('pages_scraped', 0),
                        "total_blog_posts": result.get('total_blog_posts', 0),
                        "articles_saved": result.get('articles_saved', 0),
                        "keywords_updated": result.get('keywords_updated', 0),
                        "blog_links": result.get('blog_links', [])[:10],  # İlk 10 link
                        "cached": result.get('cached', False)
                    }
                })
            else:
                error_msg = result.get('error', 'Bilinmeyen hata') if result else 'Scraping sonucu None döndü'
                app.logger.error(f"Scraping failed: {error_msg}")
                return jsonify({
                    "success": False,
                    "message": f"Scraping hatası: {error_msg}",
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
@app.route("/similar-titles", methods=["POST"])
def get_similar_titles():
    try:
        # Get data from request body (JSON) or form data
        if request.is_json:
            data = request.get_json()
            query = data.get("query")
            word_count = data.get("word_count", 2000)
            language = data.get("language", "turkish")
        else:
            query = request.form.get("query")
            word_count = request.form.get("word_count", default=2000, type=int)
            language = request.form.get("language", default="turkish", type=str)
       
        # Validate query parameter
        if not query:
            return jsonify({"error": "Query parameter is required"}), 400

        # Ensure query is properly encoded string
        try:
            query = str(query).encode('utf-8', errors='ignore').decode('utf-8')
        except Exception as e:
            return jsonify({"error": "Invalid query parameter encoding"}), 400

        # Validate word_count
        try:
            word_count = int(word_count)
            if word_count < 0:
                return jsonify({"error": "Word count must be a positive number"}), 400
        except (ValueError, TypeError):
            return jsonify({"error": "Word count must be a valid number"}), 400

        # Validate and set language (default: turkish)
        if not language:
            language = "turkish"

        app.logger.info(f"Processing query: {query}")
        app.logger.info(f"Target word count: {word_count}")
        app.logger.info(f"Language: {language}")

        # Fetch URLs with error handling
        try:
            urls = fetch_google_results(query)
            if not urls:
                app.logger.warning(f"No search results found for query: {query}")
                return jsonify({
                    "error": "No relevant search results found",
                    "message": f"Google search for '{query}' returned no results. This could be due to: 1) Invalid query, 2) SerpAPI error, 3) No matching content found.",
                    "query": query
                }), 404
            app.logger.info(f"Found {len(urls)} URLs to process")
        except Exception as e:
            app.logger.error(f"Error fetching Google results: {str(e)}")
            import traceback
            app.logger.error(f"Traceback: {traceback.format_exc()}")
            return jsonify({
                "error": "Failed to fetch search results",
                "message": f"An error occurred while searching Google: {str(e)}",
                "query": query
            }), 500

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
            result = ask_gpt_similar_titles(raw_texts, query, subheading_count, language=language)
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


@app.route("/test-openai")
def test_openai():
    try:
        result = _make_openai_request("Say 'Hello World'", temperature=0.7, stream=False)
       
        return jsonify({
            "status": "success",
            "response": result
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
   
    # Logger seviyesini ayarla (DEBUG, INFO, WARNING, ERROR)
    log_level = logging.DEBUG if not is_production else logging.INFO
    app.logger.setLevel(log_level)

    # Add console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)  # Handler seviyesini de ayarla
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
