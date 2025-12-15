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
                'SUPABASE_API_KEY': os.getenv('SUPABASE_API_KEY') or os.getenv('SUPABASE_KEY'),  # Support both names
                'APIFY_API_TOKEN': os.getenv('APIFY_API_TOKEN'),
                'UNIPILE_API_KEY': os.getenv('UNIPILE_API_KEY', 'k8IpFvnp.1H5f5alAgW2gK5M+J4GvW2M1lavbPHdsZfUGXBbEF+U='),
                'UNIPILE_BASE_URL': os.getenv('UNIPILE_BASE_URL', 'https://api21.unipile.com:15121'),
                'OPENROUTER_API_KEY': os.getenv('OPENROUTER_API_KEY', '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'),
                'INSTAGRAM_USERNAME': os.getenv('INSTAGRAM_USERNAME', 'your_instagram_username'),
                'INSTAGRAM_PASSWORD': os.getenv('INSTAGRAM_PASSWORD', 'your_instagram_password'),
                'POSTGRES_HOST': os.getenv('POSTGRES_HOST'),
                'POSTGRES_PORT': os.getenv('POSTGRES_PORT', '5432'),
                'POSTGRES_DB': os.getenv('POSTGRES_DB'),
                'POSTGRES_USER': os.getenv('POSTGRES_USER'),
                'POSTGRES_PASSWORD': os.getenv('POSTGRES_PASSWORD')
            }
        
        self.config = config
        self.supabase = None
        self.postgres_conn = None
        
        # In-memory storage for leads and sessions (replace with database later)
        self.leads_storage = []
        self.sessions_storage = []
        self.instagram_accounts = []
        self.supabase_connected = False
        self.postgres_connected = False
        
        # Global driver for bulk campaigns
        self.global_driver = None
        self._bulk_campaign_active = False
        
        # Initialize database connections
        self._setup_database_connections()
        
        # Create tables if they don't exist
        self._create_tables_if_not_exist()
        
        # Load existing data from Supabase on startup
        self._load_data_from_supabase()
    
    def _setup_database_connections(self):
        """Setup database connections (Supabase and PostgreSQL)"""
        # Try Supabase connection first
        if SUPABASE_AVAILABLE and self.config.get('SUPABASE_URL') and self.config.get('SUPABASE_API_KEY'):
            try:
                supabase_url = self.config['SUPABASE_URL']
                print(f"🔍 Connecting to Supabase: {supabase_url}")
                
                # Test DNS resolution first
                try:
                    import socket
                    from urllib.parse import urlparse
                    parsed = urlparse(supabase_url)
                    hostname = parsed.hostname
                    if hostname:
                        print(f"🔍 Testing DNS resolution for Supabase hostname: {hostname}")
                        ip_address = socket.gethostbyname(hostname)
                        print(f"✅ DNS resolution successful: {hostname} -> {ip_address}")
                except socket.gaierror as dns_error:
                    print(f"❌ DNS resolution failed for Supabase: {dns_error}")
                    print(f"⚠️ Cannot resolve Supabase hostname. Check your internet connection and DNS settings.")
                    self.supabase_connected = False
                    return
                except Exception as dns_check_error:
                    print(f"⚠️ DNS check warning: {dns_check_error}")
                
                self.supabase = create_client(
                    supabase_url, 
                    self.config['SUPABASE_API_KEY']
                )
                print("✅ Supabase client created")
                
                # Test connection
                print("🔍 Testing Supabase connection...")
                self.supabase.table("scraping_sessions").select("id").limit(1).execute()
                self.supabase_connected = True
                print("✅ Supabase connected successfully")
            except socket.gaierror as dns_error:
                print(f"❌ DNS error during Supabase connection: {dns_error}")
                print(f"⚠️ Cannot resolve Supabase hostname. Check your internet connection.")
                self.supabase_connected = False
            except Exception as e:
                error_msg = str(e)
                print(f"⚠️ Supabase connection failed: {error_msg}")
                print(f"⚠️ Error type: {type(e).__name__}")
                if "name or service not known" in error_msg.lower():
                    print("⚠️ This appears to be a DNS resolution issue.")
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
    
    def save_nationality_results(self, classified_df, session_name=None):
        """Save nationality classification results to leads - update existing or create new"""
        if classified_df.empty:
            return []
        
        try:
            leads_data = []
            updated_count = 0
            new_count = 0
            
            for _, row in classified_df.iterrows():
                username = row.get("username", "")
                nationality = row.get("Nationality", "")
                
                # Check if lead already exists in this session
                existing_lead = None
                for i, lead in enumerate(self.leads_storage):
                    if (lead.get('username', '').lower() == username.lower() and 
                        lead.get('session_name', '') == session_name):
                        existing_lead = i
                        break
                
                if existing_lead is not None:
                    # Update existing lead with nationality data
                    self.leads_storage[existing_lead]['nationality'] = nationality
                    self.leads_storage[existing_lead]['last_updated'] = datetime.now().isoformat()
                    updated_count += 1
                    print(f"✅ Updated existing lead {username} with nationality: {nationality}")
                    
                    # Also update in Supabase
                    if self.supabase_connected:
                        try:
                            self.supabase.table("leads").update({
                                "nationality": nationality,
                                "last_updated": datetime.now().isoformat()
                            }).eq("username", username).eq("session_name", session_name).execute()
                            print(f"💾 Updated lead {username} nationality in Supabase")
                        except Exception as update_error:
                            print(f"⚠️ Warning: Could not update lead in Supabase: {update_error}")
                else:
                    # Create new lead record
                    lead_record = {
                        "id": f"lead_{int(time.time())}_{username}",
                        "username": username,
                        "full_name": row.get("full_name", ""),
                        "followers_count": int(row.get("followers_count", 0)),
                        "following_count": int(row.get("following_count", 0)),
                        "posts_count": int(row.get("posts_count", 0)),
                        "is_verified": False,  # Default value
                        "profile_pic_url": "",  # Default value
                        "nationality": nationality,
                        "session_name": session_name or f"Nationality Classification - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                        "scraped_at": row.get("Detection_Date", datetime.now().isoformat()),
                        "created_at": datetime.now().isoformat()
                    }
                    leads_data.append(lead_record)
                    new_count += 1
            
            # Add new leads to storage
            if leads_data:
                self.leads_storage.extend(leads_data)
                
                # Also save to Supabase for persistence
                if self.supabase_connected:
                    try:
                        # Save leads to Supabase
                        for lead in leads_data:
                            lead_data = [{
                                "username": lead["username"],
                                "full_name": lead["full_name"],
                                "followers_count": lead["followers_count"],
                                "following_count": lead["following_count"],
                                "posts_count": lead["posts_count"],
                                "is_verified": lead["is_verified"],
                                "profile_pic_url": lead["profile_pic_url"],
                    "nationality": lead["nationality"],
                    "session_name": lead["session_name"],
                                "scraped_at": lead["scraped_at"],
                                "created_at": lead["created_at"]
                            }]
                            self.save_to_database("leads", lead_data)
                        
                        print(f"💾 Saved {len(leads_data)} leads to Supabase for persistence")
                    except Exception as e:
                        print(f"⚠️ Warning: Could not save leads to Supabase: {e}")
            
            # Update or create session
            session_exists = False
            for session in self.sessions_storage:
                if session['name'] == session_name:
                    session['lead_count'] = len([l for l in self.leads_storage if l.get('session_name') == session_name])
                    session['last_updated'] = datetime.now().isoformat()
                    session_exists = True
                    break
            
            if not session_exists:
                new_session = {
                    "id": f"session_{int(time.time())}",
                    "name": session_name,
                    "lead_count": len(leads_data),
                    "created_at": datetime.now().isoformat(),
                    "last_updated": datetime.now().isoformat()
                }
                self.sessions_storage.append(new_session)
                
                # Also save session to Supabase for persistence
                if self.supabase_connected:
                    try:
                        session_data = [{
                            "session_id": new_session["id"],
                            "session_name": new_session["name"],
                            "lead_count": new_session["lead_count"],
                            "created_at": new_session["created_at"],
                            "last_updated": new_session["last_updated"]
                        }]
                        self.save_to_database("sessions", session_data)
                        print(f"💾 Saved session '{session_name}' to Supabase for persistence")
                    except Exception as e:
                        print(f"⚠️ Warning: Could not save session to Supabase: {e}")
            
            print(f"📊 Updated {updated_count} existing leads, added {new_count} new leads")
            print(f"📊 Total leads in storage: {len(self.leads_storage)}")
            print(f"📊 Total sessions in storage: {len(self.sessions_storage)}")
            return leads_data
            
        except Exception as e:
            print(f"❌ Error preparing nationality data: {str(e)}")
            return []
    
    def _load_data_from_supabase(self):
        """Load existing data from Supabase on startup"""
        if not self.supabase_connected:
            print("⚠️ Supabase not connected, skipping data load")
            return
        
        try:
            print("🔄 Loading existing data from Supabase...")
            
            # First, try to merge data from instagram_profiles and nationality_classifications
            self._merge_profile_and_nationality_data()
            
            # Load leads from Supabase
            leads_result = self.supabase.table("leads").select("*").execute()
            if leads_result.data:
                self.leads_storage = leads_result.data
                print(f"✅ Loaded {len(self.leads_storage)} leads from Supabase")
            else:
                print("📝 No existing leads found in Supabase")
            
            # Load sessions from Supabase
            sessions_result = self.supabase.table("sessions").select("*").execute()
            if sessions_result.data:
                self.sessions_storage = sessions_result.data
                print(f"✅ Loaded {len(self.sessions_storage)} sessions from Supabase")
            else:
                print("📝 No existing sessions found in Supabase")
            
            # Load Instagram accounts from Supabase
            accounts_result = self.supabase.table("instagram_accounts").select("*").execute()
            if accounts_result.data:
                self.instagram_accounts = accounts_result.data
                print(f"✅ Loaded {len(self.instagram_accounts)} Instagram accounts from Supabase")
            else:
                print("📝 No existing Instagram accounts found in Supabase")
                
        except Exception as e:
            print(f"⚠️ Warning: Could not load data from Supabase: {e}")
            print("📝 Starting with empty storage")
    
    def _merge_profile_and_nationality_data(self):
        """Move data from instagram_profiles table directly to leads table"""
        if not self.supabase_connected:
            return
        
        try:
            print("🔄 Moving profile data directly to leads table...")
            
            # Check if instagram_profiles table exists and has data
            try:
                profiles_result = self.supabase.table("instagram_profiles").select("*").limit(1).execute()
                if not profiles_result.data:
                    print("📝 No instagram_profiles data found, skipping merge")
                    return
            except Exception:
                print("📝 instagram_profiles table not found, skipping merge")
                return
            
            # Get all profiles
            profiles_result = self.supabase.table("instagram_profiles").select("*").execute()
            profiles = profiles_result.data if profiles_result.data else []
            
            print(f"📊 Found {len(profiles)} profiles to move to leads table")
            
            # Move data directly to leads table
            moved_data = []
            for profile in profiles:
                username = profile.get('username', '')
                
                # Safe type conversions
                def safe_int(value, default=0):
                    try:
                        if value is None:
                            return default
                        # Handle string numbers like "0.0"
                        if isinstance(value, str):
                            # Remove decimal part for integer fields
                            if '.' in value:
                                return int(float(value))
                            return int(value)
                        return int(value)
                    except (ValueError, TypeError):
                        return default
                
                def safe_bool(value, default=False):
                    try:
                        return bool(value) if value is not None else default
                    except (ValueError, TypeError):
                        return default
                
                lead_data = {
                    'id': f"lead_{profile.get('id', int(time.time()))}",
                    'username': username,
                    'full_name': profile.get('full_name', ''),
                    'biography': profile.get('biography', ''),  # Use biography instead of bio
                    'followers_count': safe_int(profile.get('followers_count', 0)),
                    'following_count': safe_int(profile.get('following_count', 0)),
                    'posts_count': safe_int(profile.get('posts_count', 0)),
                    'is_verified': safe_bool(profile.get('is_verified', False)),
                    'profile_pic_url': profile.get('profile_pic_url', ''),
                    'nationality': 'UNKNOWN',  # Default nationality, will be updated later
                    'confidence': 0.0,  # Default confidence, will be updated later
                    'session_name': profile.get('session_id', 'unknown_session'),
                    'scraped_at': profile.get('scraped_at', datetime.now().isoformat()),
                    'created_at': datetime.now().isoformat(),
                    'last_updated': datetime.now().isoformat()
                }
                moved_data.append(lead_data)
            
            # Insert data into leads table
            if moved_data:
                # Use upsert to avoid duplicates
                for lead in moved_data:
                    try:
                        # Check if lead already exists
                        existing = self.supabase.table("leads").select("id").eq("username", lead['username']).execute()
                        
                        if existing.data:
                            # Update existing lead
                            self.supabase.table("leads").update({
                                'full_name': lead['full_name'],
                                'biography': lead['biography'],
                                'followers_count': lead['followers_count'],
                                'following_count': lead['following_count'],
                                'posts_count': lead['posts_count'],
                                'is_verified': lead['is_verified'],
                                'profile_pic_url': lead['profile_pic_url'],
                                'session_name': lead['session_name'],
                                'scraped_at': lead['scraped_at'],
                                'last_updated': lead['last_updated']
                            }).eq("username", lead['username']).execute()
                        else:
                            # Insert new lead
                            self.supabase.table("leads").insert(lead).execute()
                    except Exception as e:
                        print(f"⚠️ Warning: Could not upsert lead {lead['username']}: {e}")
                
                print(f"✅ Moved {len(moved_data)} profiles to leads table")
                print("📝 Nationality classification will be done directly on leads table")
            
        except Exception as e:
            print(f"⚠️ Warning: Could not move profile data to leads table: {e}")
    
    def _create_tables_if_not_exist(self):
        """Create necessary tables in Supabase if they don't exist"""
        if not self.supabase_connected:
            print("⚠️ Supabase not connected, skipping table creation")
            return
        
        try:
            print("🔧 Creating tables in Supabase...")
            
            # Create leads table
            leads_sql = """
            CREATE TABLE IF NOT EXISTS leads (
                id SERIAL PRIMARY KEY,
                username VARCHAR(255) NOT NULL,
                full_name VARCHAR(255),
                followers_count INTEGER DEFAULT 0,
                following_count INTEGER DEFAULT 0,
                posts_count INTEGER DEFAULT 0,
                is_verified BOOLEAN DEFAULT FALSE,
                profile_pic_url TEXT,
                nationality VARCHAR(255),
                session_name VARCHAR(255),
                scraped_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT NOW(),
                last_updated TIMESTAMP DEFAULT NOW()
            );
            """
            
            # Create sessions table
            sessions_sql = """
            CREATE TABLE IF NOT EXISTS sessions (
                id SERIAL PRIMARY KEY,
                session_id VARCHAR(255) UNIQUE NOT NULL,
                session_name VARCHAR(255) NOT NULL,
                lead_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT NOW(),
                last_updated TIMESTAMP DEFAULT NOW()
            );
            """
            
            # Create Instagram accounts table
            accounts_sql = """
            CREATE TABLE IF NOT EXISTS instagram_accounts (
                id VARCHAR(255) PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                display_name VARCHAR(255),
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT NOW(),
                last_updated TIMESTAMP DEFAULT NOW()
            );
            """
            
            # Execute SQL commands
            try:
                self.supabase.rpc('exec_sql', {'sql': leads_sql}).execute()
                print("✅ Leads table created")
            except Exception as e:
                print(f"⚠️ Leads table creation failed: {e}")
            
            try:
                self.supabase.rpc('exec_sql', {'sql': sessions_sql}).execute()
                print("✅ Sessions table created")
            except Exception as e:
                print(f"⚠️ Sessions table creation failed: {e}")
            
            try:
                self.supabase.rpc('exec_sql', {'sql': accounts_sql}).execute()
                print("✅ Instagram accounts table created")
            except Exception as e:
                print(f"⚠️ Instagram accounts table creation failed: {e}")
                print("📝 Please create the table manually in Supabase Dashboard")
                print("SQL: CREATE TABLE instagram_accounts (id VARCHAR(255) PRIMARY KEY, username VARCHAR(255) UNIQUE NOT NULL, password VARCHAR(255) NOT NULL, display_name VARCHAR(255), is_active BOOLEAN DEFAULT true, created_at TIMESTAMP DEFAULT NOW(), last_updated TIMESTAMP DEFAULT NOW());")
            
            print("✅ Table creation process completed")
            
        except Exception as e:
            print(f"⚠️ Warning: Could not create tables: {e}")
            print("📝 You may need to create tables manually in Supabase Dashboard")
            print("📝 SQL Commands to run manually:")
            print("""
            -- Create leads table
            CREATE TABLE IF NOT EXISTS leads (
                id SERIAL PRIMARY KEY,
                username VARCHAR(255) NOT NULL,
                full_name VARCHAR(255),
                followers_count INTEGER DEFAULT 0,
                following_count INTEGER DEFAULT 0,
                posts_count INTEGER DEFAULT 0,
                is_verified BOOLEAN DEFAULT FALSE,
                profile_pic_url TEXT,
                nationality VARCHAR(255),
                session_name VARCHAR(255),
                scraped_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT NOW(),
                last_updated TIMESTAMP DEFAULT NOW()
            );
            
            -- Create sessions table
            CREATE TABLE IF NOT EXISTS sessions (
                id SERIAL PRIMARY KEY,
                session_id VARCHAR(255) UNIQUE NOT NULL,
                session_name VARCHAR(255) NOT NULL,
                lead_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT NOW(),
                last_updated TIMESTAMP DEFAULT NOW()
            );
            """)
    
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
    
    def _ensure_warp_running(self):
        """
        Cloudflare WARP'ın çalıştığından emin ol
        WARP çalışmıyorsa başlatır
        """
        import subprocess
        import time
        
        try:
            # WARP durumunu kontrol et
            result = subprocess.run(
                ['warp-cli', 'status'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if 'Connected' in result.stdout:
                print("✅ Cloudflare WARP is already connected")
                return True
            else:
                print("⚠️ Cloudflare WARP is not connected, attempting to connect...")
                
                # WARP'ı bağla (register gerekebilir)
                try:
                    # Önce register et (ilk kurulum için)
                    subprocess.run(
                        ['warp-cli', 'register'],
                        capture_output=True,
                        timeout=10
                    )
                except:
                    pass  # Zaten kayıtlı olabilir
                
                # WARP'ı bağla
                connect_result = subprocess.run(
                    ['warp-cli', 'connect'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                # Bağlantıyı bekle
                time.sleep(3)
                
                # Tekrar kontrol et
                status_result = subprocess.run(
                    ['warp-cli', 'status'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if 'Connected' in status_result.stdout:
                    print("✅ Cloudflare WARP connected successfully")
                    return True
                else:
                    print(f"⚠️ Cloudflare WARP connection failed: {status_result.stdout}")
                    return False
                    
        except FileNotFoundError:
            print("⚠️ warp-cli not found. WARP may not be installed.")
            return False
        except Exception as e:
            print(f"⚠️ Error checking/starting WARP: {str(e)}")
            return False

    def selenium_location_scraper(self, ig_user, ig_pass, location_urls, max_profiles=200, use_warp=False, user_proxy=None):
        """
        More robust Selenium-based scraper with better page detection and multiple fallback strategies
        
        Args:
            ig_user: Instagram username
            ig_pass: Instagram password
            location_urls: List of location URLs to scrape
            max_profiles: Maximum number of profiles to scrape per location
            use_warp: If True, use Cloudflare WARP proxy (SOCKS5 on 127.0.0.1:40000)
            user_proxy: User's SOCKS5 proxy (e.g., "socks5://KULLANICI_IP:1080") - Uses user's IP
        """
        import sys
        
        # WARP kullanılacaksa, WARP'ın çalıştığından emin ol
        if use_warp:
            warp_ready = self._ensure_warp_running()
            if not warp_ready:
                print("⚠️ WARP is not available, falling back to direct connection")
                use_warp = False
        print(f"🚀 selenium_location_scraper called", flush=True)
        print(f"📋 Parameters: ig_user={ig_user}, max_profiles={max_profiles}", flush=True)
        print(f"📋 Location URLs: {location_urls}", flush=True)
        sys.stdout.flush()
        
        try:
            print("📦 Importing Selenium modules...", flush=True)
            from selenium import webdriver
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.chrome.options import Options
            from selenium.common.exceptions import TimeoutException, NoSuchElementException
            import time
            print("✅ Selenium modules imported successfully", flush=True)
            sys.stdout.flush()
        except ImportError as import_error:
            print(f"❌ Selenium import failed: {import_error}", flush=True)
            sys.stdout.flush()
            raise Exception("Selenium not installed. Run: pip install selenium")
        
        chrome_options = Options()
        chrome_options.add_argument("--headless")        
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        
        # Updated User-Agent to match Chrome version (142)
        chrome_options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36")
        
        # Additional anti-detection arguments
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--disable-features=IsolateOrigins,site-per-process")
        chrome_options.add_argument("--disable-site-isolation-trials")
        chrome_options.add_argument("--lang=en-US,en")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--start-maximized")
        
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Add preferences to make browser look more like a real user
        prefs = {
            "profile.default_content_setting_values": {
                "notifications": 2,
                "geolocation": 2,
            },
            "profile.managed_default_content_settings": {
                "images": 1
            }
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        # Proxy desteği: Önce user_proxy, sonra WARP
        if user_proxy:
            print(f"🌐 Using proxy: {user_proxy}")
            # Proxy formatını kontrol et ve düzenle
            proxy_url = user_proxy
            
            # HTTP/HTTPS proxy için
            if user_proxy.startswith("http://") or user_proxy.startswith("https://"):
                chrome_options.add_argument(f"--proxy-server={proxy_url}")
            # SOCKS5 proxy için
            elif user_proxy.startswith("socks5://"):
                chrome_options.add_argument(f"--proxy-server={proxy_url}")
                # SOCKS5 proxy için DNS çözümleme
                # Format: socks5://username:password@host:port veya socks5://host:port
                if "@" in proxy_url:
                    proxy_host = proxy_url.split("@")[1].split(":")[0]
                else:
                    proxy_host = proxy_url.replace("socks5://", "").split(":")[0]
                chrome_options.add_argument(f"--host-resolver-rules=MAP * ~NOTFOUND , EXCLUDE {proxy_host}")
            else:
                # Varsayılan olarak HTTP proxy olarak kabul et
                chrome_options.add_argument(f"--proxy-server=http://{proxy_url}")
            
            # Proxy authentication notu:
            # Chrome, proxy URL'inde username:password formatını desteklemez
            # Çözüm 1: Proxynetic IP whitelist kullanın (VPS IP'sini whitelist'e ekleyin)
            # Çözüm 2: Proxy extension kullanın (proxy_auth_extension klasöründe)
            # Çözüm 3: VPS'te proxy chain kullanın (3proxy gibi)
            
            # Eğer proxy URL'inde @ varsa (username:password formatı), uyarı ver
            if "@" in proxy_url:
                print("⚠️ Proxy authentication detected in URL")
                print("⚠️ Chrome doesn't support username:password in proxy URL")
                print("💡 Solution: Use IP whitelist in Proxynetic dashboard (add VPS IP)")
                print("💡 Or: Use proxy extension (see proxy_auth_extension folder)")
                # URL'den authentication bilgisini çıkar, sadece host:port kullan
                # Kullanıcı IP whitelist kullanmalı
                if "socks5://" in proxy_url:
                    proxy_parts = proxy_url.replace("socks5://", "").split("@")
                    if len(proxy_parts) > 1:
                        proxy_host_port = proxy_parts[1]
                        print(f"⚠️ Using proxy without auth: socks5://{proxy_host_port}")
                        print("⚠️ Make sure to whitelist VPS IP in Proxynetic dashboard!")
                        chrome_options.add_argument(f"--proxy-server=socks5://{proxy_host_port}")
                elif "http://" in proxy_url or "https://" in proxy_url:
                    proxy_parts = proxy_url.split("://")[1].split("@")
                    if len(proxy_parts) > 1:
                        proxy_host_port = proxy_parts[1]
                        protocol = "http://" if "http://" in proxy_url else "https://"
                        print(f"⚠️ Using proxy without auth: {protocol}{proxy_host_port}")
                        print("💡 Tip: If using Bright Data, make sure 3proxy is running on VPS")
                        print("💡 Tip: If using Proxynetic, whitelist VPS IP in dashboard")
                        chrome_options.add_argument(f"--proxy-server={protocol}{proxy_host_port}")
                    else:
                        # No authentication in URL, use as-is (e.g., http://localhost:3128 for 3proxy)
                        print(f"✅ Using proxy: {proxy_url}")
                        chrome_options.add_argument(f"--proxy-server={proxy_url}")
        elif use_warp:
            print("🌐 Using Cloudflare WARP proxy (SOCKS5://127.0.0.1:40000)")
            chrome_options.add_argument("--proxy-server=socks5://127.0.0.1:40000")
            # WARP için ek ayarlar
            chrome_options.add_argument("--host-resolver-rules=MAP * ~NOTFOUND , EXCLUDE 127.0.0.1")
        else:
            print("🌐 Using direct connection (no proxy)")
        
        driver = None
        try:
            print("🔧 Initializing Chrome driver...", flush=True)
            sys.stdout.flush()
            try:
                driver = webdriver.Chrome(options=chrome_options)
                print("✅ Chrome driver initialized successfully", flush=True)
                sys.stdout.flush()
            except Exception as driver_init_error:
                print(f"❌ Failed to initialize Chrome driver: {str(driver_init_error)}")
                print(f"❌ Error type: {type(driver_init_error).__name__}")
                raise Exception(f"Chrome driver initialization failed: {str(driver_init_error)}")
            
            # Check Chrome and ChromeDriver versions
            try:
                chrome_version = driver.capabilities.get('browserVersion', 'Unknown')
                chromedriver_version = driver.capabilities.get('chrome', {}).get('chromedriverVersion', 'Unknown')
                print(f"🌐 Chrome version: {chrome_version}")
                print(f"🔧 ChromeDriver version: {chromedriver_version}")
            except Exception as version_error:
                print(f"⚠️ Could not get version info: {version_error}")
            
            # Enhanced anti-detection scripts
            print("🔧 Executing enhanced anti-detection scripts...")
            
            # Remove webdriver property
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Override Chrome object
            driver.execute_script("""
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
            """)
            
            # Override languages
            driver.execute_script("""
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en']
                });
            """)
            
            # Override permissions
            driver.execute_script("""
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
            """)
            
            # Override plugins length
            driver.execute_script("""
                Object.defineProperty(navigator, 'plugins', {
                    get: () => {
                        const plugins = [];
                        for (let i = 0; i < 5; i++) {
                            plugins.push({
                                0: { type: 'application/x-google-chrome-pdf', suffixes: 'pdf', description: 'Portable Document Format' },
                                description: 'Portable Document Format',
                                filename: 'internal-pdf-viewer',
                                length: 1,
                                name: 'Chrome PDF Plugin'
                            });
                        }
                        return plugins;
                    }
                });
            """)
            
            print("✅ Enhanced anti-detection scripts executed")
            
            # Login with better error handling
            print("🌐 Navigating to Instagram login page...")
            driver.get("https://www.instagram.com/accounts/login/")
            print(f"✅ Page loaded. Current URL: {driver.current_url}")
            print(f"📄 Page title: {driver.title}")
            
            # Wait a bit for initial page load
            print("⏳ Waiting 3 seconds for initial page load...")
            time.sleep(3)
            
            # Scroll to trigger JavaScript execution
            try:
                print("📜 Scrolling page to trigger JavaScript execution...")
                driver.execute_script("window.scrollTo(0, 100);")
                time.sleep(1)
                driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(1)
                print("✅ Page scrolled")
            except:
                pass
            
            # ========== VERIFY WE'RE ON INSTAGRAM PAGE ==========
            print("\n" + "="*60)
            print("🔍 VERIFYING PAGE IS INSTAGRAM LOGIN PAGE...")
            print("="*60)
            
            # Check if we're actually on Instagram
            current_url = driver.current_url
            page_source = driver.page_source.lower()
            
            is_instagram = False
            if "instagram.com" in current_url.lower():
                is_instagram = True
                print("✅ URL contains 'instagram.com'")
            else:
                print(f"⚠️ URL does not contain 'instagram.com': {current_url}")
            
            # Check page source for Instagram indicators
            instagram_indicators = [
                "instagram",
                "login",
                "username",
                "password",
                "meta property=\"og:site_name\"",
                "react-root",
                "__d",
            ]
            
            found_indicators = []
            for indicator in instagram_indicators:
                if indicator in page_source:
                    count = page_source.count(indicator)
                    found_indicators.append(f"{indicator}: {count} occurrences")
                    print(f"✅ Found '{indicator}' in page source ({count} times)")
                else:
                    print(f"❌ '{indicator}' NOT found in page source")
            
            # Check for error pages
            error_indicators = [
                "this site can't be reached",
                "err_",
                "dns_probe",
                "network error",
                "unable to connect",
                "chrome-error",
                "error code",
            ]
            
            found_errors = []
            for error_indicator in error_indicators:
                if error_indicator in page_source:
                    found_errors.append(error_indicator)
                    print(f"⚠️ ERROR INDICATOR FOUND: '{error_indicator}'")
            
            # Log page source snippet for debugging
            print(f"\n📄 Page source preview (first 3000 chars):")
            print("="*60)
            print(page_source[:3000])
            print("="*60)
            
            # Check if "error code" is actually a real error or just in comments/JS
            # Sometimes "error code" appears in JavaScript comments but page is fine
            if "error code" in page_source:
                # Check if it's in a visible error message
                error_code_context = page_source[max(0, page_source.find("error code")-200):page_source.find("error code")+200]
                print(f"\n🔍 Context around 'error code':")
                print(error_code_context)
                
                # If it's in a script tag or comment, it might be OK
                if "error code" in page_source and ("<script" in error_code_context.lower() or "//" in error_code_context or "/*" in error_code_context):
                    print("⚠️ 'error code' found but appears to be in JavaScript/comment - might be OK")
                    found_errors = [e for e in found_errors if e != "error code"]  # Remove from errors
            
            if found_errors and len(found_errors) > 0:
                print(f"\n❌ PAGE APPEARS TO BE AN ERROR PAGE!")
                print(f"   Found error indicators: {', '.join(found_errors)}")
                print(f"   This is likely a network/connection error or bot detection")
                
                # Try to reload the page once
                print("\n🔄 Attempting to reload the page...")
                try:
                    driver.refresh()
                    time.sleep(5)
                    new_url = driver.current_url
                    new_page_source = driver.page_source.lower()
                    print(f"✅ Page reloaded. New URL: {new_url}")
                    
                    # Check again
                    if "instagram" in new_page_source and "react" in new_page_source:
                        print("✅ After reload: Instagram content detected!")
                        # Continue with the process
                    else:
                        raise Exception(f"Instagram page failed to load even after reload. Error indicators found: {', '.join(found_errors)}")
                except Exception as reload_error:
                    raise Exception(f"Instagram page failed to load. Error indicators found: {', '.join(found_errors)}. Reload attempt failed: {str(reload_error)[:100]}")
            
            # Check if page source looks like Instagram
            if len(page_source) < 1000:
                print(f"⚠️ Page source is very short ({len(page_source)} chars) - might be an error page")
            else:
                print(f"✅ Page source length: {len(page_source)} chars (looks normal)")
            
            # Check for React root (Instagram uses React)
            if "react" in page_source or "__d" in page_source:
                print("✅ React detected - likely Instagram page")
            else:
                print("⚠️ React not detected - might not be Instagram page")
            
            if not is_instagram or len(found_indicators) < 3:
                print(f"\n❌ PAGE VERIFICATION FAILED!")
                print(f"   is_instagram: {is_instagram}")
                print(f"   Found indicators: {len(found_indicators)}")
                raise Exception(f"Page verification failed. Current URL: {current_url}, Found {len(found_indicators)} Instagram indicators")
            
            print("="*60 + "\n")
            # ========== END PAGE VERIFICATION ==========
            
            # Wait for page to fully load
            print("⏳ Waiting for page to fully load...")
            
            # Wait for page ready state
            WebDriverWait(driver, 15).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            print("✅ Page ready state: complete")
            
            # Wait for React to load (Instagram uses React)
            print("⏳ Waiting for React/JavaScript to load...")
            try:
                # Wait for React root element
                WebDriverWait(driver, 20).until(
                    lambda d: d.execute_script("""
                        return typeof window !== 'undefined' && 
                               (document.querySelector('#react-root') !== null || 
                                window.__d !== undefined ||
                                document.body.innerHTML.length > 1000);
                    """)
                )
                print("✅ React/JavaScript loaded")
            except TimeoutException:
                print("⚠️ React root not found after 20 seconds, continuing anyway...")
            
            # Additional wait for React/JavaScript to render
            print("⏳ Waiting additional 3 seconds for dynamic content to render...")
            time.sleep(3)
            
            # ========== DETECT AND LOG POPUPS/MODALS ==========
            print("\n" + "="*60)
            print("🔍 CHECKING FOR POPUPS/MODALS ON PAGE...")
            print("="*60)
            
            # Check for common popup/modal indicators
            popup_indicators = [
                (By.XPATH, "//div[contains(@role, 'dialog')]"),
                (By.XPATH, "//div[contains(@class, 'modal')]"),
                (By.XPATH, "//div[contains(@class, 'popup')]"),
                (By.XPATH, "//div[contains(@class, 'overlay')]"),
                (By.XPATH, "//div[contains(@aria-label, 'dialog')]"),
                (By.CSS_SELECTOR, "[role='dialog']"),
                (By.CSS_SELECTOR, "[role='alertdialog']"),
            ]
            
            found_popups = []
            for indicator_type, indicator_value in popup_indicators:
                try:
                    popups = driver.find_elements(indicator_type, indicator_value)
                    if popups:
                        for popup in popups:
                            try:
                                is_displayed = popup.is_displayed()
                                text = popup.text[:200] if popup.text else "No text"
                                tag = popup.tag_name
                                popup_id = popup.get_attribute("id") or "no-id"
                                popup_class = popup.get_attribute("class") or "no-class"
                                found_popups.append({
                                    "type": indicator_value,
                                    "displayed": is_displayed,
                                    "text": text,
                                    "tag": tag,
                                    "id": popup_id,
                                    "class": popup_class[:100]
                                })
                            except:
                                pass
                except:
                    pass
            
            if found_popups:
                print(f"⚠️ Found {len(found_popups)} potential popup/modal elements:")
                for i, popup in enumerate(found_popups, 1):
                    print(f"  [{i}] Type: {popup['type']}")
                    print(f"      Displayed: {popup['displayed']}")
                    print(f"      Tag: {popup['tag']}, ID: {popup['id']}")
                    print(f"      Class: {popup['class']}")
                    print(f"      Text: {popup['text'][:150]}...")
            else:
                print("✅ No popup/modal elements detected")
            
            # Check for common popup button texts
            print("\n🔍 Checking for common popup buttons...")
            common_button_texts = [
                "Accept", "Accept All", "Allow", "Allow All",
                "Decline", "Reject", "Not Now", "Not Now, Thanks",
                "Save", "Save Info", "Don't Save",
                "Turn on", "Turn on Notifications", "Not Now",
                "Get App", "Not Now", "Maybe Later",
                "Cookies", "Cookie", "Privacy", "Terms"
            ]
            
            all_buttons = driver.find_elements(By.TAG_NAME, "button")
            all_divs_clickable = driver.find_elements(By.XPATH, "//div[@role='button']")
            all_clickable = list(all_buttons) + list(all_divs_clickable)
            
            print(f"📊 Found {len(all_clickable)} clickable elements (buttons + divs with role='button')")
            
            popup_buttons = []
            for btn in all_clickable[:50]:  # Check first 50 to avoid too much output
                try:
                    if btn.is_displayed():
                        btn_text = btn.text.strip()
                        btn_aria_label = btn.get_attribute("aria-label") or ""
                        btn_type = btn.get_attribute("type") or ""
                        
                        # Check if button text matches common popup patterns
                        for pattern in common_button_texts:
                            if pattern.lower() in btn_text.lower() or pattern.lower() in btn_aria_label.lower():
                                popup_buttons.append({
                                    "text": btn_text[:100],
                                    "aria_label": btn_aria_label[:100],
                                    "type": btn_type,
                                    "tag": btn.tag_name
                                })
                                break
                except:
                    pass
            
            if popup_buttons:
                print(f"⚠️ Found {len(popup_buttons)} potential popup buttons:")
                for i, btn in enumerate(popup_buttons, 1):
                    print(f"  [{i}] Text: '{btn['text']}'")
                    print(f"      Aria-label: '{btn['aria_label']}'")
                    print(f"      Type: {btn['type']}, Tag: {btn['tag']}")
            else:
                print("✅ No obvious popup buttons found")
            
            # List all visible buttons for debugging
            print(f"\n📋 All visible buttons on page (first 20):")
            visible_buttons = []
            for btn in all_clickable[:20]:
                try:
                    if btn.is_displayed():
                        btn_text = btn.text.strip()[:50]
                        btn_aria = (btn.get_attribute("aria-label") or "")[:50]
                        visible_buttons.append(f"Text: '{btn_text}' | Aria: '{btn_aria}'")
                except:
                    pass
            
            for i, btn_info in enumerate(visible_buttons, 1):
                print(f"  [{i}] {btn_info}")
            
            # Check page source for popup-related keywords
            print("\n🔍 Checking page source for popup-related keywords...")
            page_source_lower = driver.page_source.lower()
            popup_keywords = ["cookie", "consent", "privacy", "notification", "age", "verify", "save login", "turn on"]
            found_keywords = []
            for keyword in popup_keywords:
                if keyword in page_source_lower:
                    count = page_source_lower.count(keyword)
                    found_keywords.append(f"{keyword}: {count} occurrences")
            
            if found_keywords:
                print("⚠️ Found popup-related keywords in page source:")
                for kw in found_keywords:
                    print(f"  - {kw}")
            else:
                print("✅ No popup-related keywords found")
            
            # Try to take a screenshot (works in headless too)
            try:
                screenshot_path = "/tmp/instagram_login_page.png"
                driver.save_screenshot(screenshot_path)
                print(f"📸 Screenshot saved to {screenshot_path}")
            except Exception as screenshot_error:
                print(f"⚠️ Could not take screenshot: {screenshot_error}")
            
            print("="*60 + "\n")
            # ========== END POPUP DETECTION ==========
            
            # ========== ATTEMPT TO CLOSE POPUPS ==========
            print("🔧 Attempting to close any popups...")
            popup_closed = False
            
            # Common popup close button selectors
            close_selectors = [
                (By.XPATH, "//button[contains(text(), 'Not Now')]"),
                (By.XPATH, "//button[contains(text(), 'Not now')]"),
                (By.XPATH, "//button[contains(text(), 'Decline')]"),
                (By.XPATH, "//button[contains(text(), 'Reject')]"),
                (By.XPATH, "//button[contains(text(), 'Maybe Later')]"),
                (By.XPATH, "//div[contains(text(), 'Not Now')]"),
                (By.XPATH, "//div[@role='button' and contains(text(), 'Not Now')]"),
                (By.XPATH, "//button[@aria-label='Close']"),
                (By.XPATH, "//button[@aria-label='Not Now']"),
                (By.XPATH, "//svg[@aria-label='Close']/ancestor::button"),
                (By.XPATH, "//button[contains(@class, 'close')]"),
                (By.XPATH, "//button[contains(@class, 'dismiss')]"),
                (By.CSS_SELECTOR, "button[aria-label*='Close']"),
                (By.CSS_SELECTOR, "button[aria-label*='Not Now']"),
                (By.CSS_SELECTOR, "svg[aria-label='Close']"),
            ]
            
            for selector_type, selector_value in close_selectors:
                try:
                    close_buttons = driver.find_elements(selector_type, selector_value)
                    for btn in close_buttons:
                        try:
                            if btn.is_displayed():
                                btn_text = btn.text.strip()[:50]
                                print(f"  🎯 Found close button: '{btn_text}' - Clicking...")
                                btn.click()
                                time.sleep(1)
                                popup_closed = True
                                print(f"  ✅ Clicked close button: '{btn_text}'")
                        except Exception as click_error:
                            print(f"  ⚠️ Could not click button: {str(click_error)[:50]}")
                            continue
                except Exception as selector_error:
                    continue
            
            # Try pressing Escape key to close modals
            if not popup_closed:
                try:
                    from selenium.webdriver.common.keys import Keys
                    print("  ⌨️ Trying Escape key to close popup...")
                    driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
                    time.sleep(1)
                    print("  ✅ Pressed Escape key")
                except:
                    pass
            
            if popup_closed:
                print("✅ Popup closed successfully")
            else:
                print("ℹ️ No popup close buttons found or popup already closed")
            
            # Wait a bit after closing popup
            if popup_closed:
                time.sleep(2)
                print("⏳ Waiting 2 seconds after popup close...")
            
            print("="*60 + "\n")
            # ========== END POPUP CLOSING ==========
            
            # Wait for at least one input element to appear (indicates form is loaded)
            print("⏳ Waiting for login form to render...")
            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.TAG_NAME, "input"))
                )
                print("✅ Input elements detected on page")
            except TimeoutException:
                print("⚠️ No input elements found after 15 seconds, continuing anyway...")
            
            # Check page ready state
            ready_state = driver.execute_script("return document.readyState")
            print(f"📊 Page ready state: {ready_state}")
            
            try:
                # Wait for login form - try both username and email fields
                print("🔍 Looking for username/email field...")
                username_field = None
                password_field = None
                
                # Try multiple selectors for username field
                username_selectors = [
                    (By.NAME, "username"),
                    (By.NAME, "email"),
                    (By.CSS_SELECTOR, "input[name='username']"),
                    (By.CSS_SELECTOR, "input[name='email']"),
                    (By.XPATH, "//input[@name='username']"),
                    (By.XPATH, "//input[@name='email']"),
                    (By.XPATH, "//input[@aria-label[contains(., 'kullanıcı adı') or contains(., 'username') or contains(., 'e-posta') or contains(., 'email') or contains(., 'Telefon')]]"),
                    (By.CSS_SELECTOR, "input[aria-label*='kullanıcı adı'], input[aria-label*='username'], input[aria-label*='e-posta'], input[aria-label*='email'], input[aria-label*='Telefon']"),
                    (By.XPATH, "//input[@type='text' and (@name='username' or @name='email')]"),
                    (By.CSS_SELECTOR, "input[aria-label*='Telefon numarası']"),
                    (By.XPATH, "//input[@aria-label[contains(., 'Telefon numarası')]]"),
                ]
                
                for selector_type, selector_value in username_selectors:
                    try:
                        print(f"   Trying username selector: {selector_value}")
                        # Use visibility_of_element_located instead of presence_of_element_located
                        # This ensures the element is not only in DOM but also visible
                        username_field = WebDriverWait(driver, 10).until(
                            EC.visibility_of_element_located((selector_type, selector_value))
                        )
                        print(f"✅ Username field found with selector: {selector_value}!")
                        break
                    except TimeoutException:
                        continue
                    except Exception as e:
                        print(f"   Selector {selector_value} failed: {str(e)[:50]}")
                        continue
                
                if username_field is None:
                    # Debug: Get page info before raising error
                    try:
                        # Wait a bit more and try again
                        print("⏳ Waiting additional 3 seconds for page to fully render...")
                        time.sleep(3)
                        
                        all_inputs = driver.find_elements(By.TAG_NAME, "input")
                        print(f"📊 Found {len(all_inputs)} total input elements on page")
                        
                        input_info = []
                        for i, inp in enumerate(all_inputs[:15]):
                            try:
                                name_attr = inp.get_attribute("name")
                                type_attr = inp.get_attribute("type")
                                aria_label = inp.get_attribute("aria-label")
                                class_attr = inp.get_attribute("class")
                                is_displayed = inp.is_displayed()
                                input_info.append(f"[{i}] name={name_attr}, type={type_attr}, aria-label={aria_label}, displayed={is_displayed}, class={class_attr[:30] if class_attr else 'None'}")
                            except Exception as inp_e:
                                input_info.append(f"[{i}] Error getting attributes: {str(inp_e)[:50]}")
                        
                        # Get page source snippet for debugging
                        page_source_full = driver.page_source
                        page_source_length = len(page_source_full)
                        print(f"📄 Full page source length: {page_source_length} characters")
                        
                        # Show first 5000 chars if available
                        page_source_snippet = page_source_full[:5000] if page_source_length > 5000 else page_source_full
                        print(f"📄 Page source snippet (first 5000 chars):\n{page_source_snippet}")
                        
                        # Check if this looks like an error page
                        page_source_lower = page_source_full.lower()
                        if "chrome-error" in page_source_lower or "err_" in page_source_lower or "this site can't be reached" in page_source_lower:
                            print("❌ PAGE APPEARS TO BE A CHROME ERROR PAGE!")
                            print("   This means Instagram failed to load or blocked the request")
                            raise Exception("Instagram page failed to load - Chrome error page detected. This could be due to bot detection, network issues, or IP blocking.")
                        
                        # Check for Instagram-specific content
                        if "instagram" not in page_source_lower[:10000]:
                            print("⚠️ WARNING: 'instagram' keyword not found in first 10000 chars of page source")
                            print("   This might not be the Instagram login page")
                        
                        # Show body content if available
                        try:
                            body_element = driver.find_element(By.TAG_NAME, "body")
                            body_text = body_element.text[:500] if body_element.text else "No text"
                            print(f"📝 Body text (first 500 chars): {body_text}")
                        except:
                            print("⚠️ Could not get body text")
                        
                        error_msg = f"Username/email field not found. Found {len(all_inputs)} input elements. Page source length: {page_source_length} chars. First 15 inputs:\n" + "\n".join(input_info)
                        print(f"❌ {error_msg}")
                        raise Exception(error_msg)
                    except Exception as debug_e:
                        raise Exception(f"Username/email field not found. Debug error: {str(debug_e)}")
                
                # Try multiple selectors for password field
                print("🔍 Looking for password field...")
                password_selectors = [
                    (By.NAME, "password"),
                    (By.NAME, "pass"),
                    (By.CSS_SELECTOR, "input[name='password']"),
                    (By.CSS_SELECTOR, "input[name='pass']"),
                    (By.XPATH, "//input[@name='password']"),
                    (By.XPATH, "//input[@name='pass']"),
                    (By.XPATH, "//input[@type='password']"),
                ]
                
                for selector_type, selector_value in password_selectors:
                    try:
                        print(f"   Trying password selector: {selector_value}")
                        # Use visibility_of_element_located to ensure element is visible
                        password_field = WebDriverWait(driver, 10).until(
                            EC.visibility_of_element_located((selector_type, selector_value))
                        )
                        print(f"✅ Password field found with selector: {selector_value}!")
                        break
                    except TimeoutException:
                        continue
                    except Exception as e:
                        print(f"   Password selector {selector_value} failed: {str(e)[:50]}")
                        continue
                
                if password_field is None:
                    raise Exception("Password field not found")
                
                # Fill credentials
                print("📝 Filling login credentials...")
                
                username_field.clear()
                username_field.send_keys(ig_user)
                time.sleep(1)
                
                password_field.clear()
                password_field.send_keys(ig_pass)
                time.sleep(1)
                
                # Submit login - try multiple selectors for button/div
                print("🔍 Looking for login button...")
                login_button = None
                login_selectors = [
                    (By.XPATH, "//button[@type='submit']"),
                    (By.XPATH, "//div[contains(text(), 'Log in')]"),
                    (By.XPATH, "//div[contains(text(), 'Log In')]"),
                    (By.XPATH, "//button[contains(text(), 'Log in')]"),
                    (By.XPATH, "//button[contains(text(), 'Log In')]"),
                ]
                
                for i, (selector_type, selector_value) in enumerate(login_selectors, 1):
                    try:
                        print(f"   Trying selector {i}/{len(login_selectors)}: {selector_value}")
                        login_button = driver.find_element(selector_type, selector_value)
                        print(f"✅ Login button found with selector {i}!")
                        break
                    except Exception as e:
                        print(f"   ❌ Selector {i} failed: {str(e)[:50]}")
                        continue
                
                if login_button is None:
                    # Debug: Save page source for analysis
                    try:
                        page_source = driver.page_source
                        print(f"⚠️ Page source length: {len(page_source)} characters")
                        print(f"⚠️ Current URL: {driver.current_url}")
                        print(f"⚠️ Page title: {driver.title}")
                        # Try to find any button or div with text containing "log"
                        try:
                            all_buttons = driver.find_elements(By.TAG_NAME, "button")
                            all_divs = driver.find_elements(By.TAG_NAME, "div")
                            print(f"⚠️ Found {len(all_buttons)} buttons and {len(all_divs)} divs on page")
                        except:
                            pass
                    except Exception as debug_error:
                        print(f"⚠️ Could not get debug info: {debug_error}")
                    raise Exception("Login button not found - Instagram may have changed")
                
                print("🖱️ Clicking login button...")
                login_button.click()
                print("✅ Login button clicked")
                
                print("⏳ Waiting for login to process (10 seconds)...")
                time.sleep(10)
                
                # Check if login was successful
                current_url = driver.current_url
                print(f"📊 After login, current URL: {current_url}")
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
                
            except TimeoutException as e:
                print(f"❌ TimeoutException: {str(e)}")
                print(f"❌ Current URL: {driver.current_url}")
                print(f"❌ Page title: {driver.title}")
                try:
                    # Try to get page source for debugging
                    page_source_length = len(driver.page_source)
                    print(f"❌ Page source length: {page_source_length} characters")
                    
                    # Check if page loaded at all
                    ready_state = driver.execute_script("return document.readyState")
                    print(f"❌ Page ready state: {ready_state}")
                    
                    # Try to find any input fields
                    all_inputs = driver.find_elements(By.TAG_NAME, "input")
                    print(f"❌ Found {len(all_inputs)} input elements on page")
                    for inp in all_inputs[:5]:  # Show first 5 inputs
                        try:
                            name_attr = inp.get_attribute("name")
                            type_attr = inp.get_attribute("type")
                            print(f"   Input: name={name_attr}, type={type_attr}")
                        except:
                            pass
                except Exception as debug_error:
                    print(f"❌ Could not get debug info: {debug_error}")
                
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
            print("🔒 Closing Chrome driver...")
            driver.quit()
            print("✅ Chrome driver closed successfully")
            
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
            import sys
            error_type = type(e).__name__
            error_msg = str(e)
            print(f"❌ Critical error occurred!", flush=True)
            print(f"❌ Error type: {error_type}", flush=True)
            print(f"❌ Error message: {error_msg}", flush=True)
            import traceback
            print(f"❌ Full traceback:", flush=True)
            traceback.print_exc()
            sys.stdout.flush()
            
            if driver:
                try:
                    print("🔒 Attempting to close Chrome driver after error...")
                    # Try to get current URL and page info before closing
                    try:
                        current_url = driver.current_url
                        page_title = driver.title
                        print(f"📊 Current URL before close: {current_url}")
                        print(f"📊 Page title before close: {page_title}")
                    except:
                        pass
                    driver.quit()
                    print("✅ Chrome driver closed after error")
                except Exception as quit_error:
                    print(f"⚠️ Error closing driver: {quit_error}")
            raise Exception(f"Critical error: {e}")
    
    def scrape_instagram_profile(self, username, max_posts=10, include_stories=False, session_name=None):
        """Scrape a single Instagram profile"""
        try:
            # Use the existing apify_profile_scraper for single username
            result = self.apify_profile_scraper([username], max_profiles=1)
            
            if result and len(result) > 0:
                profile_data = result[0]
                
                # Add session_name if provided
                if session_name:
                    profile_data['session_name'] = session_name
                else:
                    profile_data['session_name'] = f"Profile Scraping - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                
                # Save to leads storage
                lead_data = {
                    'id': f"lead_{int(time.time())}_{username}",
                    'username': username,
                    'full_name': profile_data.get('full_name', ''),
                    'biography': profile_data.get('biography', ''),
                    'followers_count': int(profile_data.get('followers_count', 0)),
                    'following_count': int(profile_data.get('following_count', 0)),
                    'posts_count': int(profile_data.get('posts_count', 0)),
                    'is_verified': profile_data.get('is_verified', False),
                    'profile_pic_url': profile_data.get('profile_pic_url', ''),
                    'nationality': 'UNKNOWN',
                    'confidence': 0.0,
                    'session_name': profile_data['session_name'],
                    'scraped_at': datetime.now().isoformat(),
                    'created_at': datetime.now().isoformat(),
                    'last_updated': datetime.now().isoformat()
                }
                
                # Add to storage
                self.leads_storage.append(lead_data)
                
                # Save to Supabase
                if self.supabase_connected:
                    try:
                        self.supabase.table("leads").insert(lead_data).execute()
                        print(f"💾 Saved lead {username} to Supabase")
                    except Exception as e:
                        print(f"⚠️ Warning: Could not save lead to Supabase: {e}")
                
                return profile_data
            else:
                raise Exception("No profile data found")
                
        except Exception as e:
            print(f"❌ Error scraping profile {username}: {str(e)}")
            raise e

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
                
                # Click login button - try multiple selectors for button/div
                login_button = None
                login_selectors = [
                    (By.XPATH, "//button[@type='submit']"),
                    (By.XPATH, "//div[contains(text(), 'Log in')]"),
                    (By.XPATH, "//div[contains(text(), 'Log In')]"),
                    (By.XPATH, "//button[contains(text(), 'Log in')]"),
                    (By.XPATH, "//button[contains(text(), 'Log In')]"),
                ]
                
                for selector_type, selector_value in login_selectors:
                    try:
                        login_button = driver.find_element(selector_type, selector_value)
                        break
                    except:
                        continue
                
                if login_button is None:
                    raise Exception("Login button not found - Instagram may have changed")
                
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
            print(f"🔐 Attempting login for user: {username}")
            
            # Check Supabase connection
            if not self.supabase_connected:
                print("❌ Supabase not connected")
                return False, "Database not connected", None
            
            # Check if Supabase client exists
            if not self.supabase:
                print("❌ Supabase client not initialized")
                return False, "Database client not initialized", None
            
            # Test DNS resolution for Supabase URL
            try:
                import socket
                supabase_url = self.config.get('SUPABASE_URL', '')
                if supabase_url:
                    # Extract hostname from URL
                    from urllib.parse import urlparse
                    parsed = urlparse(supabase_url)
                    hostname = parsed.hostname
                    if hostname:
                        print(f"🔍 Testing DNS resolution for: {hostname}")
                        socket.gethostbyname(hostname)
                        print(f"✅ DNS resolution successful for {hostname}")
            except socket.gaierror as dns_error:
                print(f"❌ DNS resolution failed: {dns_error}")
                return False, f"DNS resolution failed: Cannot connect to database server", None
            except Exception as dns_check_error:
                print(f"⚠️ DNS check error: {dns_check_error}")
            
            password_hash = self._hash_password(password)
            print(f"🔍 Searching for user in database...")
            
            # Find user by username and password
            try:
                result = self.supabase.table("users").select("*").eq("username", username).eq("password_hash", password_hash).eq("is_active", True).execute()
                print(f"📊 Database query executed")
            except Exception as query_error:
                print(f"❌ Database query failed: {query_error}")
                print(f"❌ Error type: {type(query_error).__name__}")
                # Check if it's a DNS/network error
                error_str = str(query_error).lower()
                if "name or service not known" in error_str or "gaierror" in error_str or "dns" in error_str:
                    return False, "Network error: Cannot resolve database hostname. Please check your internet connection and DNS settings.", None
                raise query_error
            
            if result.data:
                user = result.data[0]
                
                # Update last login
                try:
                    self.supabase.table("users").update({"last_login": datetime.now().isoformat()}).eq("id", user["id"]).execute()
                except Exception as update_error:
                    print(f"⚠️ Failed to update last_login: {update_error}")
                
                print(f"✅ User {username} logged in successfully")
                return True, "Login successful", user
            else:
                print(f"❌ Invalid credentials for user: {username}")
                return False, "Invalid username or password", None
                
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Error during login: {error_msg}")
            print(f"❌ Error type: {type(e).__name__}")
            
            # Check for DNS/network errors
            if "name or service not known" in error_msg.lower() or "gaierror" in error_msg.lower():
                return False, "Network error: Cannot connect to database. Please check your internet connection.", None
            elif "timeout" in error_msg.lower():
                return False, "Connection timeout: Database server is not responding.", None
            
            return False, f"Login error: {error_msg}", None
    
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
    
    def get_all_leads(self):
        """Get all leads from storage"""
        try:
            print(f"🔍 Getting all leads from storage: {len(self.leads_storage)} leads")
            return self.leads_storage
        except Exception as e:
            print(f"❌ Error getting leads: {str(e)}")
            return []
    
    def get_all_sessions(self):
        """Get all sessions from leads storage"""
        try:
            print(f"🔍 Getting all sessions from leads storage: {len(self.leads_storage)} leads")
            
            # Create sessions from leads data
            session_map = {}
            for lead in self.leads_storage:
                session_name = lead.get('session_name', 'Unknown Session')
                if session_name not in session_map:
                    session_map[session_name] = {
                        'id': session_name,
                        'name': session_name,
                        'session_name': session_name,
                        'lead_count': 0,
                        'created_at': lead.get('created_at', ''),
                        'last_updated': lead.get('last_updated', '')
                    }
                session_map[session_name]['lead_count'] += 1
            
            sessions = list(session_map.values())
            print(f"📊 Created {len(sessions)} sessions from leads data")
            for session in sessions:
                print(f"📋 Session: {session['name']} ({session['lead_count']} leads)")
            
            return sessions
        except Exception as e:
            print(f"❌ Error getting sessions: {str(e)}")
            return []
    
    def get_leads_by_session(self, session_name):
        """Get leads filtered by session name"""
        try:
            filtered_leads = [lead for lead in self.leads_storage if lead.get('session_name') == session_name]
            print(f"🔍 Getting leads for session '{session_name}': {len(filtered_leads)} leads")
            return filtered_leads
        except Exception as e:
            print(f"❌ Error getting leads by session: {str(e)}")
            return []
    
    def _create_driver(self):
        """Create and configure Chrome WebDriver"""
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        # Instagram'a git ve giriş yap
        driver.get("https://www.instagram.com/")
        time.sleep(3)
        
        # Giriş kontrolü
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        
        try:
            WebDriverWait(driver, 5).until(
                EC.any_of(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='direct-inbox']")),
                    EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/direct/']"))
                )
            )
            print("✅ Already logged in to Instagram")
        except:
            print("🔐 Not logged in, attempting to login...")
            ig_username = self.config.get('INSTAGRAM_USERNAME')
            ig_password = self.config.get('INSTAGRAM_PASSWORD')

            if not ig_username or not ig_password:
                print("❌ Instagram credentials not configured")
                raise Exception("Instagram credentials not configured")

            username_input = driver.find_element(By.CSS_SELECTOR, "input[name='username']")
            password_input = driver.find_element(By.CSS_SELECTOR, "input[name='password']")
            username_input.send_keys(ig_username)
            password_input.send_keys(ig_password)
            driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
            time.sleep(5)

            try:
                WebDriverWait(driver, 10).until(
                    EC.any_of(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='direct-inbox']")),
                        EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/direct/']"))
                    )
                )
                print("✅ Successfully logged in to Instagram")
            except:
                print("❌ Login failed - check credentials or 2FA")
                raise Exception("Login failed - check credentials or 2FA")
        
        return driver
    
    def send_instagram_message(self, username, message_content, delay_seconds=2):
        """Send Instagram message to a user using Selenium automation"""
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.common.exceptions import TimeoutException
        from selenium.webdriver.common.action_chains import ActionChains
        from datetime import datetime
        import time

        driver = self.global_driver
        if not driver:
            driver = self._create_driver()
            self.global_driver = driver

        try:
            print(f"💬 Starting message process for @{username}...")
            print(f"📝 Message: {message_content}")

            # Önce profili ziyaret et
            profile_url = f"https://www.instagram.com/{username}/"
            print(f"🔍 Navigating to profile: {profile_url}")
            driver.get(profile_url)
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(3)
            
            # Mesaj butonunu bul ve tıkla
            message_button_selectors = [
                "//button[contains(text(), 'Message')]",
                "//button[contains(text(), 'Mesaj')]",
                "//a[contains(text(), 'Message')]",
                "//a[contains(text(), 'Mesaj')]",
                "//div[contains(@role, 'button') and contains(text(), 'Message')]",
                "//div[contains(@role, 'button') and contains(text(), 'Mesaj')]",
                "//button[contains(@aria-label, 'Message')]",
                "//button[contains(@aria-label, 'Mesaj')]"
            ]
            
            message_button = None
            for selector in message_button_selectors:
                try:
                    message_button = WebDriverWait(driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    print(f"📨 Found message button with selector: {selector}")
                    break
                except TimeoutException:
                    continue
            
            if not message_button:
                print(f"❌ Message button not found for @{username}")
                return {
                    "success": False,
                    "username": username,
                    "error": "Message button not found",
                    "timestamp": datetime.now().isoformat()
                }
            
            # Mesaj butonuna tıkla
            try:
                message_button.click()
                print(f"📨 Clicked message button for @{username}")
                time.sleep(3)  # Mesaj sayfasının yüklenmesi için bekle
                
                # Mesaj kutusunu bul ve mesajı yaz
                print(f"🔍 Looking for message input box...")
                try:
                    message_box = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div[contenteditable='true']"))
                    )
                    print(f"✅ Message input box found")
                    message_box.click()
                    time.sleep(1)
                    print(f"📝 Typing message: {message_content}")
                    # Emoji karakterlerini kaldır veya ASCII karakterlerle değiştir
                    clean_message = message_content.replace('😊', ':)').replace('😀', ':)').replace('😃', ':)').replace('😄', ':)').replace('😁', ':)').replace('😆', ':)').replace('😅', ':)').replace('😂', ':)').replace('🤣', ':)').replace('😊', ':)').replace('😇', ':)').replace('🙂', ':)').replace('🙃', ':)').replace('😉', ';)').replace('😌', ':)').replace('😍', ':)').replace('🥰', ':)').replace('😘', ':)').replace('😗', ':)').replace('😙', ':)').replace('😚', ':)').replace('😋', ':)').replace('😛', ':)').replace('😝', ':)').replace('😜', ';)').replace('🤪', ';)').replace('🤨', ';)').replace('🧐', ';)').replace('🤓', ';)').replace('😎', ';)').replace('🤩', ';)').replace('🥳', ';)').replace('😏', ';)').replace('😒', ';)').replace('😞', ';)').replace('😔', ';)').replace('😟', ';)').replace('😕', ';)').replace('🙁', ';)').replace('☹️', ';)').replace('😣', ';)').replace('😖', ';)').replace('😫', ';)').replace('😩', ';)').replace('🥺', ';)').replace('😢', ';)').replace('😭', ';)').replace('😤', ';)').replace('😠', ';)').replace('😡', ';)').replace('🤬', ';)').replace('🤯', ';)').replace('😳', ';)').replace('🥵', ';)').replace('🥶', ';)').replace('😱', ';)').replace('😨', ';)').replace('😰', ';)').replace('😥', ';)').replace('😓', ';)').replace('🤗', ';)').replace('🤔', ';)').replace('🤭', ';)').replace('🤫', ';)').replace('🤥', ';)').replace('😶', ';)').replace('😐', ';)').replace('😑', ';)').replace('😬', ';)').replace('🙄', ';)').replace('😯', ';)').replace('😦', ';)').replace('😧', ';)').replace('😮', ';)').replace('😲', ';)').replace('🥱', ';)').replace('😴', ';)').replace('🤤', ';)').replace('😪', ';)').replace('😵', ';)').replace('🤐', ';)').replace('🥴', ';)').replace('🤢', ';)').replace('🤮', ';)').replace('🤧', ';)').replace('😷', ';)').replace('🤒', ';)').replace('🤕', ';)').replace('🤑', ';)').replace('🤠', ';)').replace('😈', ';)').replace('👿', ';)').replace('👹', ';)').replace('👺', ';)').replace('🤡', ';)').replace('💩', ';)').replace('👻', ';)').replace('💀', ';)').replace('☠️', ';)').replace('👽', ';)').replace('👾', ';)').replace('🤖', ';)').replace('🎃', ';)').replace('😺', ';)').replace('😸', ';)').replace('😹', ';)').replace('😻', ';)').replace('😼', ';)').replace('😽', ';)').replace('🙀', ';)').replace('😿', ';)').replace('😾', ';)')
                    message_box.send_keys(clean_message)
                    print("✅ Message typed successfully")
                    time.sleep(2)
                except Exception as e:
                    print(f"❌ Error finding message input: {str(e)}")
                    return {
                        "success": False,
                        "username": username,
                        "error": f"Message input not found: {str(e)}",
                        "timestamp": datetime.now().isoformat()
                    }
                
                # Gönder butonunu bul (HTML'deki yapıya göre)
                print(f"🔍 Looking for send button...")
                send_selectors = [
                    "//div[@aria-label='Send' and @role='button']",
                    "//div[@aria-label='Send']",
                    "//div[contains(@class, 'x1i10hfl') and contains(@class, 'x972fbf') and @role='button']",
                    "//div[@role='button' and .//svg[@aria-label='Send']]",
                    "//div[contains(@class, 'x1i10hfl') and @role='button']",
                    "//button[contains(text(), 'Send')]",
                    "//button[contains(text(), 'Gönder')]",
                    "//button[contains(@aria-label, 'Send')]",
                    "//button[contains(@aria-label, 'Gönder')]",
                    "//button[@type='submit']"
                ]

                send_button = None
                for selector in send_selectors:
                    try:
                        send_button = WebDriverWait(driver, 2).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                        print(f"📤 Found send button with selector: {selector}")
                        break
                    except TimeoutException:
                        continue

                if not send_button:
                    print("❌ Send button not found with any selector")
                    return {
                        "success": False,
                        "username": username,
                        "error": "Send button not found",
                        "timestamp": datetime.now().isoformat()
                    }

                # Gönder butonuna tıklama denemeleri
                print("📤 Attempting to send message...")
                click_successful = False
                
                # Method 1: Regular click
                try:
                    send_button.click()
                    print("✅ Regular click successful")
                    click_successful = True
                except Exception as e1:
                    print(f"⚠️ Regular click failed: {str(e1)}")
                    
                    # Method 2: JavaScript click with focus
                    try:
                        driver.execute_script("""
                            arguments[0].focus();
                            arguments[0].click();
                        """, send_button)
                        print("✅ JavaScript click with focus successful")
                        click_successful = True
                    except Exception as e2:
                        print(f"⚠️ JavaScript click with focus failed: {str(e2)}")
                        
                        # Method 3: ActionChains click
                        try:
                            ActionChains(driver).move_to_element(send_button).click().perform()
                            print("✅ ActionChains click successful")
                            click_successful = True
                        except Exception as e3:
                            print(f"⚠️ ActionChains click failed: {str(e3)}")
                            
                            # Method 4: JavaScript event dispatch
                            try:
                                driver.execute_script("""
                                    var element = arguments[0];
                                    var event = new MouseEvent('click', {
                                        view: window,
                                        bubbles: true,
                                        cancelable: true
                                    });
                                    element.dispatchEvent(event);
                                """, send_button)
                                print("✅ JavaScript event dispatch successful")
                                click_successful = True
                            except Exception as e4:
                                print(f"❌ All click methods failed: {str(e4)}")

                if not click_successful:
                    return {
                        "success": False,
                        "username": username,
                        "error": "Failed to click send button with all methods",
                        "timestamp": datetime.now().isoformat()
                    }
                
                # Mesajın gönderilmesi için bekle
                time.sleep(3)
                print(f"✅ Message sent to @{username}")
                
                # Başarılı sonuç döndür
                return {
                    "success": True,
                    "username": username,
                    "message": "Message sent successfully",
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                print(f"❌ Error clicking message button: {str(e)}")
                return {
                    "success": False,
                    "username": username,
                    "error": f"Error clicking message button: {str(e)}",
                    "timestamp": datetime.now().isoformat()
                }


        except Exception as e:
            import traceback
            print(f"❌ Error sending message to @{username}: {str(e)}")
            print(f"❌ Error type: {type(e).__name__}")
            print(f"❌ Traceback:\n{traceback.format_exc()}")
            return {
                "success": False,
                "username": username,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

        finally:
            # Sadece tek mesaj gönderiminde browser'ı kapat
            if driver and not getattr(self, "_bulk_campaign_active", False):
                driver.quit()
                self.global_driver = None
                print("🔒 Browser closed after single message")


    def send_message_campaign(self, usernames, template_content, delay_seconds=2):
        """Send message campaign to multiple users with automatic translation"""
        from datetime import datetime
        import time

        try:
            print(f"🚀 Starting message campaign for {len(usernames)} users")
            print(f"🌐 Translation enabled: Foreign accounts will receive messages in their language")
            
            # Bulk campaign flag'ini ayarla
            self._bulk_campaign_active = True
            
            # Get leads data for nationality-based translation
            leads_data = self.get_all_leads()
            print(f"📊 Found {len(leads_data)} leads with nationality data")
            
            results = []
            for i, username in enumerate(usernames):
                print(f"\n{'='*60}")
                print(f"📤 Sending message {i+1}/{len(usernames)} to @{username}")
                print(f"{'='*60}")
                
                # {username} placeholder'ını gerçek kullanıcı adıyla değiştir
                personalized_message = template_content.replace('{username}', username)
                
                # Translate message based on user's nationality
                translated_message = self.translate_message_for_user(personalized_message, username, leads_data)
                
                if translated_message != personalized_message:
                    print(f"🌍 Message translated for {username}")
                    print(f"📝 Original: {personalized_message[:100]}...")
                    print(f"📝 Translated: {translated_message[:100]}...")
                else:
                    print(f"🇹🇷 Using original Turkish message for {username}")
                
                result = self.send_instagram_message(username, translated_message, delay_seconds)
                results.append(result)
                
                # Son mesaj dışında bekle
                if i < len(usernames) - 1:
                    print(f"⏱️ Waiting {delay_seconds} seconds before next message...")
                    time.sleep(delay_seconds)
            
            # İstatistikleri hesapla
            successful = len([r for r in results if r.get('success')])
            failed = len(results) - successful
            
            print(f"\n{'='*60}")
            print(f"✅ Campaign completed!")
            print(f"📊 Total: {len(usernames)} | Successful: {successful} | Failed: {failed}")
            print(f"{'='*60}")
            
            return {
                "success": True,
                "total_sent": len(usernames),
                "successful": successful,
                "failed": failed,
                "results": results,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            import traceback
            print(f"❌ Error in message campaign: {str(e)}")
            print(f"❌ Traceback:\n{traceback.format_exc()}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        
        finally:
            # Campaign tamamlandıktan sonra browser'ı kapat ve flag'i sıfırla
            self._bulk_campaign_active = False
            if self.global_driver:
                self.global_driver.quit()
                self.global_driver = None
                print("🔒 Global browser closed after campaign completion")

    def translate_message_with_deepl(self, message, target_language="EN"):
        """Translate message using DeepL API"""
        try:
            import requests
            
            if not self.config.get('DEEPL_API_KEY'):
                print("⚠️ DeepL API key not configured")
                return message
            
            # DeepL API endpoint
            url = "https://api-free.deepl.com/v2/translate"
            
            # API request parameters
            params = {
                'auth_key': self.config['DEEPL_API_KEY'],
                'text': message,
                'target_lang': target_language,
                'source_lang': 'TR'  # Turkish source
            }
            
            print(f"🌐 Translating message to {target_language}: {message[:50]}...")
            
            response = requests.post(url, data=params)
            
            if response.status_code == 200:
                result = response.json()
                translated_text = result['translations'][0]['text']
                print(f"✅ Translation successful: {translated_text[:50]}...")
                return translated_text
            else:
                print(f"❌ DeepL API error: {response.status_code} - {response.text}")
                return message
                
        except Exception as e:
            print(f"❌ Translation error: {str(e)}")
            return message

    def get_target_language_for_nationality(self, nationality):
        """Get target language code for nationality"""
        nationality_upper = nationality.upper().strip()
        
        # Check if it's Turkish (no translation needed)
        if 'TÜRK' in nationality_upper or 'TURK' in nationality_upper:
            return 'TR'
        
        # Handle Turkish format: "YABANCI - COUNTRY"
        if 'YABANCI' in nationality_upper:
            # Extract country name after "YABANCI - "
            country_part = nationality_upper.replace('YABANCI', '').replace('-', '').strip()
            
            # Map Turkish country names to language codes
            turkish_country_map = {
                'ABD': 'EN',           # United States
                'AMERİKA': 'EN',       # America
                'İNGİLTERE': 'EN',     # England
                'İNGİLİZ': 'EN',       # English
                'ALMANYA': 'DE',       # Germany
                'ALMAN': 'DE',         # German
                'FRANSA': 'FR',        # France
                'FRANSIZ': 'FR',       # French
                'İSPANYA': 'ES',       # Spain
                'İSPANYOL': 'ES',      # Spanish
                'İTALYA': 'IT',        # Italy
                'İTALYAN': 'IT',       # Italian
                'RUSYA': 'RU',         # Russia
                'RUS': 'RU',           # Russian
                'ARAP': 'AR',          # Arabic
                'ARAPÇA': 'AR',        # Arabic
                'İRAN': 'FA',          # Iran
                'İRANLI': 'FA',        # Iranian
                'FARS': 'FA',          # Persian
                'ÇİN': 'ZH',           # China
                'ÇİNLİ': 'ZH',         # Chinese
                'JAPONYA': 'JA',       # Japan
                'JAPON': 'JA',         # Japanese
                'KORE': 'KO',          # Korea
                'KORELİ': 'KO',        # Korean
                'BREZİLYA': 'PT',      # Brazil
                'BREZİLYALI': 'PT',    # Brazilian
                'PORTEKİZ': 'PT',      # Portugal
                'PORTEKİZLİ': 'PT',    # Portuguese
                'HOLLANDA': 'NL',      # Netherlands
                'HOLLANDALI': 'NL',    # Dutch
                'POLONYA': 'PL',       # Poland
                'POLONYALI': 'PL',     # Polish
                'YUNANİSTAN': 'EL',    # Greece
                'YUNAN': 'EL',         # Greek
                'İSRAİL': 'HE',        # Israel
                'İSRAİLLİ': 'HE',      # Israeli
                'SLOVAKYA': 'SK',      # Slovakia
                'SLOVAK': 'SK',        # Slovak
                'KAZAKİSTAN': 'KK',    # Kazakhstan
                'KAZAK': 'KK',         # Kazakh
                'MEKSİKA': 'ES',       # Mexico
                'MEKSİKALI': 'ES',     # Mexican
                'ÖZBEKİSTAN': 'UZ',   # Uzbekistan
                'ÖZBEK': 'UZ',        # Uzbek
                'UKRAYNA': 'UK',       # Ukraine
                'UKRAYNALI': 'UK',     # Ukrainian
                'ROMANYA': 'RO',       # Romania
                'ROMANYALI': 'RO',    # Romanian
                'BULGARİSTAN': 'BG',   # Bulgaria
                'BULGAR': 'BG',        # Bulgarian
                'MACARİSTAN': 'HU',    # Hungary
                'MACAR': 'HU',         # Hungarian
                'ÇEK': 'CS',           # Czech
                'ÇEK CUMHURİYETİ': 'CS', # Czech Republic
                'AVUSTURYA': 'DE',     # Austria
                'AVUSTURYALI': 'DE',   # Austrian
                'İSVİÇRE': 'DE',       # Switzerland
                'İSVİÇRELİ': 'DE',     # Swiss
                'BELÇİKA': 'NL',       # Belgium
                'BELÇİKALI': 'NL',     # Belgian
                'DANİMARKA': 'DA',     # Denmark
                'DANİMARKALI': 'DA',   # Danish
                'İSVEÇ': 'SV',         # Sweden
                'İSVEÇLİ': 'SV',       # Swedish
                'NORVEÇ': 'NO',        # Norway
                'NORVEÇLİ': 'NO',      # Norwegian
                'FİNLANDİYA': 'FI',    # Finland
                'FİNLANDİYALI': 'FI',  # Finnish
                'KANADA': 'EN',        # Canada
                'KANADALI': 'EN',      # Canadian
                'AVUSTRALYA': 'EN',    # Australia
                'AVUSTRALYALI': 'EN',  # Australian
                'YENİ ZELANDA': 'EN',  # New Zealand
                'YENİ ZELANDALI': 'EN', # New Zealander
                'GÜNEY AFRİKA': 'EN',  # South Africa
                'GÜNEY AFRİKALI': 'EN', # South African
                'HİNDİSTAN': 'HI',     # India
                'HİNDİSTANLI': 'HI',   # Indian
                'PAKİSTAN': 'UR',      # Pakistan
                'PAKİSTANLI': 'UR',    # Pakistani
                'BANGLADEŞ': 'BN',     # Bangladesh
                'BANGLADEŞLİ': 'BN',   # Bangladeshi
                'SRI LANKA': 'SI',     # Sri Lanka
                'SRI LANKALI': 'SI',   # Sri Lankan
                'NEPAL': 'NE',         # Nepal
                'NEPALLI': 'NE',       # Nepalese
                'BURMA': 'MY',         # Myanmar
                'BURMALI': 'MY',       # Burmese
                'TAYLAND': 'TH',       # Thailand
                'TAYLANDLI': 'TH',     # Thai
                'VİETNAM': 'VI',       # Vietnam
                'VİETNAMLI': 'VI',     # Vietnamese
                'KAMBOÇYA': 'KM',      # Cambodia
                'KAMBOÇYALI': 'KM',    # Cambodian
                'LAOS': 'LO',          # Laos
                'LAOSLU': 'LO',        # Laotian
                'MALEZYA': 'MS',       # Malaysia
                'MALEZYALI': 'MS',     # Malaysian
                'SİNGAPUR': 'EN',      # Singapore
                'SİNGAPURLU': 'EN',    # Singaporean
                'ENDONEZYA': 'ID',     # Indonesia
                'ENDONEZYALI': 'ID',   # Indonesian
                'FİLİPİNLER': 'TL',    # Philippines
                'FİLİPİNLİ': 'TL',     # Filipino
                'BRUNEY': 'MS',        # Brunei
                'BRUNEYLI': 'MS',      # Bruneian
                'TİMOR': 'TL',         # Timor
                'TİMORLU': 'TL',       # Timorese
                'PAPUA YENİ GİNE': 'EN', # Papua New Guinea
                'PAPUA YENİ GİNELİ': 'EN', # Papua New Guinean
                'FİJİ': 'EN',          # Fiji
                'FİJİLİ': 'EN',        # Fijian
                'TONGA': 'TO',         # Tonga
                'TONGALI': 'TO',       # Tongan
                'SAMOA': 'SM',         # Samoa
                'SAMOALI': 'SM',       # Samoan
                'KİRİBATİ': 'EN',      # Kiribati
                'KİRİBATİLİ': 'EN',    # Kiribati
                'TUVALU': 'EN',        # Tuvalu
                'TUVALU': 'EN',        # Tuvaluan
                'VANUATU': 'BI',       # Vanuatu
                'VANUATULU': 'BI',     # Vanuatuan
                'SOLOMON ADALARI': 'EN', # Solomon Islands
                'SOLOMON ADALARI': 'EN', # Solomon Islander
                'PALAU': 'EN',         # Palau
                'PALAULU': 'EN',       # Palauan
                'MARŞAL ADALARI': 'EN', # Marshall Islands
                'MARŞAL ADALARI': 'EN', # Marshallese
                'MİKRONEZYA': 'EN',    # Micronesia
                'MİKRONEZYALI': 'EN',  # Micronesian
                'NAURU': 'NA',         # Nauru
                'NAURULU': 'NA',       # Nauruan
            }
            
            # Find matching country
            for turkish_name, lang_code in turkish_country_map.items():
                if turkish_name in country_part:
                    return lang_code
        
        # Fallback to English for unknown foreign nationalities
        return 'EN'

    def translate_message_for_user(self, message, username, leads_data=None):
        """Translate message for a specific user based on their nationality"""
        try:
            # If no leads data provided, get from storage
            if leads_data is None:
                leads_data = self.get_all_leads()
            
            # Find user's nationality from leads data
            user_nationality = None
            for lead in leads_data:
                if lead.get('username', '').lower() == username.lower():
                    user_nationality = lead.get('nationality', '')
                    break
            
            if not user_nationality:
                print(f"⚠️ No nationality data found for {username}, using original message")
                return message
            
            # Get target language for this nationality
            target_language = self.get_target_language_for_nationality(user_nationality)
            
            # If target language is Turkish, no translation needed
            if target_language == 'TR':
                print(f"🇹🇷 User {username} is Turkish, using original message")
                return message
            
            # Translate for foreign users
            print(f"🌍 User {username} nationality: {user_nationality} -> Language: {target_language}")
            translated_message = self.translate_message_with_deepl(message, target_language)
            
            return translated_message
            
        except Exception as e:
            print(f"❌ Error translating message for {username}: {str(e)}")
            return message