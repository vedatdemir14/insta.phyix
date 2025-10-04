# --- Windows asyncio policy fix (must be at the very top) ---
import sys, asyncio
if sys.platform.startswith("win"):
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    except Exception:
        pass

# -------------------------------------------------------------
import io
import re
import json
import time
import requests
import pandas as pd
import hashlib
import uuid
from datetime import datetime
from apify_client import ApifyClient

# Supabase import
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False

# PostgreSQL import for direct connection
try:
    import psycopg2
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False


class InstagramBackend:
    """
    Backend class for Instagram scraping and data processing operations
    Handles all business logic, database operations, and external API calls
    
    UNIPILE CONFIGURATION:
    =====================
    config = {
        'UNIPILE_API_KEY': 'k8IpFvnp.1H5f5alAgW2gK5M+J4GvW2M1lavbPHdsZfUGXBbEF+U=',
        'UNIPILE_BASE_URL': 'https://api21.unipile.com:15121',
        # Other configurations...
    }
    
    USAGE EXAMPLE:
    ==============
    # 1. Connect Instagram account
    success, message, account_id = backend.connect_instagram_account(
        username="your_instagram_username",
        password="your_instagram_password"
    )
    
    # 2. Get target leads
    target_leads = backend.get_all_historical_leads()
    
    # 3. Create message campaign
    campaign_results = backend.create_message_campaign(
        campaign_name="My Campaign",
        target_leads=target_leads,
        message_template="Merhaba [first name]! 👋",
        delay_seconds=10,
        max_messages_per_hour=10
    )
    """
    
    def __init__(self, config=None):
        """
        Initialize backend with configuration
        
        Args:
            config (dict): Configuration containing API keys and database settings
        """
        import os
        from dotenv import load_dotenv
        
        # Load environment variables
        load_dotenv()
        
        # Use environment variables if config not provided
        if config is None:
            config = {
                'SUPABASE_URL': os.getenv('SUPABASE_URL'),
                'SUPABASE_KEY': os.getenv('SUPABASE_KEY'),
                'APIFY_API_TOKEN': os.getenv('APIFY_API_TOKEN'),
                'UNIPILE_API_KEY': os.getenv('UNIPILE_API_KEY', 'k8IpFvnp.1H5f5alAgW2gK5M+J4GvW2M1lavbPHdsZfUGXBbEF+U='),
                'UNIPILE_BASE_URL': os.getenv('UNIPILE_BASE_URL', 'https://api21.unipile.com:15121'),
                'POSTGRES_HOST': os.getenv('POSTGRES_HOST'),
                'POSTGRES_PORT': os.getenv('POSTGRES_PORT', '5432'),
                'POSTGRES_DB': os.getenv('POSTGRES_DB'),
                'POSTGRES_USER': os.getenv('POSTGRES_USER'),
                'POSTGRES_PASSWORD': os.getenv('POSTGRES_PASSWORD')
            }
        
        self.config = config
        self.supabase = None
        self.postgres_conn = None
        self.supabase_connected = False
        self.postgres_connected = False
        
        # Initialize database connections
        self._setup_database_connections()
    
    def _setup_database_connections(self):
        """Setup database connections (Supabase and PostgreSQL)"""
        # Try Supabase connection first
        if SUPABASE_AVAILABLE and self.config.get('SUPABASE_URL') and self.config.get('SUPABASE_API_KEY'):
            try:
                self.supabase = create_client(
                    self.config['SUPABASE_URL'], 
                    self.config['SUPABASE_API_KEY']
                )
                # Test connection
                self.supabase.table("scraping_sessions").select("id").limit(1).execute()
                self.supabase_connected = True
                print("✅ Supabase connected successfully")
            except Exception as e:
                print(f"⚠️ Supabase connection failed: {e}")
                self.supabase_connected = False
        
        # Try PostgreSQL connection (optional - Supabase is primary)
        if POSTGRES_AVAILABLE and self.config.get('POSTGRES_CONNECTION_STRING'):
            try:
                # Try direct connection without additional parameters
                conn_string = self.config['POSTGRES_CONNECTION_STRING']
                self.postgres_conn = psycopg2.connect(conn_string)
                self.postgres_connected = True
                print("✅ PostgreSQL connected successfully")
            except Exception as e:
                print(f"⚠️ PostgreSQL connection failed: {e}")
                print("ℹ️ Using Supabase only (PostgreSQL is optional)")
                self.postgres_connected = False
    
    # =========================================================
    # Database Operations
    # =========================================================
    
    def save_to_database(self, table_name, data):
        """Save data to database (Supabase or PostgreSQL)"""
        if not (self.supabase_connected or self.postgres_connected):
            return False, "No database connection available"
        
        try:
            if self.supabase and self.supabase_connected:
                result = self.supabase.table(table_name).insert(data).execute()
                return True, f"Saved {len(data)} records to Supabase"
            
            elif self.postgres_conn and self.postgres_connected:
                cursor = self.postgres_conn.cursor()
                
                # Get column names from first record
                if data:
                    columns = list(data[0].keys())
                    placeholders = ', '.join(['%s'] * len(columns))
                    query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
                    
                    # Insert each record
                    for record in data:
                        values = [record.get(col) for col in columns]
                        cursor.execute(query, values)
                    
                    self.postgres_conn.commit()
                    cursor.close()
                    return True, f"Saved {len(data)} records to PostgreSQL"
            
            return False, "No valid database connection"
            
        except Exception as e:
            return False, f"Database save error: {str(e)}"
    
    def load_from_database(self, table_name, limit=10):
        """Load data from database"""
        if not (self.supabase_connected or self.postgres_connected):
            return []
        
        try:
            if self.supabase and self.supabase_connected:
                result = self.supabase.table(table_name).select("*").order("created_at", desc=True).limit(limit).execute()
                return result.data if result.data else []
            
            elif self.postgres_conn and self.postgres_connected:
                cursor = self.postgres_conn.cursor()
                cursor.execute(f"SELECT * FROM {table_name} ORDER BY created_at DESC LIMIT {limit}")
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                cursor.close()
                return [dict(zip(columns, row)) for row in rows]
            
            return []
            
        except Exception as e:
            print(f"Database load error: {str(e)}")
            return []
    
    def save_scraping_session(self, locations, usernames_count, method):
        """Save scraping session to database"""
        session_data = [{
            "session_id": f"session_{int(time.time())}",
            "locations": json.dumps(locations),
            "usernames_count": usernames_count,
            "method": method,
            "created_at": datetime.now().isoformat()
        }]
        
        return self.save_to_database("scraping_sessions", session_data)
    
    def save_profiles_batch(self, profiles_df, session_id=None):
        """Save profiles batch to database"""
        if profiles_df.empty:
            return False, "No profiles to save"
        
        try:
            profiles_data = []
            for _, row in profiles_df.iterrows():
                profile_record = {
                    "session_id": session_id or f"session_{int(time.time())}",
                    "username": row.get("username", ""),
                    "full_name": row.get("full_name", ""),
                    "biography": row.get("biography", ""),
                    "followers_count": int(row.get("followers_count", 0)),
                    "following_count": int(row.get("following_count", 0)),
                    "posts_count": int(row.get("posts_count", 0)),
                    "is_verified": bool(row.get("is_verified", False)),
                    "is_private": bool(row.get("is_private", False)),
                    "profile_pic_url": row.get("profilePicUrl", row.get("profile_pic_url", row.get("profilePictureUrl", row.get("profilePic", row.get("avatar", row.get("photo", "")))))),
                    "created_at": datetime.now().isoformat()
                }
                profiles_data.append(profile_record)
            
            # Insert in batches
            batch_size = 1000
            total_saved = 0
            
            for i in range(0, len(profiles_data), batch_size):
                batch = profiles_data[i:i + batch_size]
                success, message = self.save_to_database("instagram_profiles", batch)
                if success:
                    total_saved += len(batch)
                else:
                    return False, f"Error in profile batch {i//batch_size + 1}: {message}"
            
            return True, f"Saved {total_saved} profiles to database"
            
        except Exception as e:
            return False, f"Error preparing profiles data: {str(e)}"
    
    def save_nationality_results(self, classified_df, session_id=None):
        """Save nationality classification results"""
        if classified_df.empty:
            return False, "No classification results to save"
        
        try:
            nationality_data = []
            for _, row in classified_df.iterrows():
                nationality_record = {
                    "session_id": session_id or f"session_{int(time.time())}",
                    "username": row.get("Username", ""),
                    "full_name": row.get("Full Name", ""),
                    "nationality": row.get("Nationality", ""),
                    "detection_date": row.get("Detection_Date", datetime.now().isoformat()),
                    "followers_count": int(row.get("Followers Count", 0)),
                    "created_at": datetime.now().isoformat()
                }
                nationality_data.append(nationality_record)
            
            # Insert in batches
            batch_size = 1000
            total_saved = 0
            
            for i in range(0, len(nationality_data), batch_size):
                batch = nationality_data[i:i + batch_size]
                success, message = self.save_to_database("nationality_classifications", batch)
                if success:
                    total_saved += len(batch)
                else:
                    return False, f"Error in nationality batch {i//batch_size + 1}: {message}"
            
            return True, f"Saved {total_saved} nationality classifications to database"
            
        except Exception as e:
            return False, f"Error preparing nationality data: {str(e)}"
    
    # =========================================================
    # 2FA Helper Functions
    # =========================================================
    
    def detect_2fa_page(self, driver):
        """Detect if Instagram 2FA page is loaded"""
        try:
            # Common 2FA page indicators
            indicators = [
                "//input[@name='security_code']",
                "//input[@placeholder*='code']",
                "//input[@placeholder*='Code']",
                "//button[contains(text(), 'Send')]",
                "//button[contains(text(), 'Resend')]",
                "//div[contains(text(), 'security code')]",
                "//div[contains(text(), 'verification code')]"
            ]
            
            for indicator in indicators:
                try:
                    element = driver.find_element("xpath", indicator)
                    if element:
                        return True, element
                except:
                    continue
                    
            return False, None
            
        except Exception as e:
            return False, None
    
    def click_send_sms_button(self, driver):
        """Click the 'Send SMS' button on 2FA page"""
        try:
            # Common SMS button selectors
            sms_selectors = [
                "//button[contains(text(), 'Send')]",
                "//button[contains(text(), 'Resend')]",
                "//button[contains(@class, 'send')]",
                "//a[contains(text(), 'Send')]"
            ]
            
            for selector in sms_selectors:
                try:
                    button = driver.find_element("xpath", selector)
                    if button and button.is_displayed():
                        button.click()
                        return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            return False
    
    def handle_2fa_verification(self, driver, ig_user):
        """Handle 2FA verification process"""
        try:
            # Detect 2FA page
            is_2fa, element = self.detect_2fa_page(driver)
            
            if not is_2fa:
                return "NOT_2FA"
            
            # Try to click send SMS button
            sms_sent = self.click_send_sms_button(driver)
            
            if sms_sent:
                return "SMS_SENT"
            else:
                return "SMS_FAILED"
                
        except Exception as e:
            return f"2FA_ERROR: {str(e)}"
    
    # =========================================================
    # Scraping Functions
    # =========================================================
    
    def selenium_location_scraper(self, ig_user, ig_pass, location_urls, max_profiles=200):
        """
        More robust Selenium-based scraper with better page detection and multiple fallback strategies
        """
        try:
            from selenium import webdriver
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.chrome.options import Options
            from selenium.common.exceptions import TimeoutException, NoSuchElementException
            import time
        except ImportError:
            raise Exception("Selenium not installed. Run: pip install selenium")
        
        chrome_options = Options()
        chrome_options.add_argument("--headless")        
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        driver = None
        try:
            driver = webdriver.Chrome(options=chrome_options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Login with better error handling
            driver.get("https://www.instagram.com/accounts/login/")
            
            try:
                # Wait for login form
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.NAME, "username"))
                )
                
                # Fill credentials
                username_field = driver.find_element(By.NAME, "username")
                password_field = driver.find_element(By.NAME, "password")
                
                username_field.clear()
                username_field.send_keys(ig_user)
                time.sleep(1)
                
                password_field.clear()
                password_field.send_keys(ig_pass)
                time.sleep(1)
                
                # Submit login
                login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
                login_button.click()
                
                time.sleep(10)
                
                # Check if login was successful
                current_url = driver.current_url
                if "challenge" in current_url or "checkpoint" in current_url:
                    # Handle 2FA
                    result = self.handle_2fa_verification(driver, ig_user)
                    if result == "SMS_SENT":
                        return "2FA_REQUIRED"
                    elif result == "SMS_FAILED":
                        return []
                    else:
                        return result
                elif "login" in current_url:
                    raise Exception("Login failed - check credentials")
                
            except TimeoutException:
                raise Exception("Login form not found - Instagram may have changed")
            
            # Handle post-login modals
            modal_selectors = [
                "//button[contains(text(), 'Not Now')]",
                "//button[contains(text(), 'Şimdi Değil')]",
                "//button[contains(text(), 'Later')]",
                "//button[contains(text(), 'Daha Sonra')]",
                "//div[@role='button'][contains(text(), 'Not Now')]"
            ]
            
            for selector in modal_selectors:
                try:
                    button = WebDriverWait(driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    button.click()
                    time.sleep(2)
                    break
                except:
                    continue
            
            all_usernames = []
            
            for url_idx, url in enumerate(location_urls):
                try:
                    driver.get(url)
                    time.sleep(8)  # Wait longer for page load
                    
                    # Check what page we actually got
                    page_source = driver.page_source.lower()
                    current_url = driver.current_url
                    
                    # Detect different page states
                    if "login" in current_url:
                        raise Exception("Redirected to login - session expired")
                    elif "sorry, this page isn't available" in page_source or "page not found" in page_source:
                        print(f"Location page not found: {url}")
                        continue
                    elif "location" not in current_url and "explore" not in current_url:
                        print(f"Unexpected page redirect: {current_url}")
                        continue
                    
                    # Try multiple selectors to find content
                    content_selectors = [
                        "article",
                        "[role='main']",
                        "main",
                        "section",
                        "[data-testid]",
                        "div[style*='grid']",
                        "a[href*='/p/']",  # Direct post links
                        "a[href*='/reel/']"  # Reel links
                    ]
                    
                    content_found = False
                    for selector in content_selectors:
                        try:
                            elements = driver.find_elements(By.CSS_SELECTOR, selector)
                            if elements:
                                content_found = True
                                break
                        except:
                            continue
                    
                    if not content_found:
                        print(f"No recognizable content structure found")
                        continue
                    
                    # Extract usernames with multiple strategies
                    usernames = set()
                    
                    # Strategy 1: Find all links and extract usernames
                    all_links = driver.find_elements(By.CSS_SELECTOR, "a[href]")
                    
                    for link in all_links:
                        try:
                            href = link.get_attribute("href")
                            if not href:
                                continue
                            
                            # Extract username from various URL patterns
                            if "/p/" in href or "/reel/" in href:
                                # These are post/reel links, extract username from URL structure
                                parts = href.split('/')
                                for i, part in enumerate(parts):
                                    if part in ['p', 'reel'] and i > 0:
                                        potential_username = parts[i - 1]
                                        if potential_username and len(potential_username) > 0 and not potential_username.startswith('www'):
                                            usernames.add(potential_username)
                                            break
                            elif href.count('/') == 4 and href.endswith('/'):
                                # Direct profile links like https://instagram.com/username/
                                username = href.rstrip('/').split('/')[-1]
                                if username and len(username) > 0 and not any(skip in username for skip in ['explore', 'accounts', 'p', 'reel']):
                                    usernames.add(username)
                            
                        except Exception as e:
                            continue
                    
                    # Strategy 2: Scroll and collect more
                    if len(usernames) < max_profiles:
                        scroll_attempts = 0
                        last_count = len(usernames)
                        stall_count = 0
                        
                        while len(usernames) < max_profiles and scroll_attempts < 20:
                            # Scroll down
                            driver.execute_script("window.scrollBy(0, window.innerHeight);")
                            time.sleep(7)
                            scroll_attempts += 1
                            
                            # Find new links after scroll
                            new_links = driver.find_elements(By.CSS_SELECTOR, "a[href]")
                            
                            for link in new_links:
                                try:
                                    href = link.get_attribute("href")
                                    if not href:
                                        continue
                                    
                                    # Same extraction logic as above
                                    if "/p/" in href or "/reel/" in href:
                                        parts = href.split('/')
                                        for i, part in enumerate(parts):
                                            if part in ['p', 'reel'] and i > 0:
                                                potential_username = parts[i - 1]
                                                if potential_username and len(potential_username) > 0 and not potential_username.startswith('www'):
                                                    usernames.add(potential_username)
                                                    break
                                    elif href.count('/') == 4 and href.endswith('/'):
                                        username = href.rstrip('/').split('/')[-1]
                                        if username and len(username) > 0 and not any(skip in username for skip in ['explore', 'accounts', 'p', 'reel']):
                                            usernames.add(username)
                                    
                                except:
                                    continue
                            
                            # Check progress
                            if len(usernames) == last_count:
                                stall_count += 1
                                if stall_count >= 3:
                                    break
                            else:
                                stall_count = 0
                                last_count = len(usernames)
                    
                    location_usernames = list(usernames)
                    all_usernames.extend(location_usernames)
                    
                except Exception as e:
                    print(f"Error processing location {url}: {e}")
                    continue
            
            # Cleanup and return results
            driver.quit()
            
            # Deduplicate final results
            unique_usernames = list(set(all_usernames))
            
            # yasaklı alt dizgiler (gerekirse genişletin: "shop", "store", "official" vs.)
            banned_substrings = ["blog"]
            
            # final filtre
            ig_lc = ig_user.strip().lower() if ig_user else None
            
            def is_allowed(u: str) -> bool:
                u_lc = u.strip().lower()
                if ig_lc and u_lc == ig_lc:
                    return False
                if any(bad in u_lc for bad in banned_substrings):
                    return False
                return True
            
            unique_usernames = [u for u in unique_usernames if is_allowed(u)]
            
            if unique_usernames:
                return [f"https://www.instagram.com/{u}/" for u in unique_usernames]
            else:
                return []
            
        except Exception as e:
            if driver:
                driver.quit()
            raise Exception(f"Critical error: {e}")
    
    def apify_profile_scraper(self, usernames, max_profiles=100):
        """
        Apify-based profile scraper using the working version from original backup
        """
        try:
            client = ApifyClient(self.config['APIFY_API_TOKEN'])
            
            # Try multiple actors in order of preference
            actors_to_try = [
                {
                    "id": "apify/instagram-scraper",
                    "input": {
                        "directUrls": [f"https://www.instagram.com/{username}/" for username in usernames[:max_profiles]],
                        "resultsType": "details",
                        "resultsLimit": max_profiles,
                        "addParentData": False
                    }
                },
                {
                    "id": "apify/instagram-scraper",
                    "input": {
                        "usernames": usernames[:max_profiles],
                        "resultsType": "details",
                        "resultsLimit": max_profiles
                    }
                },
                {
                    "id": "apify/instagram-scraper",
                    "input": {
                        "usernames": usernames[:max_profiles],
                        "resultsType": "posts",
                        "resultsLimit": max_profiles
                    }
                },
                {
                    "id": "dSCLg0C3YEZ83HzYX",  # Original working actor
                    "input": {"usernames": usernames[:max_profiles]}
                }
            ]
            
            results = []
            for actor_config in actors_to_try:
                try:
                    print(f"DEBUG - Trying actor: {actor_config['id']}")
                    run = client.actor(actor_config['id']).call(run_input=actor_config['input'])
                    
                    # Get results
                    actor_results = []
                    for item in client.dataset(run["defaultDatasetId"]).iterate_items():
                        # Debug: Print first item to see structure
                        if len(actor_results) == 0:
                            print("DEBUG - First Apify item structure:")
                            print(json.dumps(item, indent=2))
                            print("DEBUG - Available keys:", list(item.keys()) if isinstance(item, dict) else "Not a dict")
                        
                        # Check for error items
                        if isinstance(item, dict) and item.get("error") == "no_items":
                            print(f"DEBUG - Actor {actor_config['id']} returned no_items error, trying next actor...")
                            break
                        
                        actor_results.append(item)
                    
                    if actor_results and not any(item.get("error") == "no_items" for item in actor_results if isinstance(item, dict)):
                        print(f"DEBUG - Successfully got {len(actor_results)} results from {actor_config['id']}")
                        return actor_results
                    else:
                        print(f"DEBUG - No valid results from {actor_config['id']}, trying next actor...")
                        continue
                        
                except Exception as e:
                    print(f"DEBUG - Actor {actor_config['id']} failed: {str(e)}")
                    continue
            
            # If all actors failed
            print("DEBUG - All actors failed, returning empty results")
            return []
            
        except Exception as e:
            raise Exception(f"Apify scraper error: {str(e)}")
    
    # =========================================================
    # Nationality Classification
    # =========================================================
    
    def classify_nationality_openrouter(self, df, api_key, model="openai/gpt-4o-mini",
                                      batch_size=20, sleep_s=3.0, max_retries=3, debug=True, return_logs=True):
        """
        Nationality classification using OpenRouter API
        """
        if df.empty:
            empty = pd.DataFrame({"Nationality": [], "Count": [], "Percentage": []})
            return (df.copy(), empty, pd.DataFrame([])) if return_logs else (df.copy(), empty)
        
        work = df.copy()
        for col in ["Nationality", "Detection_Date"]:
            if col not in work.columns:
                work[col] = ""
        
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        
        def build_payload(batch_profiles):
            """Build a clean prompt for nationality detection"""
            user_lines = []
            for i, (username, fullname) in enumerate(batch_profiles, 1):
                # Clean the inputs
                clean_username = str(username).strip() if username else ""
                clean_fullname = str(fullname).strip() if fullname else ""
                user_lines.append(f"{i}. {clean_username} - {clean_fullname}")
            
            prompt = """Aşağıdaki Instagram profillerinin milliyet tahmini yap.
            Tahmini yaparken öncelikle username fullname ve biography bilgilerinden ismini bulmaya çalış.
             Ondan sonra milliyet tahmini yap. Biography ingilizce olunca kişi yabancı olmak zorunda değildir.
            Sadece bu iki format kullan:
            - TÜRK (Türk isimleri için)
            - YABANCI - [ülke adı] (yabancı isimler için)
            yabancıların ülkelerini belirtemezsen sadece YABANCI yaz.
            çıktı olarak YABANCI-[ülke adı] şekline çıktı istemiyorum. Ülkesini bulamazsan sadece YABANCI yaz.
            örnek:
            YABANCI - RUSYA
            YABANCI - ALMANYA
            uygun olmayan çıktı örneği:
            YABANCI - [ülke adı ]
            

            Her profil için sırasıyla 1'den başlayarak cevap ver."""
            
            messages = [
                {
                    "role": "system",
                    "content": "Sen bir milliyet tahmin uzmanısın. Sadece verilen formatta cevap ver."
                },
                {
                    "role": "user",
                    "content": prompt + "\n\n" + "\n".join(user_lines)
                }
            ]
            
            return {
                "model": model,
                "messages": messages,
                "temperature": 0.1,
                "max_tokens": 1000
            }
        
        def make_api_call(payload, retry_count=0):
            """Make API call with retry logic"""
            try:
                response = requests.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    if retry_count < max_retries:
                        time.sleep(sleep_s * (retry_count + 1))
                        return make_api_call(payload, retry_count + 1)
                    else:
                        raise Exception(f"API call failed: {response.status_code} - {response.text}")
                        
            except Exception as e:
                if retry_count < max_retries:
                    time.sleep(sleep_s * (retry_count + 1))
                    return make_api_call(payload, retry_count + 1)
                else:
                    raise e
        
        # Process in batches
        all_results = []
        logs = []
        
        for i in range(0, len(work), batch_size):
            batch = work.iloc[i:i + batch_size]
            batch_profiles = list(zip(batch['username'], batch['full_name']))
            
            if debug:
                print(f"Processing batch {i//batch_size + 1}/{(len(work) + batch_size - 1)//batch_size}")
            
            try:
                payload = build_payload(batch_profiles)
                response = make_api_call(payload)
                
                if response and 'choices' in response:
                    content = response['choices'][0]['message']['content']
                    
                    # Parse the response
                    lines = content.strip().split('\n')
                    batch_results = []
                    
                    for j, line in enumerate(lines):
                        if j < len(batch_profiles):
                            username, fullname = batch_profiles[j]
                            
                            # Extract nationality from line
                            nationality = "UNKNOWN"
                            if "TÜRK" in line.upper():
                                nationality = "TÜRK"
                            elif "YABANCI" in line.upper():
                                # Try to extract country
                                parts = line.split("-")
                                if len(parts) > 1:
                                    country = parts[1].strip()
                                    nationality = f"YABANCI - {country}"
                                else:
                                    nationality = "YABANCI"
                            
                            batch_results.append({
                                'username': username,
                                'full_name': fullname,
                                'Nationality': nationality,
                                'Detection_Date': datetime.now().isoformat()
                            })
                    
                    all_results.extend(batch_results)
                    
                    if debug:
                        print(f"Batch {i//batch_size + 1} completed: {len(batch_results)} profiles classified")
                    
                    logs.append({
                        'batch': i//batch_size + 1,
                        'profiles': len(batch_results),
                        'status': 'success'
                    })
                    
                else:
                    raise Exception("Invalid API response")
                    
            except Exception as e:
                error_msg = f"Batch {i//batch_size + 1} failed: {str(e)}"
                print(error_msg)
                logs.append({
                    'batch': i//batch_size + 1,
                    'profiles': len(batch_profiles),
                    'status': 'error',
                    'error': str(e)
                })
                
                # Add unknown results for failed batch
                for username, fullname in batch_profiles:
                    all_results.append({
                        'username': username,
                        'full_name': fullname,
                        'Nationality': "UNKNOWN",
                        'Detection_Date': datetime.now().isoformat()
                    })
            
            # Sleep between batches
            if i + batch_size < len(work):
                time.sleep(sleep_s)
        
        # Create results DataFrame
        results_df = pd.DataFrame(all_results)
        
        # Create summary
        nationality_counts = results_df['Nationality'].value_counts()
        summary_df = pd.DataFrame({
            'Nationality': nationality_counts.index,
            'Count': nationality_counts.values,
            'Percentage': (nationality_counts.values / len(results_df) * 100).round(2)
        })
        
        # Update work DataFrame with results
        for _, row in results_df.iterrows():
            mask = work['username'] == row['username']
            work.loc[mask, 'Nationality'] = row['Nationality']
            work.loc[mask, 'Detection_Date'] = row['Detection_Date']
        
        if return_logs:
            logs_df = pd.DataFrame(logs)
            return work, summary_df, logs_df
        else:
            return work, summary_df
    
    def batch_nationality_classification(self, profiles_df, model, batch_size, sleep_s):
        """
        Batch nationality classification wrapper
        """
        try:
            # Prepare data for classification
            classification_data = []
            for _, row in profiles_df.iterrows():
                classification_data.append({
                    'username': row.get('username', ''),
                    'full_name': row.get('full_name', ''),
                    'followers_count': row.get('followers_count', 0)
                })
            
            # Convert to DataFrame
            df = pd.DataFrame(classification_data)
            
            # Run classification
            result_df, summary_df, logs_df = self.classify_nationality_openrouter(
                df, 
                self.config['OPENROUTER_API_KEY'], 
                model, 
                batch_size, 
                sleep_s
            )
            
            return result_df
            
        except Exception as e:
            raise Exception(f"Batch classification error: {str(e)}")
    
    # =========================================================
    # Utility Functions
    # =========================================================
    
    def parse_usernames_from_text(self, content):
        """Parse usernames from text content"""
        usernames = []
        lines = content.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Extract username from various formats
            if '@' in line:
                # Extract from @username format
                username = line.split('@')[-1].split()[0]
                if username:
                    usernames.append(username)
            elif 'instagram.com/' in line:
                # Extract from URL
                parts = line.split('instagram.com/')[-1].split('/')[0]
                if parts and parts != 'p' and parts != 'explore':
                    usernames.append(parts)
            else:
                # Assume it's a direct username
                username = line.split()[0]
                if username and not username.startswith('http'):
                    usernames.append(username)
        
        return list(set(usernames))  # Remove duplicates
    
    def build_summary(self, df):
        """Build summary statistics from DataFrame"""
        if df.empty:
            return {}
        
        summary = {
            'total_profiles': len(df),
            'verified_count': df.get('is_verified', pd.Series()).sum() if 'is_verified' in df.columns else 0,
            'private_count': df.get('is_private', pd.Series()).sum() if 'is_private' in df.columns else 0,
            'avg_followers': df.get('followers_count', pd.Series()).mean() if 'followers_count' in df.columns else 0,
            'avg_following': df.get('following_count', pd.Series()).mean() if 'following_count' in df.columns else 0,
            'avg_posts': df.get('posts_count', pd.Series()).mean() if 'posts_count' in df.columns else 0
        }
        
        return summary
    
    def get_database_stats(self):
        """Get database statistics"""
        if not (self.supabase_connected or self.postgres_connected):
            return {}
        
        try:
            stats = {}
            
            # Get session count
            sessions = self.load_from_database("scraping_sessions", 1)
            stats['total_sessions'] = len(sessions)
            
            # Get profiles count
            profiles = self.load_from_database("instagram_profiles", 1)
            stats['total_profiles'] = len(profiles)
            
            # Get classifications count
            classifications = self.load_from_database("nationality_classifications", 1)
            stats['total_classifications'] = len(classifications)
            
            return stats
            
        except Exception as e:
            print(f"Error getting database stats: {e}")
            return {}
    
    def personalize_message(self, template_content, recipient_data):
        """
        Personalize message template with recipient data
        
        Args:
            template_content (str): Message template with placeholders
            recipient_data (dict): Recipient information containing username, full_name, etc.
        
        Returns:
            str: Personalized message
        """
        try:
            personalized = template_content
            
            # Get recipient info
            username = recipient_data.get("username", "")
            full_name = recipient_data.get("full_name", username)
            
            # Extract first name from full name
            first_name = full_name.split()[0] if full_name else username
            
            # Replace parameters
            personalized = personalized.replace("[full name]", full_name)
            personalized = personalized.replace("[first name]", first_name)
            personalized = personalized.replace("[username]", username)
            
            return personalized
            
        except Exception as e:
            print(f"Error personalizing message: {e}")
            return template_content
    
    def get_personalized_messages_for_leads(self, template_content, leads_list):
        """
        Generate personalized messages for multiple leads
        
        Args:
            template_content (str): Message template
            leads_list (list): List of lead dictionaries
        
        Returns:
            list: List of dictionaries with account info and personalized message
        """
        try:
            personalized_messages = []
            
            for lead in leads_list:
                personalized_message = self.personalize_message(template_content, lead)
                
                personalized_messages.append({
                    "username": lead.get("username", ""),
                    "full_name": lead.get("full_name", ""),
                    "nationality": lead.get("nationality", "Unknown"),
                    "session_name": lead.get("session_name", "Unknown"),
                    "original_message": template_content,
                    "personalized_message": personalized_message
                })
            
            return personalized_messages
            
        except Exception as e:
            print(f"Error generating personalized messages: {e}")
            return []
    
    # ===============================================
    # POPUP HANDLING UTILITIES
    # ===============================================
    
    def _handle_notification_popups(self, driver):
        """Handle various notification popups that may appear"""
        try:
            # Common notification popup selectors
            popup_selectors = [
                # "Turn on notifications" popup
                "//button[contains(text(), 'Not Now')]",
                "//button[contains(text(), 'Şimdi Değil')]",
                "//button[contains(text(), 'Later')]",
                "//button[contains(text(), 'Daha Sonra')]",
                "//button[contains(text(), 'Cancel')]",
                "//button[contains(text(), 'İptal')]",
                "//button[contains(text(), 'Close')]",
                "//button[contains(text(), 'Kapat')]",
                "//button[contains(text(), 'Skip')]",
                "//button[contains(text(), 'Atla')]",
                "//button[contains(text(), 'No Thanks')]",
                "//button[contains(text(), 'Hayır Teşekkürler')]",
                "//button[contains(text(), 'Don\'t Allow')]",
                "//button[contains(text(), 'İzin Verme')]",
                "//button[contains(text(), 'Not Now')]",
                "//button[contains(text(), 'Şimdi Değil')]",
                # X button selectors
                "//button[@aria-label='Close']",
                "//button[@aria-label='Kapat']",
                "//button[contains(@class, 'close')]",
                "//button[contains(@class, 'dismiss')]",
                "//div[@role='button' and contains(@aria-label, 'Close')]",
                "//div[@role='button' and contains(@aria-label, 'Kapat')]",
                # Modal close buttons
                "//div[contains(@class, 'modal')]//button[contains(text(), '×')]",
                "//div[contains(@class, 'modal')]//button[contains(text(), '✕')]",
                "//div[contains(@class, 'modal')]//button[contains(@class, 'close')]",
                # Instagram specific selectors
                "//div[contains(@class, 'x1i10hfl') and contains(@class, 'x1a2a7pz')]//button",
                "//div[contains(@class, 'x1i10hfl')]//button[contains(text(), 'Not Now')]",
                "//div[contains(@class, 'x1i10hfl')]//button[contains(text(), 'Şimdi Değil')]"
            ]
            
            popup_closed = False
            for selector in popup_selectors:
                try:
                    popup_button = WebDriverWait(driver, 2).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    popup_button.click()
                    time.sleep(1)
                    print(f"✅ Popup closed (selector: {selector})")
                    popup_closed = True
                    break
                except TimeoutException:
                    continue
            
            if not popup_closed:
                # Try pressing Escape key as alternative
                try:
                    from selenium.webdriver.common.keys import Keys
                    driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                    time.sleep(1)
                    print("✅ Popup closed via Escape key")
                except:
                    pass
                    
        except Exception as e:
            print(f"⚠️ Error handling popups: {str(e)}")
    
    # ===============================================
    # SELENIUM INSTAGRAM MESSAGE SENDER
    # ===============================================
    
    def send_single_instagram_message(self, target_username, message_template, username, password):
        """
        Send a single Instagram message using Selenium
        
        Args:
            target_username (str): Target Instagram username
            message_template (str): Message template
            username (str): Instagram login username
            password (str): Instagram login password
        
        Returns:
            dict: Results with success/failure status
        """
        return self.send_selenium_instagram_messages([target_username], message_template, username, password, delay_seconds=5)
    
    def send_selenium_instagram_messages(self, usernames, message_template, username, password, delay_seconds=10):
        """
        Send Instagram messages using Selenium automation with OTP login
        
        Args:
            usernames (list): List of Instagram usernames
            message_template (str): Message template
            username (str): Instagram username for login
            password (str): Instagram password for login
            delay_seconds (int): Delay between messages
        
        Returns:
            dict: Results with success/failure details
        """
        try:
            from selenium import webdriver
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.chrome.options import Options
            from selenium.common.exceptions import TimeoutException, NoSuchElementException
            import time
            import random
        except ImportError:
            return {
                'success': False,
                'error': 'Selenium not installed. Run: pip install selenium',
                'results': []
            }
        
        driver = None
        results = {
            'total_targets': len(usernames),
            'successful_sends': 0,
            'failed_sends': 0,
            'success_details': [],
            'failure_details': []
        }
        
        try:
            # Setup Chrome options
            chrome_options = Options()
            chrome_options.add_argument("--headless")        
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Run in background (minimized window)
            chrome_options.add_argument("--start-minimized")
            chrome_options.add_argument("--window-size=1024,768")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-plugins")
            chrome_options.add_argument("--disable-images")
            chrome_options.add_argument("--disable-javascript")
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--disable-features=VizDisplayCompositor")
            
            # Additional background processing options
            chrome_options.add_argument("--disable-background-timer-throttling")
            chrome_options.add_argument("--disable-backgrounding-occluded-windows")
            chrome_options.add_argument("--disable-renderer-backgrounding")
            chrome_options.add_argument("--disable-background-networking")
            chrome_options.add_argument("--disable-default-apps")
            chrome_options.add_argument("--disable-sync")
            chrome_options.add_argument("--disable-translate")
            chrome_options.add_argument("--hide-scrollbars")
            chrome_options.add_argument("--mute-audio")
            chrome_options.add_argument("--no-first-run")
            chrome_options.add_argument("--disable-logging")
            chrome_options.add_argument("--disable-permissions-api")
            chrome_options.add_argument("--disable-popup-blocking")
            chrome_options.add_argument("--disable-prompt-on-repost")
            chrome_options.add_argument("--disable-hang-monitor")
            chrome_options.add_argument("--disable-client-side-phishing-detection")
            chrome_options.add_argument("--disable-component-update")
            chrome_options.add_argument("--disable-domain-reliability")
            chrome_options.add_argument("--disable-features=TranslateUI")
            chrome_options.add_argument("--disable-ipc-flooding-protection")
            
            driver = webdriver.Chrome(options=chrome_options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            print(f"🚀 Starting Selenium Instagram Message Sender...")
            print(f"📋 Target usernames: {usernames}")
            print(f"💬 Message template: {message_template}")
            print(f"⏱️ Delay: {delay_seconds} seconds")
            print(f"👤 Login username: {username}")
            print(f"🔄 Running in background mode...")
            
            # Go to Instagram login page
            driver.get("https://www.instagram.com/accounts/login/")
            time.sleep(3)
            
            # Login with username and password
            try:
                # Find username field
                username_field = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.NAME, "username"))
                )
                username_field.clear()
                username_field.send_keys(username)
                time.sleep(1)
                
                # Find password field
                password_field = driver.find_element(By.NAME, "password")
                password_field.clear()
                password_field.send_keys(password)
                time.sleep(1)
                
                # Click login button
                login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
                login_button.click()
                time.sleep(8)  # Increased wait time for login processing
                
                print("✅ Login credentials submitted")
                print("⏳ Waiting for login to complete...")
                
            except TimeoutException:
                return {
                    'success': False,
                    'error': 'Failed to find login form. Instagram may have changed.',
                    'results': results
                }
            
            # Handle 2FA/OTP if required
            try:
                # Check if 2FA page is loaded
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, "//input[@name='security_code']"))
                )
                print("🔐 2FA/OTP required. Please check your phone for the code.")
                
                # Wait for user to manually enter OTP
                st.info("🔐 **2FA/OTP Required!**")
                st.info("Please check your phone for the verification code and enter it in the browser.")
                st.info("The automation will continue after you complete the 2FA process.")
                
                # Wait for user to complete 2FA (check for home page)
                WebDriverWait(driver, 300).until(  # Wait up to 5 minutes
                    EC.presence_of_element_located((By.CSS_SELECTOR, "svg[aria-label='Home']"))
                )
                print("✅ 2FA completed successfully")
                
            except TimeoutException:
                # No 2FA required, check if login was successful
                try:
                    # Try multiple selectors for successful login
                    login_success_selectors = [
                        "svg[aria-label='Home']",
                        "svg[aria-label='Ana Sayfa']", 
                        "a[href='/']",
                        "div[role='main']",
                        "main",
                        "nav[role='navigation']"
                    ]
                    
                    login_successful = False
                    for selector in login_success_selectors:
                        try:
                            WebDriverWait(driver, 3).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                            )
                            print(f"✅ Successfully logged in (found: {selector})")
                            login_successful = True
                            break
                        except TimeoutException:
                            continue
                    
                    if not login_successful:
                        # Check if we're still on login page (login failed)
                        current_url = driver.current_url
                        print(f"🔍 Current URL: {current_url}")
                        print(f"🔍 Page title: {driver.title}")
                        
                        if "login" in current_url or "challenge" in current_url:
                            # Check for specific error messages
                            try:
                                error_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'error') or contains(text(), 'incorrect') or contains(text(), 'wrong')]")
                                if error_elements:
                                    error_text = error_elements[0].text
                                    print(f"❌ Login error message: {error_text}")
                                    return {
                                        'success': False,
                                        'error': f'Login failed: {error_text}',
                                        'results': results
                                    }
                            except:
                                pass
                            
                            return {
                                'success': False,
                                'error': 'Login failed. Please check your credentials.',
                                'results': results
                            }
                        else:
                            print("✅ Login appears successful (URL changed from login page)")
                            
                except Exception as e:
                    print(f"⚠️ Login check error: {str(e)}")
                    # Continue anyway, might be successful
            
            # Handle post-login modals
            try:
                modal_selectors = [
                    "//button[contains(text(), 'Not Now')]",
                    "//button[contains(text(), 'Şimdi Değil')]",
                    "//button[contains(text(), 'Later')]",
                    "//button[contains(text(), 'Daha Sonra')]"
                ]
                
                for selector in modal_selectors:
                    try:
                        button = WebDriverWait(driver, 3).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                        button.click()
                        time.sleep(2)
                        break
                    except:
                        continue
                        
            except:
                pass  # No modals to handle
            
            # Send messages to each user
            for i, username in enumerate(usernames):
                try:
                    print(f"📤 Processing @{username} ({i+1}/{len(usernames)}) - Background mode")
                    
                    # Go to user's profile
                    profile_url = f"https://www.instagram.com/{username}/"
                    driver.get(profile_url)
                    time.sleep(3)
                    
                    # Check if profile exists
                    try:
                        WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "h2"))
                        )
                    except TimeoutException:
                        results['failed_sends'] += 1
                        results['failure_details'].append({
                            'username': username,
                            'error': 'Profile not found or private'
                        })
                        print(f"❌ Profile @{username} not found or private")
                        continue
                    
                    # Click Message button - try direct message first, then three dots menu
                    message_clicked = False
                    
                    # First try: Direct Message button
                    try:
                        message_button = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Message') or contains(text(), 'Mesaj')]"))
                        )
                        message_button.click()
                        time.sleep(2)
                        message_clicked = True
                        print(f"✅ Direct message button found for @{username}")
                    except TimeoutException:
                        print(f"⚠️ Direct message button not found for @{username}, trying three dots menu...")
                    
                    # Second try: Three dots menu (for non-followed accounts)
                    if not message_clicked:
                        try:
                            # Click three dots menu (Seçenekler) - Updated selectors
                            three_dots_selectors = [
                                "//div[@role='button' and .//svg[@aria-label='Seçenekler']]",
                                "//button[@aria-label='Seçenekler']",
                                "//button[@aria-label='Options']",
                                "//div[contains(@class, 'x1i10hfl') and @role='button']",
                                "//div[contains(@class, 'x1i10hfl') and contains(@class, 'x1a2a7pz')]"
                            ]
                            
                            three_dots_clicked = False
                            for selector in three_dots_selectors:
                                try:
                                    three_dots_button = WebDriverWait(driver, 3).until(
                                        EC.element_to_be_clickable((By.XPATH, selector))
                                    )
                                    three_dots_button.click()
                                    time.sleep(2)
                                    print(f"✅ Three dots menu clicked for @{username} (selector: {selector})")
                                    three_dots_clicked = True
                                    break
                                except TimeoutException:
                                    continue
                            
                            if not three_dots_clicked:
                                print(f"⚠️ Three dots menu not found for @{username}")
                            else:
                                # Now look for "Mesaj Gönder" button in the dropdown
                                message_selectors = [
                                    "//button[contains(text(), 'Mesaj Gönder')]",
                                    "//button[contains(text(), 'Send Message')]",
                                    "//a[contains(text(), 'Mesaj Gönder')]",
                                    "//a[contains(text(), 'Send Message')]",
                                    "//div[contains(text(), 'Mesaj Gönder')]",
                                    "//div[contains(text(), 'Send Message')]",
                                    "//span[contains(text(), 'Mesaj Gönder')]",
                                    "//span[contains(text(), 'Send Message')]"
                                ]
                                
                                message_found = False
                                for selector in message_selectors:
                                    try:
                                        message_button = WebDriverWait(driver, 3).until(
                                            EC.element_to_be_clickable((By.XPATH, selector))
                                        )
                                        message_button.click()
                                        time.sleep(2)
                                        message_clicked = True
                                        message_found = True
                                        print(f"✅ Message button found in three dots menu for @{username} (selector: {selector})")
                                        break
                                    except TimeoutException:
                                        continue
                                
                                if not message_found:
                                    print(f"⚠️ Message button not found in three dots menu for @{username}")
                            
                        except Exception as e:
                            print(f"⚠️ Three dots menu error for @{username}: {str(e)}")
                    
                    # Third try: Alternative selectors
                    if not message_clicked:
                        try:
                            message_button = driver.find_element(By.CSS_SELECTOR, "a[href*='/direct/inbox/']")
                            message_button.click()
                            time.sleep(2)
                            message_clicked = True
                            print(f"✅ Alternative message button found for @{username}")
                        except:
                            pass
                    
                    # If still no message button found, check for follow requirement
                    if not message_clicked:
                        try:
                            # Look for follow button to determine if account needs to be followed
                            follow_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Follow') or contains(text(), 'Takip Et')]")
                            if follow_button:
                                results['failed_sends'] += 1
                                results['failure_details'].append({
                                    'username': username,
                                    'error': 'Account not followed - you need to follow this account first to send messages'
                                })
                                print(f"⚠️ Account @{username} not followed - need to follow first")
                                continue
                        except:
                            pass
                        
                        results['failed_sends'] += 1
                        results['failure_details'].append({
                            'username': username,
                            'error': 'Message button not found - account may not be followed or may require manual interaction'
                        })
                        print(f"❌ Message button not found for @{username} - may need to follow first or manual interaction required")
                        continue
                    
                    # Find message input - Multiple selectors
                    message_input_selectors = [
                        "textarea[placeholder*='Message']",
                        "textarea[placeholder*='Mesaj']",
                        "textarea[placeholder*='message']",
                        "textarea[placeholder*='mesaj']",
                        "div[contenteditable='true']",
                        "div[role='textbox']",
                        "textarea",
                        "input[type='text']"
                    ]
                    
                    message_input = None
                    for selector in message_input_selectors:
                        try:
                            message_input = WebDriverWait(driver, 3).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                            )
                            print(f"✅ Message input found for @{username} (selector: {selector})")
                            break
                        except TimeoutException:
                            continue
                    
                    if not message_input:
                        results['failed_sends'] += 1
                        results['failure_details'].append({
                            'username': username,
                            'error': 'Message input not found'
                        })
                        print(f"❌ Message input not found for @{username}")
                        continue
                    
                    # Handle notification popups that may appear
                    self._handle_notification_popups(driver)
                    
                    # Type message
                    personalized_message = self.personalize_message(message_template, {'username': username, 'first name': username})
                    message_input.clear()
                    message_input.send_keys(personalized_message)
                    time.sleep(1)
                    
                    # Send message - Multiple selectors
                    send_button_selectors = [
                        "//button[contains(text(), 'Send')]",
                        "//button[contains(text(), 'Gönder')]",
                        "//button[contains(text(), 'send')]",
                        "//button[contains(text(), 'gönder')]",
                        "//button[@type='submit']",
                        "//button[contains(@class, 'send')]",
                        "//div[contains(@class, 'send')]",
                        "//svg[@aria-label='Send']",
                        "//svg[@aria-label='Gönder']"
                    ]
                    
                    send_clicked = False
                    for selector in send_button_selectors:
                        try:
                            send_button = WebDriverWait(driver, 3).until(
                                EC.element_to_be_clickable((By.XPATH, selector))
                            )
                            send_button.click()
                            time.sleep(2)
                            send_clicked = True
                            print(f"✅ Send button clicked for @{username} (selector: {selector})")
                            break
                        except TimeoutException:
                            continue
                    
                    if not send_clicked:
                        # Try pressing Enter as alternative
                        try:
                            from selenium.webdriver.common.keys import Keys
                            message_input.send_keys(Keys.ENTER)
                            time.sleep(2)
                            send_clicked = True
                            print(f"✅ Message sent via Enter key for @{username}")
                        except:
                            pass
                    
                    if send_clicked:
                        results['successful_sends'] += 1
                        results['success_details'].append({
                            'username': username,
                            'message': personalized_message,
                            'sent_at': time.time()
                        })
                        print(f"✅ Message sent to @{username}")
                    else:
                        results['failed_sends'] += 1
                        results['failure_details'].append({
                            'username': username,
                            'error': 'Send button not found'
                        })
                        print(f"❌ Send button not found for @{username}")
                        continue
                    
                    # Add delay between messages
                    if i < len(usernames) - 1:  # Don't delay after last message
                        print(f"⏱️ Waiting {delay_seconds} seconds before next message...")
                        time.sleep(delay_seconds)
                        
                        # Add random variation to avoid detection
                        random_delay = random.randint(1, 3)
                        time.sleep(random_delay)
                    
                except Exception as e:
                    results['failed_sends'] += 1
                    results['failure_details'].append({
                        'username': username,
                        'error': f'Unexpected error: {str(e)}'
                    })
                    print(f"❌ Error sending message to @{username}: {e}")
                    continue
            
            return {
                'success': True,
                'total_sent': results['successful_sends'],
                'results': results,
                'message': f'Successfully sent {results["successful_sends"]} messages via Selenium'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Selenium error: {str(e)}',
                'results': results
            }
        finally:
            if driver:
                driver.quit()
    
    def create_selenium_message_campaign(self, campaign_name, target_leads, message_template, 
                                       username, password, delay_seconds=10):
        """
        Create and execute a complete message campaign using Selenium with OTP login
        
        Args:
            campaign_name (str): Name of the campaign
            target_leads (list): List of target lead dictionaries
            message_template (str): Message template with placeholders
            username (str): Instagram username for login
            password (str): Instagram password for login
            delay_seconds (int): Delay between messages
        
        Returns:
            dict: Campaign results with success/failure details
        """
        try:
            # Extract usernames from target accounts
            usernames = [lead.get('username', '') for lead in target_leads if lead.get('username')]
            
            if not usernames:
                return {
                    'success': False,
                    'error': 'No valid usernames found in target leads',
                    'results': None
                }
            
            print(f"🚀 Starting Selenium campaign: {campaign_name}")
            print(f"📋 Target usernames: {usernames}")
            print(f"⏱️ Delay between messages: {delay_seconds} seconds")
            
            # Send messages via Selenium
            results = self.send_selenium_instagram_messages(
                usernames=usernames,
                message_template=message_template,
                username=username,
                password=password,
                delay_seconds=delay_seconds
            )
            
            # Save campaign to database
            save_success, save_message = self.save_message_campaign(
                campaign_name, 
                target_leads, 
                message_template, 
                {
                    'successful_sends': results.get('total_sent', 0),
                    'failed_sends': len(usernames) - results.get('total_sent', 0),
                    'success_details': results.get('results', {}).get('success_details', []),
                    'failure_details': results.get('results', {}).get('failure_details', [])
                }
            )
            
            return {
                'success': True,
                'campaign_name': campaign_name,
                'results': results,
                'saved_to_database': save_success
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Selenium campaign creation failed: {str(e)}",
                'results': None
            }

    # ===============================================
    # APIFY INSTAGRAM BULK MESSAGE SENDER
    # ===============================================
    
    def send_apify_instagram_messages(self, usernames, message, cookies, delay_seconds=5):
        """
        Send bulk Instagram messages using Apify Instagram Bulk Message Sender
        
        Args:
            usernames (list): List of Instagram usernames
            message (str): Message to send
            cookies (str): Instagram cookies (JSON format)
            delay_seconds (int): Delay between messages
        
        Returns:
            dict: Results with success/failure details
        """
        try:
            from apify_client import ApifyClient
            
            # Initialize Apify client
            client = ApifyClient(self.config.get('APIFY_API_TOKEN', ''))
            
            # Prepare input for Apify actor
            run_input = {
                "instagram_usernames": usernames,
                "message": message,
                "delay_seconds": delay_seconds,
                "cookies": cookies
            }
            
            print(f"🚀 Starting Apify Instagram Bulk Message Sender...")
            print(f"📋 Target usernames: {usernames}")
            print(f"💬 Message: {message}")
            print(f"⏱️ Delay: {delay_seconds} seconds")
            
            # Run the Apify actor
            run = client.actor("bhansalisoft/instagram-bulk-message-sender").call(run_input=run_input)
            
            # Get results
            results = []
            for item in client.dataset(run["defaultDatasetId"]).iterate_items():
                results.append(item)
            
            return {
                'success': True,
                'total_sent': len(results),
                'results': results,
                'message': f'Successfully sent {len(results)} messages via Apify'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Apify error: {str(e)}',
                'results': []
            }
    
    def format_instagram_cookies_for_apify(self, cookies_list):
        """
        Format Instagram cookies for Apify actor
        
        Args:
            cookies_list (list): Instagram cookies list (from JSON)
            
        Returns:
            str: JSON formatted cookies string
        """
        import json
        
        # Apify expects cookies in Selenium format
        formatted_cookies = []
        
        for cookie in cookies_list:
            # Selenium cookie format - only required fields
            formatted_cookie = {
                "name": cookie.get("name", ""),
                "value": cookie.get("value", ""),
                "domain": cookie.get("domain", ".instagram.com"),
                "path": cookie.get("path", "/")
            }
            
            # Add optional fields if they exist
            if "httpOnly" in cookie:
                formatted_cookie["httpOnly"] = cookie["httpOnly"]
            if "secure" in cookie:
                formatted_cookie["secure"] = cookie["secure"]
            if "expires" in cookie:
                formatted_cookie["expires"] = cookie["expires"]
                
            formatted_cookies.append(formatted_cookie)
        
        return json.dumps(formatted_cookies)
    
    def create_apify_message_campaign(self, campaign_name, target_leads, message_template, 
                                    cookies, delay_seconds=5):
        """
        Create and execute a complete message campaign using Apify
        
        Args:
            campaign_name (str): Name of the campaign
            target_leads (list): List of target lead dictionaries
            message_template (str): Message template with placeholders
            cookies (dict): Instagram cookies
            delay_seconds (int): Delay between messages
        
        Returns:
            dict: Campaign results with success/failure details
        """
        try:
            # Extract usernames from target accounts
            usernames = [lead.get('username', '') for lead in target_leads if lead.get('username')]
            
            if not usernames:
                return {
                    'success': False,
                    'error': 'No valid usernames found in target leads',
                    'results': None
                }
            
            # Format cookies for Apify
            cookies_json = self.format_instagram_cookies_for_apify(cookies)
            
            # Send messages via Apify
            results = self.send_apify_instagram_messages(
                usernames=usernames,
                message=message_template,
                cookies=cookies_json,
                delay_seconds=delay_seconds
            )
            
            # Save campaign to database
            save_success, save_message = self.save_message_campaign(
                campaign_name, 
                target_leads, 
                message_template, 
                {
                    'successful_sends': results.get('total_sent', 0),
                    'failed_sends': len(usernames) - results.get('total_sent', 0),
                    'success_details': results.get('results', []),
                    'failure_details': []
                }
            )
            
            return {
                'success': True,
                'campaign_name': campaign_name,
                'results': results,
                'saved_to_database': save_success
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Apify campaign creation failed: {str(e)}",
                'results': None
            }

    # ===============================================
    # UNIPILE INSTAGRAM API INTEGRATION
    # ===============================================
    
    def _get_unipile_headers(self):
        """Get Unipile API headers"""
        return {
            "X-API-KEY": self.config.get('UNIPILE_API_KEY', ''),
            "accept": "application/json"
        }
    
    def _format_instagram_cookies(self, cookies):
        """
        Format Instagram cookies for Unipile API
        
        Args:
            cookies (dict): Raw Instagram cookies
            
        Returns:
            dict: Formatted cookies for Unipile
        """
        required_cookies = [
            'sessionid',
            'csrftoken',
            'ds_user_id',
            'ig_did',
            'mid',
            'rur'
        ]
        
        formatted_cookies = {}
        for cookie_name in required_cookies:
            if cookie_name in cookies:
                formatted_cookies[cookie_name] = cookies[cookie_name]
        
        if not formatted_cookies.get('sessionid'):
            raise ValueError("sessionid cookie is required for authentication")
            
        return formatted_cookies
    
    def connect_instagram_account(self, username, password=None, cookies=None):
        """
        Connect Instagram account to Unipile using either password or cookies
        
        Args:
            username (str): Instagram username
            password (str, optional): Instagram password
            cookies (dict, optional): Instagram cookies for authentication
        
        Returns:
            tuple: (success, message, account_id)
        """
        try:
            headers = self._get_unipile_headers()
            
            print(f"🔍 Connecting Instagram account: @{username}")
            print(f"📡 API URL: {self.config.get('UNIPILE_BASE_URL', 'https://api21.unipile.com:15121')}/api/v1/accounts")
            print(f"🔑 API Key: {self.config.get('UNIPILE_API_KEY', 'Not set')[:10]}...")
            
            # Prepare connection data based on authentication method
            connect_data = {
                "provider": "INSTAGRAM",
                "username": username,
                "proxy": {
                    "source": "UNIPILE",
                    "host": "brd.superproxy.io",
                    "port": 33335,
                    "username": "brd-customer-hl_ef5019d9-zone-france-ip-58.97.241.247",
                    "password": "iqepcffaeu65",
                    "protocol": "http"
                }
            }

            # Add authentication method (password or cookies)
            if password:
                connect_data["password"] = password
            elif cookies:
                # For Instagram cookie auth, only sessionid is required
                if not cookies.get('sessionid'):
                    raise ValueError("sessionid cookie is required for Instagram authentication")
                connect_data["sessionid"] = cookies['sessionid']
            else:
                raise ValueError("Either password or cookies must be provided")
            
            print(f"📤 Sending request data: {json.dumps(connect_data, indent=2)}")
            
            response = requests.post(
                f"{self.config.get('UNIPILE_BASE_URL', 'https://api21.unipile.com:15121')}/api/v1/accounts",
                headers=headers,
                json=connect_data,
                timeout=30
            )
            
            print(f"📡 Response Status: {response.status_code}")
            print(f"📡 Response Headers: {dict(response.headers)}")
            print(f"📡 Response Text: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                account_id = result.get('id')
                print(f"✅ Success! Account ID: {account_id}")
                return True, "Instagram account connected successfully", account_id
            else:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('message', 'Failed to connect Instagram account')
                    error_details = error_data.get('details', '')
                    print(f"❌ API Error: {error_msg}")
                    print(f"❌ Error Details: {error_details}")
                    return False, f"Connection failed: {error_msg}. Details: {error_details}", None
                except:
                    print(f"❌ Raw Error Response: {response.text}")
                    return False, f"Connection failed: HTTP {response.status_code} - {response.text}", None
                
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
            return False, f"Error connecting Instagram account: {str(e)}", None
    
    def get_instagram_accounts(self):
        """
        Get connected Instagram accounts
        
        Returns:
            list: List of connected Instagram accounts
        """
        try:
            headers = self._get_unipile_headers()
            
            response = requests.get(
                f"{self.config.get('UNIPILE_BASE_URL', 'https://api21.unipile.com:15121')}/api/v1/accounts",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                instagram_accounts = []
                for account in result.get('data', []):
                    if account.get('provider') == 'instagram':
                        instagram_accounts.append({
                            'id': account.get('id'),
                            'username': account.get('username'),
                            'status': account.get('status'),
                            'connected_at': account.get('created_at')
                        })
                return instagram_accounts
            else:
                return []
                
        except Exception as e:
            print(f"Error getting Instagram accounts: {e}")
            return []
    
    def get_or_create_chat(self, account_id, target_username):
        """
        Get existing chat or create new chat with target user
        
        Args:
            account_id (str): Connected Instagram account ID
            target_username (str): Target Instagram username
        
        Returns:
            tuple: (success, chat_id, message)
        """
        try:
            headers = self._get_unipile_headers()
            
            # First, try to find existing chat
            response = requests.get(
                f"{self.config.get('UNIPILE_BASE_URL', 'https://api21.unipile.com:15121')}/api/v1/chats",
                headers=headers,
                params={
                    'account_id': account_id,
                    'provider': 'instagram'
                },
                timeout=30
            )
            
            if response.status_code == 200:
                chats = response.json().get('data', [])
                
                # Look for existing chat with target user
                for chat in chats:
                    if target_username.lower() in chat.get('name', '').lower():
                        return True, chat.get('id'), "Existing chat found"
            
            # If no existing chat, create new one
            chat_data = {
                'account_id': account_id,
                'provider': 'instagram',
                'recipient': target_username
            }
            
            response = requests.post(
                f"{self.config.get('UNIPILE_BASE_URL', 'https://api21.unipile.com:15121')}/api/v1/chats",
                headers=headers,
                json=chat_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                chat_id = result.get('id')
                return True, chat_id, "New chat created"
            else:
                error_msg = response.json().get('message', 'Failed to create chat')
                return False, None, f"Chat creation failed: {error_msg}"
                
        except Exception as e:
            return False, None, f"Error managing chat: {str(e)}"
    
    def send_instagram_message(self, account_id, target_username, message_content):
        """
        Send message to Instagram user
        
        Args:
            account_id (str): Connected Instagram account ID
            target_username (str): Target Instagram username
            message_content (str): Message content to send
        
        Returns:
            tuple: (success, message, message_id)
        """
        try:
            headers = self._get_unipile_headers()
            
            # Get or create chat
            chat_success, chat_id, chat_message = self.get_or_create_chat(account_id, target_username)
            
            if not chat_success:
                return False, f"Chat error: {chat_message}", None
            
            # Send message
            message_data = {
                'account_id': account_id,
                'chat_id': chat_id,
                'content': message_content,
                'type': 'text'
            }
            
            response = requests.post(
                f"{self.config.get('UNIPILE_BASE_URL', 'https://api21.unipile.com:15121')}/api/v1/messages",
                headers=headers,
                json=message_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                message_id = result.get('id')
                return True, "Message sent successfully", message_id
            else:
                error_msg = response.json().get('message', 'Failed to send message')
                return False, f"Send failed: {error_msg}", None
                
        except Exception as e:
            return False, f"Error sending message: {str(e)}", None
    
    def send_bulk_messages(self, account_id, target_leads, message_template, delay_seconds=5, max_messages_per_hour=10):
        """
        Send bulk messages to multiple Instagram accounts with rate limiting
        
        Args:
            account_id (str): Connected Instagram account ID
            target_leads (list): List of target lead dictionaries
            message_template (str): Message template with placeholders
            delay_seconds (int): Delay between messages in seconds
            max_messages_per_hour (int): Maximum messages per hour
        
        Returns:
            dict: Results with success/failure counts and details
        """
        try:
            results = {
                'total_targets': len(target_leads),
                'successful_sends': 0,
                'failed_sends': 0,
                'success_details': [],
                'failure_details': [],
                'rate_limited': False
            }
            
            messages_sent_this_hour = 0
            start_time = time.time()
            
            for i, lead in enumerate(target_leads):
                # Check rate limiting
                current_time = time.time()
                if current_time - start_time < 3600:  # Within one hour
                    if messages_sent_this_hour >= max_messages_per_hour:
                        results['rate_limited'] = True
                        results['failure_details'].append({
                            'username': account.get('username', ''),
                            'error': 'Rate limit reached (max messages per hour)'
                        })
                        results['failed_sends'] += 1
                        continue
                else:
                    # Reset counter for new hour
                    messages_sent_this_hour = 0
                    start_time = current_time
                
                # Personalize message
                personalized_message = self.personalize_message(message_template, account)
                
                # Send message
                success, message, message_id = self.send_instagram_message(
                    account_id, 
                    account.get('username', ''), 
                    personalized_message
                )
                
                if success:
                    results['successful_sends'] += 1
                    results['success_details'].append({
                        'username': account.get('username', ''),
                        'message_id': message_id,
                        'personalized_message': personalized_message
                    })
                    messages_sent_this_hour += 1
                else:
                    results['failed_sends'] += 1
                    results['failure_details'].append({
                        'username': account.get('username', ''),
                        'error': message
                    })
                
                # Add delay between messages to avoid rate limiting
                if i < len(target_leads) - 1:  # Don't delay after last message
                    time.sleep(delay_seconds)
            
            return results
            
        except Exception as e:
            return {
                'total_targets': len(target_leads),
                'successful_sends': 0,
                'failed_sends': len(target_leads),
                'success_details': [],
                'failure_details': [{'error': f'Bulk send error: {str(e)}'}],
                'rate_limited': False
            }
    
    def save_message_campaign(self, campaign_name, target_leads, message_template, results):
        """
        Save message campaign results to database
        
        Args:
            campaign_name (str): Name of the campaign
            target_leads (list): List of target leads
            message_template (str): Message template used
            results (dict): Campaign results
        
        Returns:
            tuple: (success, message)
        """
        try:
            if not self.supabase_connected:
                return False, "Database not connected"
            
            campaign_data = [{
                "campaign_name": campaign_name,
                "message_template": message_template,
                "target_count": len(target_leads),
                "successful_sends": results.get('successful_sends', 0),
                "failed_sends": results.get('failed_sends', 0),
                "rate_limited": results.get('rate_limited', False),
                "success_details": results.get('success_details', []),
                "failure_details": results.get('failure_details', []),
                "created_at": datetime.now().isoformat()
            }]
            
            return self.save_to_database("message_campaigns", campaign_data)
            
        except Exception as e:
            return False, f"Error saving campaign: {str(e)}"
    
    def get_message_campaigns(self, limit=10):
        """
        Get message campaign history
        
        Args:
            limit (int): Maximum number of campaigns to retrieve
        
        Returns:
            list: List of campaign records
        """
        try:
            if not self.supabase_connected:
                return []
            
            result = self.supabase.table("message_campaigns").select("*").order("created_at", desc=True).limit(limit).execute()
            return result.data if result.data else []
            
        except Exception as e:
            print(f"Error getting message campaigns: {e}")
            return []
    
    def test_unipile_connection(self):
        """
        Test Unipile API connection and Instagram account status
        
        Returns:
            dict: Test results with connection status and account info
        """
        try:
            test_results = {
                'api_connection': False,
                'instagram_accounts': [],
                'error': None
            }
            
            # Test API connection by getting accounts
            headers = self._get_unipile_headers()
            
            response = requests.get(
                f"{self.config.get('UNIPILE_BASE_URL', 'https://api21.unipile.com:15121')}/api/v1/accounts",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                test_results['api_connection'] = True
                result = response.json()
                
                # Get Instagram accounts
                for account in result.get('data', []):
                    if account.get('provider') == 'instagram':
                        test_results['instagram_accounts'].append({
                            'id': account.get('id'),
                            'username': account.get('username'),
                            'status': account.get('status'),
                            'connected_at': account.get('created_at')
                        })
            else:
                test_results['error'] = f"API connection failed: {response.status_code} - {response.text}"
            
            return test_results
            
        except Exception as e:
            return {
                'api_connection': False,
                'instagram_accounts': [],
                'error': f"Test error: {str(e)}"
            }
    
    def create_message_campaign(self, campaign_name, target_leads, message_template, 
                              account_id=None, delay_seconds=5, max_messages_per_hour=10):
        """
        Create and execute a complete message campaign
        
        Args:
            campaign_name (str): Name of the campaign
            target_leads (list): List of target lead dictionaries
            message_template (str): Message template with placeholders
            account_id (str): Instagram account ID (if None, will use first available)
            delay_seconds (int): Delay between messages
            max_messages_per_hour (int): Maximum messages per hour
        
        Returns:
            dict: Campaign results with success/failure details
        """
        try:
            # Get Instagram account if not provided
            if not account_id:
                instagram_accounts = self.get_instagram_accounts()
                if not instagram_accounts:
                    return {
                        'success': False,
                        'error': 'No Instagram accounts connected. Please connect an account first.',
                        'results': None
                    }
                account_id = instagram_accounts[0]['id']
            
            # Send bulk messages
            results = self.send_bulk_messages(
                account_id, 
                target_leads, 
                message_template, 
                delay_seconds, 
                max_messages_per_hour
            )
            
            # Save campaign to database
            save_success, save_message = self.save_message_campaign(
                campaign_name, 
                target_leads, 
                message_template, 
                results
            )
            
            if not save_success:
                print(f"Warning: Could not save campaign to database: {save_message}")
            
            return {
                'success': True,
                'campaign_name': campaign_name,
                'results': results,
                'saved_to_database': save_success
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Campaign creation failed: {str(e)}",
                'results': None
            }
    
    def demo_message_campaign(self):
        """
        Demo function showing how to use the message campaign system
        
        Returns:
            dict: Demo results
        """
        try:
            print("🚀 Starting Unipile Instagram Message Campaign Demo")
            print("=" * 60)
            
            # Step 1: Test Unipile connection
            print("1. Testing Unipile API connection...")
            test_results = self.test_unipile_connection()
            
            if not test_results['api_connection']:
                return {
                    'success': False,
                    'error': f"Unipile API connection failed: {test_results.get('error', 'Unknown error')}",
                    'steps_completed': 0
                }
            
            print("✅ Unipile API connection successful")
            
            # Step 2: Check Instagram accounts
            print("2. Checking connected Instagram accounts...")
            instagram_accounts = test_results['instagram_accounts']
            
            if not instagram_accounts:
                return {
                    'success': False,
                    'error': "No Instagram accounts connected. Please connect an account first using connect_instagram_account()",
                    'steps_completed': 1
                }
            
            print(f"✅ Found {len(instagram_accounts)} connected Instagram account(s)")
            for account in instagram_accounts:
                print(f"   - {account['username']} (Status: {account['status']})")
            
            # Step 3: Create demo target account
            print("3. Creating demo target account...")
            demo_target = {
                "username": "tinercifedai",
                "full_name": "Tiner Cifedai",
                "nationality": "TÜRK",
                "followers_count": 1000,
                "source": "demo_target",
                "session_name": "Demo Session",
                "created_at": datetime.now().isoformat(),
                "profile_pic_url": ""
            }
            
            demo_accounts = [demo_target]
            
            print(f"📋 Using demo account:")
            print(f"   - @{demo_target['username']} ({demo_target.get('full_name', 'N/A')}) - {demo_target.get('nationality', 'Unknown')}")
            
            # Step 4: Create message template
            print("4. Creating message template...")
            message_template = """Merhaba [first name]! 👋

Instagram'da profilinizi gördüm ve çok etkileyici! 

Ben [username] hesabından yazıyorum. Sizinle bağlantı kurmak istiyorum.

Umarım bu mesaj sizi rahatsız etmez. 

İyi günler! 😊"""
            
            print("✅ Message template created")
            print("Template preview:")
            print("-" * 40)
            print(message_template)
            print("-" * 40)
            
            # Step 5: Create and run campaign
            print("5. Creating message campaign...")
            campaign_name = f"Demo Campaign - @tinercifedai - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            
            campaign_results = self.create_message_campaign(
                campaign_name=campaign_name,
                target_accounts=demo_accounts,
                message_template=message_template,
                delay_seconds=5,  # 5 seconds between messages for demo
                max_messages_per_hour=10  # Conservative limit for demo
            )
            
            if not campaign_results['success']:
                return {
                    'success': False,
                    'error': campaign_results['error'],
                    'steps_completed': 4
                }
            
            # Step 6: Show results
            print("6. Campaign results:")
            results = campaign_results['results']
            print(f"✅ Campaign '{campaign_name}' completed!")
            print(f"📊 Results:")
            print(f"   - Total targets: {results['total_targets']}")
            print(f"   - Successful sends: {results['successful_sends']}")
            print(f"   - Failed sends: {results['failed_sends']}")
            print(f"   - Rate limited: {results['rate_limited']}")
            
            if results['success_details']:
                print("✅ Successful messages:")
                for detail in results['success_details']:
                    print(f"   - @{detail['username']} (Message ID: {detail['message_id']})")
            
            if results['failure_details']:
                print("❌ Failed messages:")
                for detail in results['failure_details']:
                    print(f"   - @{detail['username']}: {detail['error']}")
            
            print("=" * 60)
            print("🎉 Demo completed successfully!")
            
            return {
                'success': True,
                'campaign_name': campaign_name,
                'results': results,
                'steps_completed': 6
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Demo failed: {str(e)}",
                'steps_completed': 0
            }
    
    def test_unipile_api_connection(self):
        """
        Test Unipile API connection with the provided API key
        
        Returns:
            dict: Test results
        """
        try:
            print("🔍 Testing Unipile API connection...")
            print(f"API Key: {self.config.get('UNIPILE_API_KEY', 'Not set')[:10]}...")
            print(f"Base URL: {self.config.get('UNIPILE_BASE_URL', 'https://api21.unipile.com:15121')}")
            
            headers = self._get_unipile_headers()
            print(f"Headers: {headers}")
            
            response = requests.get(
                f"{self.config.get('UNIPILE_BASE_URL', 'https://api21.unipile.com:15121')}/api/v1/accounts",
                headers=headers,
                timeout=30
            )
            
            print(f"Response Status: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            print(f"Response Text: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Unipile API connection successful!")
                print(f"📊 Response: {json.dumps(result, indent=2)}")
                
                return {
                    'success': True,
                    'status_code': response.status_code,
                    'response': result,
                    'message': 'API connection successful'
                }
            else:
                error_text = response.text
                print(f"❌ API connection failed: {response.status_code}")
                print(f"Error: {error_text}")
                
                return {
                    'success': False,
                    'status_code': response.status_code,
                    'error': error_text,
                    'message': f'API connection failed with status {response.status_code}'
                }
                
        except Exception as e:
            print(f"❌ Connection test error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': f'Connection test failed: {str(e)}'
            }
    
    def debug_unipile_connection(self):
        """
        Debug Unipile connection with detailed logging
        
        Returns:
            dict: Debug results
        """
        try:
            print("🔍 DEBUG: Unipile Connection Debug")
            print("=" * 50)
            
            # Check configuration
            api_key = self.config.get('UNIPILE_API_KEY', '')
            base_url = self.config.get('UNIPILE_BASE_URL', 'https://api21.unipile.com:15121')
            
            print(f"🔑 API Key: {api_key[:10]}... (length: {len(api_key)})")
            print(f"🌐 Base URL: {base_url}")
            
            if not api_key:
                return {
                    'success': False,
                    'error': 'UNIPILE_API_KEY not configured',
                    'debug_info': 'API key is empty or not set'
                }
            
            # Test headers
            headers = self._get_unipile_headers()
            print(f"📤 Headers: {headers}")
            
            # Test basic connectivity
            try:
                response = requests.get(
                    f"{base_url}/api/v1/accounts",
                    headers=headers,
                    timeout=10
                )
                
                print(f"📡 Response Status: {response.status_code}")
                print(f"📡 Response Headers: {dict(response.headers)}")
                print(f"📡 Response Text: {response.text[:500]}...")
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        'success': True,
                        'message': 'API connection successful',
                        'debug_info': {
                            'status_code': response.status_code,
                            'response': result,
                            'headers': dict(response.headers)
                        }
                    }
                else:
                    return {
                        'success': False,
                        'error': f'HTTP {response.status_code}',
                        'debug_info': {
                            'status_code': response.status_code,
                            'response_text': response.text,
                            'headers': dict(response.headers)
                        }
                    }
                    
            except requests.exceptions.ConnectionError as e:
                return {
                    'success': False,
                    'error': 'Connection error',
                    'debug_info': f'Cannot connect to {base_url}: {str(e)}'
                }
            except requests.exceptions.Timeout as e:
                return {
                    'success': False,
                    'error': 'Timeout error',
                    'debug_info': f'Request timeout: {str(e)}'
                }
            except Exception as e:
                return {
                    'success': False,
                    'error': 'Request error',
                    'debug_info': f'Request failed: {str(e)}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Debug failed: {str(e)}',
                'debug_info': 'Debug function error'
            }

    # ===============================================
    # USER AUTHENTICATION METHODS
    # ===============================================
    
    def _hash_password(self, password):
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _generate_user_id(self):
        """Generate unique user ID"""
        return str(uuid.uuid4())
    
    def create_user_tables(self):
        """Create user authentication tables in Supabase"""
        try:
            if not self.supabase_connected:
                return False, "Database not connected"
            
            # SQL commands to create tables
            create_users_sql = """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT,
                created_at TIMESTAMP DEFAULT NOW(),
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT true
            );
            """
            
            create_sessions_sql = """
            CREATE TABLE IF NOT EXISTS user_sessions (
                id SERIAL PRIMARY KEY,
                user_id TEXT REFERENCES users(id) ON DELETE CASCADE,
                session_name TEXT NOT NULL,
                session_data JSONB,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );
            """
            
            create_message_campaigns_sql = """
            CREATE TABLE IF NOT EXISTS message_campaigns (
                id SERIAL PRIMARY KEY,
                campaign_name TEXT NOT NULL,
                message_template TEXT,
                target_count INTEGER DEFAULT 0,
                successful_sends INTEGER DEFAULT 0,
                failed_sends INTEGER DEFAULT 0,
                rate_limited BOOLEAN DEFAULT false,
                success_details JSONB,
                failure_details JSONB,
                created_at TIMESTAMP DEFAULT NOW()
            );
            """
            
            create_indexes_sql = """
            CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
            CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
            CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
            CREATE INDEX IF NOT EXISTS idx_message_campaigns_created_at ON message_campaigns(created_at);
            """
            
            # Just try to verify tables exist with a simple query
            try:
                # Test if users table exists
                result = self.supabase.table("users").select("count", count="exact").limit(0).execute()
                print("✅ Users table exists and accessible")
                
                # Test if user_sessions table exists
                result = self.supabase.table("user_sessions").select("count", count="exact").limit(0).execute()
                print("✅ User_sessions table exists and accessible")
                
                # Test if message_campaigns table exists
                result = self.supabase.table("message_campaigns").select("count", count="exact").limit(0).execute()
                print("✅ Message_campaigns table exists and accessible")
                
            except Exception as test_error:
                print(f"❌ Tables not accessible: {test_error}")
                print("📝 Please run the SQL commands manually in Supabase Dashboard:")
                print("   1. Go to https://supabase.com/dashboard")
                print("   2. Select your project")
                print("   3. Go to SQL Editor")
                print("   4. Run the SQL commands below")
                print("")
                print("SQL Commands to run:")
                print(create_users_sql)
                print(create_sessions_sql)
                print(create_message_campaigns_sql)
                print(create_indexes_sql)
                return False, "Tables need to be created manually"
            
            return True, "User tables ready"
            
        except Exception as e:
            print(f"❌ Error creating user tables: {e}")
            return False, str(e)
    
    def register_user(self, username, email, password, full_name=""):
        """Register a new user"""
        try:
            if not self.supabase_connected:
                return False, "Database not connected"
            
            # Check if user already exists
            existing_user = self.supabase.table("users").select("username, email").or_(f"username.eq.{username},email.eq.{email}").execute()
            
            if existing_user.data:
                for user in existing_user.data:
                    if user["username"] == username:
                        return False, "Username already exists"
                    if user["email"] == email:
                        return False, "Email already exists"
            
            # Create new user
            user_id = self._generate_user_id()
            password_hash = self._hash_password(password)
            
            user_data = {
                "id": user_id,
                "username": username,
                "email": email,
                "password_hash": password_hash,
                "full_name": full_name,
                "created_at": datetime.now().isoformat()
            }
            
            result = self.supabase.table("users").insert(user_data).execute()
            
            if result.data:
                print(f"✅ User {username} registered successfully")
                return True, "User registered successfully"
            else:
                return False, "Failed to register user"
                
        except Exception as e:
            print(f"❌ Error registering user: {e}")
            return False, str(e)
    
    def login_user(self, username, password):
        """Authenticate user login"""
        try:
            if not self.supabase_connected:
                return False, "Database not connected", None
            
            password_hash = self._hash_password(password)
            
            # Find user by username and password
            result = self.supabase.table("users").select("*").eq("username", username).eq("password_hash", password_hash).eq("is_active", True).execute()
            
            if result.data:
                user = result.data[0]
                
                # Update last login
                self.supabase.table("users").update({"last_login": datetime.now().isoformat()}).eq("id", user["id"]).execute()
                
                print(f"✅ User {username} logged in successfully")
                return True, "Login successful", user
            else:
                return False, "Invalid username or password", None
                
        except Exception as e:
            print(f"❌ Error during login: {e}")
            return False, str(e), None
    
    def get_user_sessions(self, user_id):
        """Get all sessions for a user"""
        try:
            if not self.supabase_connected:
                return []
            
            result = self.supabase.table("user_sessions").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            print(f"❌ Error getting user sessions: {e}")
            return []
    
    def save_user_session(self, user_id, session_name, session_data):
        """Save a session for a user"""
        try:
            if not self.supabase_connected:
                return False, "Database not connected"
            
            session_record = {
                "user_id": user_id,
                "session_name": session_name,
                "session_data": session_data,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            result = self.supabase.table("user_sessions").insert(session_record).execute()
            
            if result.data:
                print(f"✅ Session '{session_name}' saved for user {user_id}")
                return True, "Session saved successfully"
            else:
                return False, "Failed to save session"
                
        except Exception as e:
            print(f"❌ Error saving user session: {e}")
            return False, str(e)
    
    def delete_user_session(self, user_id, session_id):
        """Delete a specific session for a user"""
        try:
            if not self.supabase_connected:
                return False, "Database not connected"
            
            result = self.supabase.table("user_sessions").delete().eq("user_id", user_id).eq("id", session_id).execute()
            
            if result.data:
                print(f"✅ Session {session_id} deleted for user {user_id}")
                return True, "Session deleted successfully"
            else:
                return False, "Session not found or not authorized"
                
        except Exception as e:
            print(f"❌ Error deleting user session: {e}")
            return False, str(e)
    
    def save_instagram_account(self, username, password, account_name=None):
        """Save Instagram account credentials securely"""
        try:
            if not self.supabase_connected:
                return False, "Database not connected"
            
            # Hash password for security (in real app, use proper encryption)
            import hashlib
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            account_data = {
                "username": username,
                "password_hash": password_hash,
                "account_name": account_name or username,
                "created_at": datetime.now().isoformat(),
                "status": "active"
            }
            
            result = self.supabase.table("instagram_accounts").insert(account_data).execute()
            
            if result.data:
                return True, "Account saved successfully", result.data[0]['id']
            else:
                return False, "Failed to save account", None
                
        except Exception as e:
            return False, f"Error saving account: {str(e)}", None
    
    def get_saved_instagram_accounts(self):
        """Get all saved Instagram accounts"""
        try:
            if not self.supabase_connected:
                return []
            
            result = self.supabase.table("instagram_accounts").select("*").execute()
            return result.data if result.data else []
            
        except Exception as e:
            print(f"Error getting saved accounts: {e}")
            return []
    
    def delete_instagram_account(self, account_id):
        """Delete Instagram account"""
        try:
            if not self.supabase_connected:
                return False, "Database not connected"
            
            result = self.supabase.table("instagram_accounts").delete().eq("id", account_id).execute()
            return True, "Account deleted successfully"
            
        except Exception as e:
            return False, f"Error deleting account: {str(e)}"

    def get_all_historical_leads(self):
        """Get all leads from all user sessions in the database"""
        try:
            if not self.supabase_connected:
                return []
            
            # Get all user sessions with nationality data from database
            result = self.supabase.table("user_sessions").select("*").order("created_at", desc=True).execute()
            
            # Also get direct nationality data from database
            nationality_result = self.supabase.table("nationality_classifications").select("*").execute()
            nationality_map = {}
            if nationality_result.data:
                for item in nationality_result.data:
                    username = item.get("username", "")
                    if username:
                        nationality_map[username] = {
                            "nationality": item.get("nationality", "Unknown"),
                            "full_name": item.get("full_name", username),
                            "followers_count": item.get("followers_count", 0)
                        }
            
            if not result.data:
                return []
            
            all_leads = []
            seen_usernames = set()
            
            for session in result.data:
                try:
                    session_data = session.get("session_data", {})
                    session_name = session.get("session_name", "Unknown Session")
                    created_at = session.get("created_at", "")
                    
                    # Extract usernames from session data
                    usernames = session_data.get("usernames", [])
                    for username in usernames:
                        if username and username not in seen_usernames:
                            seen_usernames.add(username)
                            # Get nationality from database if available
                            nationality_info = nationality_map.get(username, {})
                            all_leads.append({
                                "username": username,
                                "full_name": nationality_info.get("full_name", username),
                                "source": "historical_usernames",
                                "followers_count": nationality_info.get("followers_count", 0),
                                "nationality": nationality_info.get("nationality", "Unknown"),
                                "session_name": session_name,
                                "created_at": created_at,
                                "profile_pic_url": ""
                            })
                    
                    # Extract profiles from session data
                    profiles_data = session_data.get("profiles_df", [])
                    if isinstance(profiles_data, list):
                        for profile in profiles_data:
                            username = profile.get("username", "")
                            if username and username not in seen_usernames:
                                seen_usernames.add(username)
                                # Get nationality from database if available, otherwise from profile
                                nationality_info = nationality_map.get(username, {})
                                nationality = nationality_info.get("nationality") or profile.get("Nationality", profile.get("nationality", "Unknown"))
                                
                                all_leads.append({
                                    "username": username,
                                    "full_name": nationality_info.get("full_name") or profile.get("full_name", username),
                                    "source": "historical_profiles",
                                    "followers_count": max(nationality_info.get("followers_count", 0), profile.get("followers_count", 0)),
                                    "nationality": nationality,
                                    "session_name": session_name,
                                    "created_at": created_at,
                                    "profile_pic_url": profile.get("profilePicUrl", profile.get("profile_pic_url", ""))
                                })
                    
                    # Extract nationality classifications from session data
                    nationality_data = session_data.get("nationality_classifications", [])
                    if isinstance(nationality_data, list):
                        for classification in nationality_data:
                            username = classification.get("username", "")
                            if username and username not in seen_usernames:
                                seen_usernames.add(username)
                                # Get nationality from database if available, otherwise from classification
                                nationality_info = nationality_map.get(username, {})
                                nationality = nationality_info.get("nationality") or classification.get("Nationality", classification.get("nationality", "Unknown"))
                                
                                all_leads.append({
                                    "username": username,
                                    "full_name": nationality_info.get("full_name") or classification.get("full_name", username),
                                    "source": "historical_classifications", 
                                    "followers_count": max(nationality_info.get("followers_count", 0), classification.get("followers_count", 0)),
                                    "nationality": nationality,
                                    "session_name": session_name,
                                    "created_at": created_at,
                                    "profile_pic_url": classification.get("profilePicUrl", classification.get("profile_pic_url", ""))
                                })
                            elif username in seen_usernames:
                                # Update nationality for existing account
                                for lead in all_leads:
                                    if lead["username"] == username and lead["nationality"] == "Unknown":
                                        nationality_info = nationality_map.get(username, {})
                                        nationality_value = nationality_info.get("nationality") or classification.get("Nationality", classification.get("nationality", "Unknown"))
                                        lead["nationality"] = nationality_value
                                        if nationality_info.get("followers_count", 0) > lead["followers_count"]:
                                            lead["followers_count"] = nationality_info.get("followers_count", 0)
                                        elif classification.get("followers_count", 0) > lead["followers_count"]:
                                            lead["followers_count"] = classification.get("followers_count", 0)
                                        break
                    
                except Exception as e:
                    print(f"⚠️ Error processing session data: {e}")
                    continue
            
            print(f"✅ Retrieved {len(all_leads)} historical leads from database")
            return all_leads
            
        except Exception as e:
            print(f"❌ Error getting historical leads: {e}")
            return []