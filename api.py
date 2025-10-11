from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import time
from datetime import datetime
from dotenv import load_dotenv
from backend import InstagramBackend
import json

# Load environment variables
load_dotenv()

app = FastAPI(title="Instagram Scraper API", version="1.0.0")

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "https://your-frontend-domain.vercel.app",
        "https://*.vercel.app"  # Vercel subdomain'leri için
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize backend with Supabase config
config = {
    'SUPABASE_URL': 'https://rltkqtlinpsueyaervdv.supabase.co',
    'SUPABASE_API_KEY': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJsdGtxdGxpbnBzdWV5YWVydmR2Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NzU3NTk4NSwiZXhwIjoyMDczMTUxOTg1fQ.doT1nxL0izQRpCqzAY-StRFrzqRRuRyiKhZDwKfk_fI',
    'APIFY_API_TOKEN': 'apify_api_VeivXy54nUuP7jP3zdPStvnY1bdy6P12ohvn',
    'OPENROUTER_API_KEY': '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',
    'UNIPILE_API_KEY': 'k8IpFvnp.1H5f5alAgW2gK5M+J4GvW2M1lavbPHdsZfUGXBbEF+U=',
    'UNIPILE_BASE_URL': 'https://api21.unipile.com:15121',
    'DEEPL_API_KEY': '721f4e0a-7600-425a-9bd4-7c4282e7770c:fx'
}
backend = InstagramBackend(config)
# Instagram accounts will be loaded from Supabase in backend.__init__

# Pydantic models
class ScrapeRequest(BaseModel):
    username: str
    max_posts: Optional[int] = 10
    include_stories: Optional[bool] = False

class MessageRequest(BaseModel):
    username: str
    message: str
    delay_seconds: Optional[int] = 2

class UserData(BaseModel):
    username: str
    full_name: Optional[str] = None
    bio: Optional[str] = None
    followers_count: Optional[int] = None
    following_count: Optional[int] = None
    posts_count: Optional[int] = None

class PostData(BaseModel):
    id: str
    caption: Optional[str] = None
    likes_count: Optional[int] = None
    comments_count: Optional[int] = None
    timestamp: Optional[str] = None
    media_urls: List[str] = []

class LocationScrapingRequest(BaseModel):
    locations: List[str]
    ig_user: str
    ig_pass: str
    max_profiles: Optional[int] = 20

class NationalityClassificationRequest(BaseModel):
    usernames: List[str]
    session_name: Optional[str] = None

class ProfileScrapingRequest(BaseModel):
    usernames: List[str]
    max_profiles: Optional[int] = 50

class InstagramAccountRequest(BaseModel):
    instagram_username: str
    instagram_password: str
    display_name: Optional[str] = None
    id: Optional[str] = None

# API Endpoints
@app.get("/")
async def root():
    return {"message": "Instagram Scraper API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "backend_available": True}

@app.post("/scrape/profile")
async def scrape_profile(request: ScrapeRequest):
    """Scrape Instagram profile data"""
    try:
        result = backend.scrape_instagram_profile(
            username=request.username,
            max_posts=request.max_posts,
            include_stories=request.include_stories
        )
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/scrape/posts")
async def scrape_posts(request: ScrapeRequest):
    """Scrape Instagram posts"""
    try:
        result = backend.scrape_instagram_posts(
            username=request.username,
            max_posts=request.max_posts
        )
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/send/message")
async def send_message(request: MessageRequest):
    """Send Instagram message"""
    try:
        result = backend.send_instagram_message(
            username=request.username,
            message=request.message,
            delay_seconds=request.delay_seconds
        )
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/users")
async def get_users():
    """Get all users from database"""
    try:
        users = backend.get_all_users()
        return {"success": True, "data": users}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/users/{username}")
async def get_user(username: str):
    """Get specific user data"""
    try:
        user = backend.get_user_data(username)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {"success": True, "data": user}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics/{username}")
async def get_analytics(username: str):
    """Get analytics data for a user"""
    try:
        analytics = backend.get_user_analytics(username)
        return {"success": True, "data": analytics}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/dashboard/stats")
async def get_dashboard_stats():
    """Get dashboard statistics"""
    try:
        stats = backend.get_dashboard_statistics()
        return {"success": True, "data": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/users/{username}")
async def delete_user(username: str):
    """Delete user data"""
    try:
        result = backend.delete_user_data(username)
        return {"success": True, "message": f"User {username} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Campaign endpoints
@app.post("/campaigns/location-scraping")
async def location_scraping(request: LocationScrapingRequest):
    """Start location scraping campaign"""
    try:
        print(f"🔍 Starting REAL location scraping for: {request.locations}")
        print(f"👤 Using Instagram account: {request.ig_user}")
        print(f"📊 Max profiles: {request.max_profiles}")
        
        # Real scraping
        result = backend.selenium_location_scraper(
            request.ig_user,
            request.ig_pass,
            request.locations,
            request.max_profiles
        )
        
        print(f"✅ Scraping completed! Result type: {type(result)}")
        print(f"✅ Scraping completed! Found {len(result)} usernames")
        print(f"✅ First few usernames: {result[:3] if result else 'Empty'}")
        
        return {"success": True, "data": {"usernames": result}}
        
    except Exception as e:
        print(f"❌ Scraping error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/campaigns/nationality-classification")
async def nationality_classification(request: NationalityClassificationRequest):
    """Start nationality classification"""
    try:
        print(f"🔍 Starting nationality classification for {len(request.usernames)} usernames")
        print(f"📝 Usernames: {request.usernames[:5]}...")  # Show first 5 usernames
        
        import pandas as pd
        
        # Get existing profile data from leads storage
        all_leads = backend.get_all_leads()
        print(f"📊 Found {len(all_leads)} existing leads in storage")
        
        # Create profiles DataFrame with real data from previous scraping
        profiles_data = []
        for username in request.usernames:
            # Look for existing profile data for this username
            existing_profile = None
            for lead in all_leads:
                if lead.get('username', '').lower() == username.lower():
                    existing_profile = lead
                    break
            
            if existing_profile:
                # Use real data from previous scraping
                profiles_data.append({
                    'username': username,
                    'full_name': existing_profile.get('full_name', username),
                    'followers_count': existing_profile.get('followers_count', 0),
                    'following_count': existing_profile.get('following_count', 0),
                    'bio': existing_profile.get('bio', ''),
                    'posts_count': existing_profile.get('posts_count', 0)
                })
                print(f"✅ Found existing profile data for {username}: {existing_profile.get('followers_count', 0)} followers")
            else:
                # Fallback to default values if no existing data
                profiles_data.append({
                    'username': username,
                    'full_name': username,
                    'followers_count': 0,
                    'following_count': 0,
                    'bio': '',
                    'posts_count': 0
                })
                print(f"⚠️ No existing profile data for {username}, using defaults")
        
        profiles_df = pd.DataFrame(profiles_data)
        
        print(f"📊 Created DataFrame with {len(profiles_df)} rows")
        print(f"📋 DataFrame columns: {list(profiles_df.columns)}")
        print(f"📊 Sample data: {profiles_df.head(2).to_dict('records')}")
        
        if not hasattr(backend, 'config') or 'OPENROUTER_API_KEY' not in backend.config:
            raise Exception("OpenRouter API key not configured")
        
        print(f"🔑 API key configured: {bool(backend.config.get('OPENROUTER_API_KEY'))}")
        
        result = backend.batch_nationality_classification(
            profiles_df,
            model="openai/gpt-4o-mini",
            batch_size=50,
            sleep_s=2.0
        )
        
        print(f"✅ Classification completed, result type: {type(result)}")
        print(f"📊 Result shape: {result.shape if hasattr(result, 'shape') else 'N/A'}")
        print(f"📋 Result columns: {list(result.columns) if hasattr(result, 'columns') else 'N/A'}")
        if len(result) > 0:
            first_result = result.iloc[0].to_dict()
            print(f"🔍 First result: {first_result}")
            print(f"🏳️ Nationality: {first_result.get('Nationality', 'NOT_FOUND')}")
            print(f"📝 Bio: {first_result.get('bio', 'NOT_FOUND')}")
        
        # Save results to leads - use existing profile scraping session if available
        try:
            # Check if there's a recent profile scraping session to merge with
            all_sessions = backend.get_all_sessions()
            recent_profile_session = None
            
            # Look for the most recent profile scraping session
            for session in all_sessions:
                if 'Profile Scraping' in session.get('name', ''):
                    recent_profile_session = session
                    break
            
            if recent_profile_session:
                # Use the existing profile scraping session name
                session_name = recent_profile_session['name']
                print(f"📝 Merging nationality data with existing profile session: {session_name}")
            else:
                # Create new session if no profile scraping session found
                session_name = request.session_name or f"Nationality Classification - {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}"
                print(f"📝 Using new session name: {session_name}")
            
            saved_leads = backend.save_nationality_results(result, session_name)
            print(f"✅ Saved {len(saved_leads)} leads to database")
        except Exception as save_error:
            print(f"⚠️ Warning: Could not save leads to database: {save_error}")
        
        return {"success": True, "data": {"classifications": result.to_dict('records')}}
    except Exception as e:
        print(f"❌ Nationality classification error: {str(e)}")
        print(f"❌ Error type: {type(e).__name__}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Nationality classification failed: {str(e)}")

@app.post("/campaigns/profile-scraping")
async def profile_scraping(request: ProfileScrapingRequest):
    """Start profile scraping campaign"""
    try:
        print(f"🔍 Starting REAL profile scraping for {len(request.usernames)} usernames")
        print(f"📊 Max profiles: {request.max_profiles}")
        
        # Call real backend profile scraping function
        result = backend.apify_profile_scraper(
            usernames=request.usernames,
            max_profiles=request.max_profiles
        )
        
        # Transform backend data to frontend format
        transformed_profiles = []
        for item in result:
            profile_data = {
                "username": item.get("username", ""),
                "full_name": item.get("fullName", ""),
                "bio": item.get("biography", ""),
                "followers_count": item.get("followersCount", 0),
                "following_count": item.get("followsCount", 0),
                "posts_count": item.get("postsCount", 0),
                "is_verified": item.get("verified", False),
                "profile_pic_url": item.get("profilePicUrl", "")
            }
            transformed_profiles.append(profile_data)
        
        # Save profiles to leads storage for future nationality classification
        try:
            import pandas as pd
            profiles_df = pd.DataFrame(transformed_profiles)
            session_name = f"Profile Scraping - {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}"
            saved_leads = backend.save_nationality_results(profiles_df, session_name)
            print(f"💾 Saved {len(saved_leads)} profiles to leads storage for future nationality classification")
        except Exception as save_error:
            print(f"⚠️ Warning: Could not save profiles to leads storage: {save_error}")
        
        print(f"✅ Profile scraping completed! Found {len(transformed_profiles)} profiles")
        return {"success": True, "data": {"profiles": transformed_profiles}}
        
    except Exception as e:
        print(f"❌ Profile scraping error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Instagram Accounts endpoints
@app.get("/instagram-accounts")
async def get_instagram_accounts():
    """Get all Instagram accounts"""
    try:
        print(f"🔍 Getting Instagram accounts, count: {len(backend.instagram_accounts)}")
        print(f"🔍 Accounts: {backend.instagram_accounts}")
        print(f"🔍 Supabase connected: {backend.supabase_connected}")
        
        # Try to load from Supabase if accounts are empty
        if len(backend.instagram_accounts) == 0 and backend.supabase_connected:
            print("🔄 No accounts in memory, trying to load from Supabase...")
            try:
                accounts_result = backend.supabase.table("instagram_accounts").select("*").execute()
                if accounts_result.data:
                    backend.instagram_accounts = accounts_result.data
                    print(f"✅ Loaded {len(backend.instagram_accounts)} accounts from Supabase")
                else:
                    print("📝 No accounts found in Supabase")
            except Exception as load_error:
                print(f"❌ Error loading accounts from Supabase: {load_error}")
        
        return {"success": True, "data": backend.instagram_accounts}
    except Exception as e:
        print(f"❌ Error getting accounts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/instagram-accounts")
async def create_instagram_account(request: InstagramAccountRequest):
    """Create new Instagram account"""
    try:
        print(f"🔍 Received Instagram account request: {request}")
        print(f"🔍 Username: {request.instagram_username}")
        print(f"🔍 Password: {request.instagram_password}")
        print(f"🔍 Display name: {request.display_name}")
        
        # For now, just return success - you can implement database storage later
        account_data = {
            "id": f"account_{len(backend.instagram_accounts) + 1}",
            "username": request.instagram_username,
            "password": request.instagram_password,
            "display_name": request.display_name or request.instagram_username,
            "created_at": "2024-01-01T00:00:00Z"
        }
        
        # Store in backend and Supabase
        if not hasattr(backend, 'instagram_accounts'):
            backend.instagram_accounts = []
        backend.instagram_accounts.append(account_data)
        
        # Save to Supabase for persistence
        try:
            if backend.supabase_connected:
                # Direct Supabase insert
                result = backend.supabase.table("instagram_accounts").insert(account_data).execute()
                print(f"💾 Saved Instagram account to Supabase: {account_data['username']}")
                print(f"📊 Supabase result: {result}")
            else:
                print("⚠️ Supabase not connected, account not saved to database")
        except Exception as save_error:
            print(f"⚠️ Warning: Could not save Instagram account to Supabase: {save_error}")
            print(f"🔍 Save error details: {save_error}")
        
        print(f"✅ Created account: {account_data}")
        return {"success": True, "data": account_data}
    except Exception as e:
        print(f"❌ Error creating account: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/instagram-accounts/{account_id}")
async def delete_instagram_account(account_id: str):
    """Delete Instagram account"""
    try:
        # For now, just return success - you can implement database storage later
        return {"success": True, "message": f"Account {account_id} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Leads endpoints
@app.get("/leads")
async def get_leads():
    """Get all leads"""
    try:
        print("🔍 GET /leads endpoint called")
        
        # Get leads from backend storage
        leads = backend.get_all_leads()
        
        print(f"📊 Returning {len(leads)} leads from storage")
        if leads:
            print(f"📋 First lead: {leads[0]['username']}")
        
        return {"success": True, "data": leads}
    except Exception as e:
        print(f"❌ Error getting leads: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/leads/sessions")
async def get_sessions():
    """Get all sessions"""
    try:
        print("🔍 GET /leads/sessions endpoint called")
        
        # Get sessions from backend storage
        sessions = backend.get_all_sessions()
        
        print(f"📊 Returning {len(sessions)} sessions from storage")
        if sessions:
            first_session = sessions[0]
            print(f"📋 First session: {first_session}")
            if 'name' in first_session:
                print(f"📋 Session name: {first_session['name']}")
            else:
                print(f"📋 Session keys: {list(first_session.keys())}")
        
        return {"success": True, "data": sessions}
    except Exception as e:
        print(f"❌ Error getting sessions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/leads/update-nationality")
async def update_nationality(request: dict):
    """Update nationality for a specific lead"""
    try:
        username = request.get('username')
        nationality = request.get('nationality')
        
        if not username or not nationality:
            raise HTTPException(status_code=400, detail="Username and nationality are required")
        
        print(f"🔍 Updating nationality for {username} to {nationality}")
        
        # Update in backend storage
        updated = False
        for lead in backend.leads_storage:
            if lead.get('username', '').lower() == username.lower():
                lead['nationality'] = nationality
                lead['last_updated'] = datetime.now().isoformat()
                updated = True
                break
        
        if not updated:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        # Update in Supabase
        if backend.supabase_connected:
            try:
                result = backend.supabase.table("leads").update({
                    "nationality": nationality,
                    "last_updated": datetime.now().isoformat()
                }).eq("username", username).execute()
                print(f"💾 Updated nationality in Supabase for {username}")
            except Exception as supabase_error:
                print(f"⚠️ Warning: Could not update nationality in Supabase: {supabase_error}")
        
        return {"success": True, "message": f"Nationality updated to {nationality} for {username}"}
    except Exception as e:
        print(f"❌ Error updating nationality: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Global templates storage
message_templates = [
    {
        "id": "welcome",
        "name": "Hoş Geldin Mesajı",
        "content": "Merhaba {username}! Instagram hesabınızı beğendim. Takip etmek ister misiniz? :)"
    },
    {
        "id": "follow_back",
        "name": "Takip Et Mesajı",
        "content": "Merhaba! Hesabınızı çok beğendim. Karşılıklı takip yapalım mı? :)"
    },
    {
        "id": "collaboration",
        "name": "İş Birliği Mesajı",
        "content": "Merhaba {username}! İş birliği yapmak ister misiniz? Birlikte güzel projeler çıkarabiliriz! :)"
    },
    {
        "id": "compliment",
        "name": "Övgü Mesajı",
        "content": "Harika paylaşımlarınız var! Çok beğendim. Devam edin! :)"
    },
    {
        "id": "question",
        "name": "Soru Mesajı",
        "content": "Merhaba! {username} hesabınızda gördüğüm bir şey hakkında soru sormak istiyorum. Cevap verebilir misiniz?"
    }
]

# Authentication endpoints with Supabase
@app.post("/auth/register")
async def register_user(request: dict):
    """Register a new user"""
    try:
        username = request.get('username')
        email = request.get('email')
        password = request.get('password')
        full_name = request.get('full_name', '')
        
        if not username or not email or not password:
            raise HTTPException(status_code=400, detail="Username, email and password are required")
        
        success, message = backend.register_user(username, email, password, full_name)
        
        if success:
            # Create user object for response
            user = {
                "id": f"user_{int(time.time())}",
                "username": username,
                "email": email,
                "full_name": full_name
            }
            
            return {
                "success": True,
                "message": "User registered successfully",
                "user": user
            }
        else:
            raise HTTPException(status_code=400, detail=message)
            
    except Exception as e:
        print(f"❌ Error registering user: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/auth/login")
async def login_user(request: dict):
    """Login user with Supabase"""
    try:
        username = request.get('username')
        password = request.get('password')
        
        if not username or not password:
            raise HTTPException(status_code=400, detail="Username and password are required")
        
        success, message, user = backend.login_user(username, password)
        
        if success:
            # Generate a simple token
            import hashlib
            import time
            token = hashlib.sha256(f"{username}{time.time()}".encode()).hexdigest()
            
            return {
                "success": True,
                "message": "Login successful",
                "access_token": token,
                "user": user
            }
        else:
            raise HTTPException(status_code=401, detail=message)
            
    except Exception as e:
        print(f"❌ Error logging in user: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/auth/me")
async def get_current_user():
    """Get current user info"""
    try:
        return {
            "success": True,
            "user": {
                "id": "user_1",
                "username": "admin",
                "email": "admin@example.com",
                "full_name": "Admin User"
            }
        }
    except Exception as e:
        print(f"❌ Error getting user info: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Message templates endpoints
@app.get("/message-templates")
async def get_message_templates():
    """Get all message templates"""
    try:
        return {
            "success": True,
            "data": message_templates
        }
    except Exception as e:
        print(f"❌ Error getting message templates: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/message-templates")
async def create_message_template(request: dict):
    """Create a new message template"""
    try:
        template_name = request.get('template_name')
        message_content = request.get('message_content')
        
        if not template_name or not message_content:
            raise HTTPException(status_code=400, detail="Template name and content are required")
        
        # Create new template
        new_template = {
            "id": f"template_{int(time.time())}",
            "name": template_name,
            "content": message_content
        }
        
        # Add to global templates list
        message_templates.append(new_template)
        
        print(f"✅ Template created: {template_name}")
        print(f"📝 Total templates: {len(message_templates)}")
        
        return {
            "success": True,
            "message": "Template created successfully",
            "data": new_template
        }
    except Exception as e:
        print(f"❌ Error creating message template: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Message campaign endpoint
@app.post("/campaigns/message-campaign")
async def message_campaign(request: dict):
    """Start message campaign"""
    try:
        print(f"🔍 Starting message campaign")
        print(f"📝 Campaign type: {request.get('campaign_type')}")
        print(f"📝 Usernames: {request.get('usernames', [])}")
        print(f"📝 Template ID: {request.get('template_id')}")
        print(f"📝 Delay: {request.get('delay_seconds')} seconds")
        
        # Get campaign parameters
        usernames = request.get('usernames', [])
        campaign_type = request.get('campaign_type', 'bulk')
        template_id = request.get('template_id')
        delay_seconds = request.get('delay_seconds', 2)
        instagram_account_id = request.get('instagram_account_id')
        
        # Check maximum usernames limit
        if len(usernames) > 100:
            raise HTTPException(status_code=400, detail="Maximum 100 usernames allowed per campaign")
        
        print(f"📝 Instagram Account ID: {instagram_account_id}")
        print(f"📊 Available Instagram accounts: {len(backend.instagram_accounts)}")
        print(f"📋 Account list: {backend.instagram_accounts}")
        
        # Get Instagram account credentials
        selected_account = None
        if instagram_account_id:
            for account in backend.instagram_accounts:
                print(f"🔍 Checking account: {account.get('id')} vs {instagram_account_id}")
                if account.get('id') == instagram_account_id:
                    selected_account = account
                    print(f"✅ Found matching account: {account}")
                    break
        
        if not selected_account:
            print(f"❌ No matching account found for ID: {instagram_account_id}")
            raise Exception("Instagram account not found")
        
        print(f"📝 Using Instagram account: {selected_account.get('username')}")
        
        # Update backend config with selected account credentials
        backend.config['INSTAGRAM_USERNAME'] = selected_account.get('username')
        backend.config['INSTAGRAM_PASSWORD'] = selected_account.get('password')
        
        # Get template content
        template_content = "Merhaba {username}! Instagram hesabınızı beğendim. Takip etmek ister misiniz? 😊"
        
        # Map template IDs to content
        template_map = {
            'welcome': 'Merhaba {username}! Instagram hesabınızı beğendim. Takip etmek ister misiniz? 😊',
            'follow_back': 'Merhaba! Hesabınızı çok beğendim. Karşılıklı takip yapalım mı? 🤝',
            'collaboration': 'Merhaba {username}! İş birliği yapmak ister misiniz? Birlikte güzel projeler çıkarabiliriz! 💼',
            'compliment': 'Harika paylaşımlarınız var! Çok beğendim. Devam edin! 👏',
            'question': 'Merhaba! {username} hesabınızda gördüğüm bir şey hakkında soru sormak istiyorum. Cevap verebilir misiniz?'
        }
        
        if template_id and template_id in template_map:
            template_content = template_map[template_id]
        
        print(f"📝 Using template: {template_content}")
        
        # Send messages using backend
        campaign_result = backend.send_message_campaign(
            usernames=usernames,
            template_content=template_content,
            delay_seconds=delay_seconds
        )
        
        if campaign_result.get('success'):
            print(f"✅ Message campaign completed successfully")
            print(f"📊 Results: {campaign_result.get('successful')} successful, {campaign_result.get('failed')} failed")
            
            return {
                "success": True, 
                "message": f"Message campaign completed: {campaign_result.get('successful')} successful, {campaign_result.get('failed')} failed",
                "data": {
                    "campaign_type": campaign_type,
                    "total_sent": campaign_result.get('total_sent'),
                    "successful": campaign_result.get('successful'),
                    "failed": campaign_result.get('failed'),
                    "results": campaign_result.get('results')
                }
            }
        else:
            print(f"❌ Message campaign failed: {campaign_result.get('error')}")
            raise Exception(f"Message campaign failed: {campaign_result.get('error')}")
    except Exception as e:
        print(f"❌ Error starting message campaign: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
