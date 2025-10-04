import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import json


class InstagramFrontend:
    """
    Frontend class for Instagram scraping UI
    Handles all Streamlit UI components, form handling, and user interactions
    """
    
    def __init__(self, backend):
        """
        Initialize frontend with backend instance
        
        Args:
            backend: InstagramBackend instance
        """
        self.backend = backend
        self._setup_page_config()
        self._initialize_session_state()
    
    def _setup_page_config(self):
        """Setup Streamlit page configuration"""
        st.set_page_config(
            page_title="Instagram Message System", 
            page_icon="💬", 
            layout="wide"
        )
        
        # Add custom CSS for better styling
        st.markdown("""
        <style>
        /* Main title styling */
        .main-title {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            text-align: center;
            font-size: 2.5rem;
            font-weight: bold;
            margin-bottom: 2rem;
        }
        
        /* Tab styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 2px;
        }
        
        .stTabs [data-baseweb="tab"] {
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border-radius: 8px 8px 0 0;
            border: 1px solid #dee2e6;
            margin-right: 2px;
            color: #000000 !important;
        }
        
        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        /* Button styling */
        .stButton > button {
            border-radius: 8px;
            border: none;
            transition: all 0.3s ease;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }
        
        /* Dataframe styling */
        .dataframe {
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        /* Success/Error message styling */
        .stSuccess {
            border-radius: 8px;
            border-left: 4px solid #28a745;
        }
        
        .stError {
            border-radius: 8px;
            border-left: 4px solid #dc3545;
        }
        
        .stWarning {
            border-radius: 8px;
            border-left: 4px solid #ffc107;
        }
        
        .stInfo {
            border-radius: 8px;
            border-left: 4px solid #17a2b8;
        }
        
        /* Sidebar styling */
        .css-1d391kg {
            background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
        }
        
        /* Metric styling */
        [data-testid="metric-container"] {
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border-radius: 8px;
            padding: 1rem;
            border: 1px solid #dee2e6;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown('<h1 class="main-title">💬 Instagram Message System</h1>', unsafe_allow_html=True)
    
    def _initialize_session_state(self):
        """Initialize session state variables"""
        # Authentication states
        if "authenticated" not in st.session_state:
            st.session_state.authenticated = False
        
        if "current_user" not in st.session_state:
            st.session_state.current_user = None
        
        if "show_register" not in st.session_state:
            st.session_state.show_register = False
        
        # Application states
        if "active_tab" not in st.session_state:
            st.session_state.active_tab = "campaigns"
        
        if "usernames" not in st.session_state:
            st.session_state.usernames = []
        
        if "profiles_df" not in st.session_state:
            st.session_state.profiles_df = pd.DataFrame()
        
        if "nationality_classifications" not in st.session_state:
            st.session_state.nationality_classifications = pd.DataFrame()
        
        # Message templates
        if "message_templates" not in st.session_state:
            st.session_state["message_templates"] = {
                "Default Connection Message": {
                    "content": "Hi [first name], I noticed your profile and would love to connect!",
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
                },
                "Professional Introduction": {
                    "content": "Hello [full name], I'm reaching out because I'm impressed with your work in our industry.",
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
                },
                "Business Inquiry": {
                    "content": "Hi [first name], I have a business opportunity that might interest you.",
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
                },
                "Networking Message": {
                    "content": "Hello @[username], I'd like to expand my professional network with people in our field.",
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
                }
            }
            
            # Load user's saved templates if authenticated
            if st.session_state.authenticated and st.session_state.current_user:
                user_id = st.session_state.current_user["id"]
                user_sessions = self.backend.get_user_sessions(user_id)
                
                for session in user_sessions:
                    session_data = session.get("session_data", {})
                    if "message_templates" in session_data:
                        st.session_state["message_templates"].update(session_data["message_templates"])
    
    # =========================================================
    # Main UI Components
    # =========================================================
    
    def render_main_ui(self):
        """Render the main UI based on authentication status"""
        # Check authentication first
        if not st.session_state.authenticated:
            self.render_auth_ui()
            return
        # Global dark theme CSS
        st.markdown("""
        <style>
        /* Global dark theme */
        .main .block-container {
            background-color: #1a1a1a;
            color: white;
        }
        .stApp {
            background-color: #1a1a1a;
        }
        .stApp > header {
            background-color: #2c2c2c;
        }
        
        /* Sidebar dark theme */
        .css-1d391kg {
            background-color: #2c2c2c;
        }
        .css-1d391kg .css-1d391kg {
            background-color: #2c2c2c;
        }
        
        /* Text colors */
        .stMarkdown {
            color: white;
        }
        .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4, .stMarkdown h5, .stMarkdown h6 {
            color: white;
        }
        .stMarkdown p {
            color: #cccccc;
        }
        
        /* Dataframe styling */
        .stDataFrame {
            background-color: #2c2c2c;
        }
        .stDataFrame table {
            background-color: #2c2c2c;
            color: white;
        }
        .stDataFrame th {
            background-color: #444444;
            color: white;
        }
        .stDataFrame td {
            background-color: #2c2c2c;
            color: white;
        }
        
        /* Expander styling */
        .streamlit-expanderHeader {
            background-color: #2c2c2c;
            color: white;
        }
        .streamlit-expanderContent {
            background-color: #2c2c2c;
            color: white;
        }
        
        /* Selectbox styling */
        .stSelectbox > div > div {
            background-color: #2c2c2c !important;
            color: white !important;
            border: 1px solid #444444 !important;
        }
        
        /* Text input styling */
        .stTextInput > div > div > input {
            background-color: #2c2c2c !important;
            color: white !important;
            border: 1px solid #444444 !important;
        }
        
        /* Textarea styling */
        .stTextArea > div > div > textarea {
            background-color: #2c2c2c !important;
            color: white !important;
            border: 1px solid #444444 !important;
        }
        
        /* Number input styling */
        .stNumberInput > div > div > input {
            background-color: #2c2c2c !important;
            color: white !important;
            border: 1px solid #444444 !important;
        }
        
        /* Checkbox styling */
        .stCheckbox > div > div {
            background-color: #2c2c2c !important;
        }
        
        /* Button styling */
        .stButton > button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
            color: white !important;
            border: none !important;
        }
        .stButton > button:hover {
            background: linear-gradient(135deg, #764ba2 0%, #667eea 100%) !important;
        }
        
        /* Tab styling */
        .stTabs [data-baseweb="tab"] {
            background: linear-gradient(135deg, #2c2c2c 0%, #1a1a1a 100%) !important;
            color: #ffffff !important;
            border: 1px solid #444444 !important;
        }
        .stTabs [data-baseweb="tab"]:hover {
            background: linear-gradient(135deg, #3c3c3c 0%, #2a2a2a 100%) !important;
            color: #ffffff !important;
        }
        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
            color: #ffffff !important;
        }
        
        /* Info boxes */
        .stInfo {
            background-color: #2c2c2c;
            border: 1px solid #444444;
        }
        .stSuccess {
            background-color: #2c2c2c;
            border: 1px solid #4CAF50;
        }
        .stWarning {
            background-color: #2c2c2c;
            border: 1px solid #FF9800;
        }
        .stError {
            background-color: #2c2c2c;
            border: 1px solid #f44336;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Render sidebar first (always visible)
        self.render_sidebar()
        
        # Show current tab
        st.markdown(f"<p style='color: #cccccc; margin-bottom: 1rem;'><strong>Current Tab:</strong> {st.session_state.active_tab.title()}</p>", unsafe_allow_html=True)
        
        if st.session_state.active_tab == "campaigns":
            self.render_campaigns_tab()
        elif st.session_state.active_tab == "leads":
            self.render_leads_tab()
    
    def render_campaigns_tab(self):
        """Render campaigns tab with all campaign options"""
        # Custom CSS for campaigns page
        st.markdown("""
        <style>
        .campaigns-header {
            background: #2c2c2c;
            padding: 1rem;
            border-bottom: 1px solid #444444;
            margin-bottom: 1rem;
            color: white;
        }
        .campaign-card {
            background: #2c2c2c;
            padding: 1rem;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.3);
            margin-bottom: 1rem;
            border-left: 4px solid #667eea;
            color: white;
        }
        
        /* Campaigns page specific tab styling */
        .stTabs [data-baseweb="tab"] {
            background: linear-gradient(135deg, #2c2c2c 0%, #1a1a1a 100%) !important;
            color: #ffffff !important;
            border: 1px solid #444444 !important;
        }
        .stTabs [data-baseweb="tab"]:hover {
            background: linear-gradient(135deg, #3c3c3c 0%, #2a2a2a 100%) !important;
            color: #ffffff !important;
        }
        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
            color: #ffffff !important;
        }
        
        /* Input styling for dark theme */
        .stSelectbox > div > div {
            background-color: #2c2c2c !important;
            color: white !important;
        }
        .stTextInput > div > div > input {
            background-color: #2c2c2c !important;
            color: white !important;
            border: 1px solid #444444 !important;
        }
        .stTextArea > div > div > textarea {
            background-color: #2c2c2c !important;
            color: white !important;
            border: 1px solid #444444 !important;
        }
        .stNumberInput > div > div > input {
            background-color: #2c2c2c !important;
            color: white !important;
            border: 1px solid #444444 !important;
        }
        .stCheckbox > div > div {
            background-color: #2c2c2c !important;
        }
        
        /* Button styling */
        .stButton > button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
            color: white !important;
            border: none !important;
        }
        .stButton > button:hover {
            background: linear-gradient(135deg, #764ba2 0%, #667eea 100%) !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Main header
        st.markdown("""
        <div class="campaigns-header">
            <h2 style="margin: 0; color: #ffffff;">🎯 Campaign Management</h2>
        </div>
        """, unsafe_allow_html=True)
        
        # Campaign tabs within campaigns
        campaign_tabs = st.tabs([
            "🏗️ Location Scraping", 
            "📤 Upload Profiles", 
            "🕷️ Profile Scraping", 
            "🏳️ Nationality Classification",
            "💬 Message Templates",
            "📱 Message Campaign"
        ])
        
        with campaign_tabs[0]:
            self.render_location_scraping_tab()
        
        with campaign_tabs[1]:
            self.render_upload_profiles_tab()
        
        with campaign_tabs[2]:
            self.render_profile_scraping_tab()
        
        with campaign_tabs[3]:
            self.render_nationality_classification_tab()
        
        with campaign_tabs[4]:
            self.render_message_templates_tab()
        
        with campaign_tabs[5]:
            self.render_message_campaign_tab()
        
        # Navigation buttons
        self.render_campaign_navigation()
    
    def render_location_scraping_tab(self):
        """Render location scraping tab"""
        st.subheader("🏗️ Fetch usernames from Instagram locations")
        
        # Session name input
        session_name = st.text_input(
            "📝 Session Name", 
            placeholder="e.g., Istanbul Cafes, Ankara Shopping, etc.",
            help="Give a name to this scraping session for easy identification"
        )
        
        # Location scraping form
        col1, col2 = st.columns(2)
        with col1:
            # Instagram Account Selection
            if "instagram_accounts" in st.session_state and st.session_state.instagram_accounts:
                location_account_options = [f"{acc['account_name']} (@{acc['username']})" for acc in st.session_state.instagram_accounts]
                selected_location_account = st.selectbox(
                    "Select Instagram Account",
                    options=location_account_options,
                    help="Choose which Instagram account to use for location scraping"
                )
                
                # Get selected account details
                selected_location_index = location_account_options.index(selected_location_account)
                selected_location_account_info = st.session_state.instagram_accounts[selected_location_index]
                ig_user = selected_location_account_info['username']
                
                st.info(f"📱 Selected: {selected_location_account_info['account_name']} (@{selected_location_account_info['username']})")
            else:
                st.warning("⚠️ No Instagram accounts saved. Please add an account in the sidebar first.")
                ig_user = None
                
        with col2:
            # Password input for selected account
            if "instagram_accounts" in st.session_state and st.session_state.instagram_accounts:
                st.markdown("**Password for selected account:**")
                ig_pass = st.text_input(
                    f"Password for @{selected_location_account_info['username']}",
                    type="password",
                    key=f"location_password_{selected_location_account_info['username']}",
                    help="Enter password to use this account for location scraping"
                )
            else:
                st.warning("⚠️ No Instagram accounts saved.")
                ig_pass = None
        
        loc_text = st.text_area(
            "Location URLs or IDs (one per line)", 
            placeholder="https://www.instagram.com/explore/locations/123456789/\nhttps://www.instagram.com/explore/locations/987654321/"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            max_profiles = st.number_input("Max profiles per location", min_value=1, max_value=1000, value=50)
        with col2:
            st.write("")  # Spacer
        
        if st.button("🚀 Start Location Scraping", key="campaign_location_scrape"):
            locations = [ln.strip() for ln in loc_text.splitlines() if ln.strip()]
            
            if not session_name.strip():
                st.error("❌ Please provide a session name")
            elif not locations:
                st.error("❌ Please provide at least one location URL or ID")
            elif not (ig_user and ig_pass):
                st.error("❌ Please select an Instagram account and enter its password")
            else:
                with st.spinner(f"🔄 Scraping {len(locations)} location(s) using selenium method..."):
                    try:
                        profile_urls = self.backend.selenium_location_scraper(
                            ig_user, ig_pass, locations, max_profiles
                        )
                        
                        if profile_urls == "2FA_REQUIRED":
                            st.warning("🔐 2FA verification required. Please check your phone for SMS code.")
                            st.info("💡 The scraper is waiting for 2FA verification. Please complete the verification in the browser window.")
                        else:
                            # Extract usernames from profile URLs
                            usernames = []
                            for url in profile_urls:
                                if "instagram.com/" in url:
                                    username = url.split("instagram.com/")[-1].rstrip('/')
                                    if username and len(username) > 1:
                                        usernames.append(username)
                            
                            # Results handling
                            if usernames:
                                st.success(f"✅ Successfully collected {len(usernames)} unique usernames!")
                                
                                # Create session info
                                session_id = f"session_{int(datetime.now().timestamp())}"
                                session_info = {
                                    "session_id": session_id,
                                    "session_name": session_name.strip(),
                                    "locations": locations,
                                    "scraped_at": datetime.now().isoformat(),
                                    "method": "selenium",
                                    "usernames_count": len(usernames)
                                }
                                
                                # Initialize session state
                                if "scraping_sessions" not in st.session_state:
                                    st.session_state["scraping_sessions"] = {}
                                if "usernames" not in st.session_state:
                                    st.session_state["usernames"] = []
                                if "username_sessions" not in st.session_state:
                                    st.session_state["username_sessions"] = {}
                                
                                # Save session info
                                st.session_state["scraping_sessions"][session_id] = session_info
                                
                                # Add usernames to global list
                                st.session_state["usernames"].extend(usernames)
                                
                                # Map usernames to session
                                for username in usernames:
                                    st.session_state["username_sessions"][username] = session_id
                                
                                # Save to database with user association
                                if self.backend.supabase_connected and st.session_state.current_user:
                                    try:
                                        # Save scraping session to database
                                        self.backend.save_scraping_session(locations, len(usernames), "selenium")
                                        
                                        # Get nationality data if available
                                        nationality_data = {}
                                        if "nationality_classifications" in st.session_state and isinstance(st.session_state["nationality_classifications"], pd.DataFrame):
                                            for _, row in st.session_state["nationality_classifications"].iterrows():
                                                username = row.get("username")
                                                if username in usernames:
                                                    nationality_data[username] = {
                                                        "nationality": row.get("Nationality", "Unknown"),
                                                        "full_name": row.get("full_name", username)
                                                    }
                                        
                                        # Save user session data
                                        session_data = {
                                            "session_id": session_id,
                                            "session_name": session_name,
                                            "locations": locations,
                                            "username_count": len(usernames),
                                            "scraping_method": "selenium",
                                            "usernames": usernames,
                                            "nationality_data": nationality_data,
                                            "created_at": datetime.now().isoformat()
                                        }
                                        
                                        user_id = st.session_state.current_user["id"]
                                        success, msg = self.backend.save_user_session(user_id, session_name, session_data)
                                        
                                        if success:
                                            st.success("💾 Session saved to your account!")
                                        else:
                                            st.warning(f"⚠️ Session save failed: {msg}")
                                    except Exception as e:
                                        st.warning(f"⚠️ Session save failed: {e}")
                                
                                # Download option
                                csv_data = pd.DataFrame({"username": usernames}).to_csv(index=False)
                                st.download_button(
                                    "📥 Download usernames as CSV",
                                    csv_data,
                                    "instagram_usernames.csv",
                                    "text/csv"
                                )
                            else:
                                st.warning("⚠️ No usernames were collected. Check your locations and try again.")
                    
                    except Exception as e:
                        st.error(f"❌ Scraping failed: {str(e)}")
    
    def render_upload_profiles_tab(self):
        """Render upload profiles tab"""
        st.subheader("📤 Upload Profile Data")
        
        uploaded_file = st.file_uploader(
            "Upload CSV file with profile data", 
            type=['csv'],
            help="CSV should contain columns: username, full_name, biography, followers_count, etc."
        )
        
        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)
                st.success(f"✅ Successfully loaded {len(df)} profiles!")
                
                # Show preview
                st.write("📋 **Data Preview:**")
                st.dataframe(df.head(), use_container_width=True)
                
                # Save to session state
                st.session_state["profiles_df"] = df
                
                # Save to database
                if self.backend.supabase_connected or self.backend.postgres_connected:
                    try:
                        success, message = self.backend.save_profiles_batch(df)
                        if success:
                            st.success(f"💾 {message}")
                        else:
                            st.warning(f"⚠️ {message}")
                    except Exception as e:
                        st.warning(f"⚠️ Database save failed: {e}")
                
            except Exception as e:
                st.error(f"❌ Error reading file: {str(e)}")
    
    def render_profile_scraping_tab(self):
        """Render profile scraping tab"""
        st.subheader("🕷️ Scrape Instagram Profiles")
        
        if "usernames" not in st.session_state or not st.session_state["usernames"]:
            st.warning("⚠️ Please scrape usernames first or upload profile data")
        else:
            usernames = st.session_state["usernames"]
            st.info(f"📊 Ready to scrape {len(usernames)} profiles")
            
            col1, col2 = st.columns(2)
            with col1:
                max_profiles = st.number_input("Max profiles to scrape", min_value=1, max_value=len(usernames), value=min(100, len(usernames)))
            with col2:
                st.write("")  # Spacer
            
            if st.button("🚀 Start Profile Scraping", key="campaign_profile_scrape"):
                with st.spinner("🔄 Scraping profiles with Apify..."):
                    try:
                        results = self.backend.apify_profile_scraper(usernames[:max_profiles])
                        
                        if results:
                            # Convert to DataFrame using the working format from original backup
                            profiles_df = self._normalize_apify_results_to_df(results)
                            
                            if not profiles_df.empty:
                                st.success(f"✅ Successfully scraped {len(profiles_df)} profiles!")
                                
                                # Show bio and following count info
                                bio_count = len(profiles_df[profiles_df['biography'].notna() & (profiles_df['biography'] != '')])
                                following_count = len(profiles_df[profiles_df['following_count'] > 0])
                                
                                st.info(f"📊 **Data Quality**: {bio_count} profiles with bio, {following_count} profiles with following count")
                            else:
                                st.warning("⚠️ No profile data could be extracted. This might be due to:")
                                st.markdown("""
                                - **Private accounts**: Some profiles might be private
                                - **Rate limiting**: Instagram might be blocking requests
                                - **Invalid usernames**: Some usernames might not exist
                                - **Apify limitations**: The scraper might need different input format
                                """)
                                return
                            
                            # Save to session state
                            st.session_state["profiles_df"] = profiles_df
                            
                            # Show results
                            st.write("📋 **Scraped Profiles:**")
                            display_columns = ["username", "full_name", "biography", "followers_count", "following_count", "posts_count", "is_verified"]
                            available_columns = [col for col in display_columns if col in profiles_df.columns]
                            
                            if available_columns:
                                profiles_display = profiles_df[available_columns].copy()
                                
                                # Truncate biography for better display
                                if 'biography' in profiles_display.columns:
                                    profiles_display['biography'] = profiles_display['biography'].apply(
                                        lambda x: (x[:100] + '...') if isinstance(x, str) and len(x) > 100 else x
                                    )
                                
                                profiles_display = profiles_display.sort_values("followers_count", ascending=False)
                                st.dataframe(profiles_display, use_container_width=True)
                            
                            # Save to database with user association
                            if self.backend.supabase_connected and st.session_state.current_user:
                                try:
                                    success, message = self.backend.save_profiles_batch(profiles_df)
                                    if success:
                                        st.success(f"💾 {message}")
                                        
                                        # Get nationality data if available
                                        nationality_data = {}
                                        if "nationality_classifications" in st.session_state and isinstance(st.session_state["nationality_classifications"], pd.DataFrame):
                                            for _, row in st.session_state["nationality_classifications"].iterrows():
                                                username = row.get("username")
                                                if username in usernames[:max_profiles]:
                                                    nationality_data[username] = {
                                                        "nationality": row.get("Nationality", "Unknown"),
                                                        "full_name": row.get("full_name", username)
                                                    }
                                        
                                        # Save user session data for profiles
                                        session_data = {
                                            "session_type": "profile_scraping",
                                            "scraping_method": "apify",
                                            "profile_count": len(profiles_df),
                                            "usernames_scraped": usernames[:max_profiles],
                                            "profiles_data": profiles_df.to_dict('records'),
                                            "nationality_data": nationality_data,
                                            "created_at": datetime.now().isoformat()
                                        }
                                        
                                        user_id = st.session_state.current_user["id"]
                                        session_name = f"Profile Scraping - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                                        
                                        user_success, user_msg = self.backend.save_user_session(user_id, session_name, session_data)
                                        if user_success:
                                            st.success("💾 Profiles saved to your account!")
                                        else:
                                            st.warning(f"⚠️ User session save failed: {user_msg}")
                                    else:
                                        st.warning(f"⚠️ {message}")
                                except Exception as e:
                                    st.warning(f"⚠️ Database save failed: {e}")
                            
                            # Download option
                            csv_data = profiles_df.to_csv(index=False)
                            st.download_button(
                                "📥 Download profiles as CSV",
                                csv_data,
                                "instagram_profiles.csv",
                                "text/csv"
                            )
                        else:
                            st.warning("⚠️ No profiles were scraped. Check your usernames and try again.")
                    
                    except Exception as e:
                        st.error(f"❌ Scraping failed: {str(e)}")
    
    def render_nationality_classification_tab(self):
        """Render nationality classification tab"""
        st.subheader("🏳️ Batch nationality classification (OpenRouter)")
        
        if "profiles_df" not in st.session_state or not isinstance(st.session_state["profiles_df"], pd.DataFrame) or st.session_state["profiles_df"].empty:
            st.warning("⚠️ Please scrape profiles first")
        else:
            profiles_df = st.session_state["profiles_df"]
            st.info(f"📊 Ready to classify {len(profiles_df)} profiles")
            
            # Hidden parameters (fixed values)
            model = "openai/gpt-4o-mini"  # Fixed
            bs2 = 50  # Fixed batch size
            sleep_s = 2.0  # Fixed delay
            
            if st.button("🚀 Start Nationality Classification", key="campaign_classify"):
                with st.spinner("🔄 Classifying nationalities with OpenRouter..."):
                    try:
                        classifications = self.backend.batch_nationality_classification(
                            profiles_df, model, bs2, sleep_s
                        )
                        
                        # Ensure classifications is a DataFrame
                        if isinstance(classifications, list):
                            classifications = pd.DataFrame(classifications)
                        
                        if not classifications.empty:
                            st.success(f"✅ Successfully classified {len(classifications)} profiles!")
                            
                            # Save to session state
                            st.session_state["nationality_classifications"] = classifications
                            
                            # Show results
                            st.write("📋 **Classification Results:**")
                            st.dataframe(classifications, use_container_width=True)
                            
                            # Show nationality distribution
                            nationality_counts = classifications['Nationality'].value_counts()
                            st.write("📊 **Nationality Distribution:**")
                            st.bar_chart(nationality_counts)
                            
                            # Save to database
                            if self.backend.supabase_connected or self.backend.postgres_connected:
                                try:
                                    success, message = self.backend.save_nationality_results(classifications)
                                    if success:
                                        st.success(f"💾 {message}")
                                    else:
                                        st.warning(f"⚠️ {message}")
                                except Exception as e:
                                    st.warning(f"⚠️ Database save failed: {e}")
                            
                            # Download option
                            csv_data = classifications.to_csv(index=False)
                            st.download_button(
                                "📥 Download classifications as CSV",
                                csv_data,
                                "nationality_classifications.csv",
                                "text/csv"
                            )
                        else:
                            st.warning("⚠️ No classifications were generated. Check your profiles and try again.")
                    
                    except Exception as e:
                        st.error(f"❌ Classification failed: {str(e)}")
    
    def render_message_templates_tab(self):
        """Render message templates tab with modern design"""
        # Dark theme CSS for message templates
        st.markdown("""
        <style>
        /* Message Templates Dark Theme */
        .stApp {
            background-color: #1a1a1a !important;
        }
        .main .block-container {
            background-color: #1a1a1a !important;
            color: white !important;
        }
        
        /* Info box styling */
        .stAlert {
            background-color: #2c2c2c !important;
            color: white !important;
            border: 1px solid #444444 !important;
        }
        .stInfo {
            background-color: #2c2c2c !important;
            color: white !important;
            border-left: 4px solid #667eea !important;
        }
        
        /* Button styling */
        .stButton > button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 8px !important;
        }
        .stButton > button:hover {
            background: linear-gradient(135deg, #764ba2 0%, #667eea 100%) !important;
        }
        
        /* Selectbox styling */
        .stSelectbox > div > div {
            background-color: #2c2c2c !important;
            color: white !important;
            border: 1px solid #444444 !important;
        }
        .stSelectbox label {
            color: white !important;
        }
        
        /* Text styling */
        .stMarkdown {
            color: white !important;
        }
        .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4 {
            color: white !important;
        }
        
        /* Text area styling */
        .stTextArea > div > div > textarea {
            background-color: #2c2c2c !important;
            color: white !important;
            border: 1px solid #444444 !important;
            border-radius: 8px !important;
        }
        .stTextArea > div > div > textarea:focus {
            border-color: #667eea !important;
            box-shadow: 0 0 0 1px #667eea !important;
        }
        .stTextArea label {
            color: white !important;
        }
        </style>
        """, unsafe_allow_html=True)
        # Custom CSS for modern message templates design
        st.markdown("""
        <style>
        .message-header {
            background: #2c2c2c;
            padding: 1.5rem;
            border-radius: 12px;
            margin-bottom: 2rem;
            border-left: 4px solid #667eea;
            color: white;
        }
        .message-card {
            background: #2c2c2c;
            border: 1px solid #444444;
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        }
        .message-card-header {
            display: flex;
            align-items: center;
            margin-bottom: 1rem;
        }
        .message-card-icon {
            width: 40px;
            height: 40px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-right: 1rem;
            font-size: 1.2rem;
        }
        .message-card-title {
            font-size: 1.2rem;
            font-weight: 600;
            color: #ffffff;
            margin: 0;
        }
        .message-card-description {
            color: #cccccc;
            font-size: 0.9rem;
            margin: 0.5rem 0 0 0;
        }
        .timing-controls {
            background: #1a1a1a;
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
        }
        .template-selector {
            background: #2c2c2c;
            border: 1px solid #444444;
            border-radius: 8px;
            padding: 1rem;
            margin: 1rem 0;
        }
        .message-preview {
            background: #1a1a1a;
            border: 1px solid #444444;
            border-radius: 12px;
            padding: 1.5rem;
            margin: 1rem 0;
        }
        .profile-preview {
            display: flex;
            align-items: center;
            margin-bottom: 1rem;
        }
        .profile-avatar-preview {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            margin-right: 1rem;
        }
        .profile-info {
            flex: 1;
        }
        .profile-name {
            font-weight: 600;
            color: #ffffff;
            margin: 0;
        }
        .profile-title {
            color: #cccccc;
            font-size: 0.9rem;
            margin: 0;
        }
        .message-input {
            background: #2c2c2c;
            border: 1px solid #444444;
            border-radius: 8px;
            padding: 1rem;
            margin: 1rem 0;
            min-height: 120px;
        }
        .character-counter {
            text-align: right;
            color: #aaaaaa;
            font-size: 0.8rem;
            margin-top: 0.5rem;
        }
        .action-buttons {
            display: flex;
            gap: 0.5rem;
            margin-top: 1rem;
        }
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 6px;
            font-weight: 500;
        }
        .btn-secondary {
            background: #6c757d;
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 6px;
            font-weight: 500;
        }
        .btn-danger {
            background: #dc3545;
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 6px;
            font-weight: 500;
        }
        .toggle-switch {
            position: relative;
            display: inline-block;
            width: 50px;
            height: 24px;
        }
        .toggle-switch input {
            opacity: 0;
            width: 0;
            height: 0;
        }
        .slider {
            position: absolute;
            cursor: pointer;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: #ccc;
            transition: .4s;
            border-radius: 24px;
        }
        .slider:before {
            position: absolute;
            content: "";
            height: 18px;
            width: 18px;
            left: 3px;
            bottom: 3px;
            background-color: white;
            transition: .4s;
            border-radius: 50%;
        }
        input:checked + .slider {
            background-color: #667eea;
        }
        input:checked + .slider:before {
            transform: translateX(26px);
        }
        /* Style Streamlit text area */
        .stTextArea > div > div > textarea {
            background: #1a1a1a !important;
            border: 1px solid #444444 !important;
            border-radius: 12px !important;
            color: #ffffff !important;
            font-size: 1rem !important;
        }
        .stTextArea > div > div > textarea::placeholder {
            color: #888888 !important;
        }
        .stTextArea > div > div > textarea:focus {
            border-color: #667eea !important;
            box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2) !important;
        }
        .message-actions {
            display: flex !important;
            justify-content: space-between !important;
            align-items: center !important;
            margin-top: 1rem !important;
        }
        .character-count {
            color: #aaaaaa !important;
            font-size: 0.9rem !important;
        }
        .action-button {
            background: #dc3545 !important;
            color: white !important;
            border: none !important;
            padding: 0.5rem 1rem !important;
            border-radius: 6px !important;
            cursor: pointer !important;
            font-size: 0.9rem !important;
        }
        .action-button:hover {
            background: #c82333 !important;
        }
        .add-message-btn {
            background: #667eea !important;
            color: white !important;
            border: none !important;
            padding: 1rem 2rem !important;
            border-radius: 8px !important;
            cursor: pointer !important;
            font-size: 1rem !important;
            width: 100% !important;
            margin-top: 1rem !important;
            font-weight: 500 !important;
        }
        .add-message-btn:hover {
            background: #5a6fd8 !important;
        }
        
        /* Template Management Styles */
        .template-section {
            background: #2c2c2c !important;
            border: 1px solid #444444 !important;
            border-radius: 12px !important;
            padding: 1.5rem !important;
            margin: 1rem 0 !important;
        }
        .template-header {
            display: flex !important;
            justify-content: space-between !important;
            align-items: center !important;
            margin-bottom: 1rem !important;
        }
        .template-title {
            color: #ffffff !important;
            font-size: 1.1rem !important;
            font-weight: 600 !important;
            margin: 0 !important;
        }
        .template-list {
            margin: 1rem 0 !important;
        }
        .template-item {
            background: #1a1a1a !important;
            border: 1px solid #555555 !important;
            border-radius: 8px !important;
            padding: 1rem !important;
            margin: 0.5rem 0 !important;
            display: flex !important;
            justify-content: space-between !important;
            align-items: center !important;
        }
        .template-name {
            color: #ffffff !important;
            font-weight: 500 !important;
        }
        .template-preview {
            color: #aaaaaa !important;
            font-size: 0.9rem !important;
            margin-top: 0.5rem !important;
        }
        .template-actions {
            display: flex !important;
            gap: 0.5rem !important;
        }
        .template-btn {
            background: #667eea !important;
            color: white !important;
            border: none !important;
            padding: 0.3rem 0.8rem !important;
            border-radius: 4px !important;
            cursor: pointer !important;
            font-size: 0.8rem !important;
        }
        .template-btn:hover {
            background: #5a6fd8 !important;
        }
        .template-btn-danger {
            background: #dc3545 !important;
        }
        .template-btn-danger:hover {
            background: #c82333 !important;
        }
        .parameter-info {
            background: #1a3a5c !important;
            border: 1px solid #4a90e2 !important;
            border-radius: 8px !important;
            padding: 1rem !important;
            margin: 1rem 0 !important;
        }
        .parameter-title {
            color: #4a90e2 !important;
            font-weight: 600 !important;
            margin-bottom: 0.5rem !important;
        }
        .parameter-list {
            color: #cccccc !important;
            font-size: 0.9rem !important;
        }
        
        /* Simple template selector styling */
        .stSelectbox > div > div > div {
            background: #2c2c2c !important;
            border: 1px solid #444444 !important;
            border-radius: 8px !important;
            color: #ffffff !important;
        }
        .stSelectbox > div > div > div > div {
            color: #ffffff !important;
        }
        .stSelectbox label {
            color: #ffffff !important;
            font-weight: 500 !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Main instruction
        st.markdown("""
        <div class="message-header">
            <h3 style="margin: 0; color: #ffffff;">💬 Engage your target by sending personalized messages</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Simple template selection like in the image (BEFORE textarea widget)
        st.markdown('<div style="margin: 1rem 0;"></div>', unsafe_allow_html=True)
        
        # Initialize default templates if not exists
        if "message_templates" not in st.session_state:
            st.session_state["message_templates"] = {
                "Default Connection Message": {
                    "content": "Hi [full name], I'd love to connect with you and learn more about your work!",
                    "created_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")
                },
                "Professional Introduction": {
                    "content": "Hello [full name], I came across your profile and was impressed by your background. I'd like to connect and potentially explore collaboration opportunities.",
                    "created_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")
                },
                "Business Inquiry": {
                    "content": "Hi [first name], I'm reaching out because I believe we could have some synergies. Would love to connect and discuss potential opportunities.",
                    "created_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")
                },
                "Networking Message": {
                    "content": "Hello [full name], I'm expanding my professional network and would love to connect with talented professionals like yourself.",
                    "created_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")
                }
            }
        
        # Template selection with dropdown and edit button
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            template_options = list(st.session_state["message_templates"].keys())
            selected_template = st.selectbox(
                "Choose template",
                template_options,
                key="selected_template"
            )
        
        with col2:
            if st.button("✏️ Use", key="use_template", use_container_width=True):
                if selected_template and selected_template in st.session_state["message_templates"]:
                    st.session_state["template_force_load"] = True
                    st.session_state["current_template_content"] = st.session_state["message_templates"][selected_template]["content"]
                    st.rerun()
        
        with col3:
            if st.button("➕ New", key="new_template", use_container_width=True):
                st.session_state["show_template_creator"] = True
                st.rerun()
        
        # Template Creator Modal
        if st.session_state.get("show_template_creator", False):
            st.markdown("### 📝 Create New Template")
            
            new_template_name = st.text_input("Template Name", placeholder="e.g., My Custom Template", key="new_template_name")
            new_template_content = st.text_area(
                "Template Content", 
                placeholder="Write your template here... Use [full name], [first name], [username] for personalization",
                height=100,
                key="new_template_content"
            )
            
            col_save, col_cancel = st.columns([1, 1])
            
            with col_save:
                if st.button("💾 Save Template", key="save_new_template", use_container_width=True):
                    if new_template_name and new_template_content:
                        # Save the new template
                        st.session_state["message_templates"][new_template_name] = {
                            "content": new_template_content,
                            "created_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")
                        }
                        
                        # Save templates to user session
                        if st.session_state.authenticated and st.session_state.current_user:
                            user_id = st.session_state.current_user["id"]
                            session_data = {
                                "message_templates": st.session_state["message_templates"],
                                "created_at": datetime.now().isoformat()
                            }
                            self.backend.save_user_session(user_id, "Message Templates", session_data)
                        
                        # Load the new template
                        st.session_state["current_template_content"] = new_template_content
                        st.session_state["template_force_load"] = True
                        st.session_state["show_template_creator"] = False
                        st.success(f"Template '{new_template_name}' created and loaded!")
                        st.rerun()
                    else:
                        st.error("Please enter both template name and content!")
            
            with col_cancel:
                if st.button("❌ Cancel", key="cancel_new_template", use_container_width=True):
                    st.session_state["show_template_creator"] = False
                    st.rerun()
        
        # Set default content based on selected template BEFORE creating the widget
        if selected_template and selected_template in st.session_state["message_templates"]:
            # Force load template if button was clicked or template changed
            if (st.session_state.get("template_force_load", False) or 
                st.session_state.get("last_selected_template") != selected_template):
                
                st.session_state["current_template_content"] = st.session_state["message_templates"][selected_template]["content"]
                st.session_state["last_selected_template"] = selected_template
                st.session_state["template_force_load"] = False
            
            # Initialize on first load
            elif "current_template_content" not in st.session_state:
                st.session_state["current_template_content"] = st.session_state["message_templates"][selected_template]["content"]
        
        
        # Message Composition Section
        st.markdown("### ✏️ Message Composition")
        
        # Set default content based on selected template
        if selected_template and selected_template in st.session_state["message_templates"]:
            if (st.session_state.get("template_force_load", False) or 
                st.session_state.get("last_selected_template") != selected_template):
                
                st.session_state["current_template_content"] = st.session_state["message_templates"][selected_template]["content"]
                st.session_state["last_selected_template"] = selected_template
                st.session_state["template_force_load"] = False
            
            elif "current_template_content" not in st.session_state:
                st.session_state["current_template_content"] = st.session_state["message_templates"][selected_template]["content"]
        
        # Message input area
        default_content = st.session_state.get("current_template_content", "")
        
        message_text = st.text_area(
            "Message Content",
            value=default_content,
            placeholder="Type your message here... Use [full name], [first name], [username] for personalization",
            height=150,
            key="message_textarea",
            help="Enter your message content (max 1900 characters)",
            label_visibility="collapsed"
        )
        
        # Actions row
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        with col1:
            char_count = len(message_text) if message_text else 0
            st.markdown(f'<p style="color: #aaaaaa; font-size: 0.9rem; margin: 0;">{char_count}/1900</p>', unsafe_allow_html=True)
        
        with col2:
            if st.button("🗑️ Clear", key="clear_message", use_container_width=True):
                st.session_state["current_template_content"] = ""
                st.rerun()
        
        with col3:
            if st.button("📋 Copy", key="copy_message", use_container_width=True):
                if message_text:
                    st.success("Message copied to clipboard!")
        
        with col4:
            if st.button("💾 Save", key="save_template", use_container_width=True):
                if message_text:
                    st.session_state["current_template_content"] = message_text
                    st.success("✅ Template saved! You can now use it in Message Campaign tab.")
                else:
                    st.warning("⚠️ Please enter a message template first.")
        
        # Parameter info
        if message_text and any(param in message_text for param in ["[full name]", "[first name]", "[username]"]):
            st.info("💡 **Parameters detected:** This message will be personalized for each recipient using their name and username.")
        
        
        # Account Management Section
        st.markdown("---")
        st.markdown("## 👥 Account Management")
        
        # Create two columns: Available Leads (left) and Target Leads (right)
        col_available, col_target = st.columns([1, 1])
        
        with col_available:
            st.markdown("### 📋 Available Leads")
            
            # Quick actions for adding leads
            col_action1, col_action2 = st.columns(2)
            
            with col_action1:
                if st.button("🔄 Add All Current", key="auto_add_leads", use_container_width=True):
                    # Get all leads from different sources
                    all_leads = []
                    
                    # From usernames
                    current_usernames = st.session_state.get("usernames", [])
                    username_sessions = st.session_state.get("username_sessions", {})
                    scraping_sessions = st.session_state.get("scraping_sessions", {})
            
                    
                    for username in current_usernames:
                        session_id = username_sessions.get(username, "Unknown")
                        session_name = scraping_sessions.get(session_id, {}).get("session_name", "Unknown Session")
                        
                        all_leads.append({
                            "username": username,
                            "full_name": username,
                            "nationality": "Unknown",
                            "session_name": session_name
                        })
                    
                    # From nationality_classifications
                    if "nationality_classifications" in st.session_state and isinstance(st.session_state["nationality_classifications"], pd.DataFrame) and not st.session_state["nationality_classifications"].empty:
                        classifications_df = st.session_state["nationality_classifications"]
                        for _, row in classifications_df.iterrows():
                            username = row.get("username", "")
                            session_id = username_sessions.get(username, "Unknown")
                            session_name = scraping_sessions.get(session_id, {}).get("session_name", "Unknown Session")
                            
                            all_leads.append({
                                "username": username,
                                "full_name": row.get("full_name", username),
                                "nationality": row.get("Nationality", "Unknown"),
                                "session_name": session_name,
                                "profile_pic_url": row.get("profilePicUrl", row.get("profile_pic_url", row.get("profilePictureUrl", row.get("profilePic", row.get("avatar", row.get("photo", ""))))))
                            })
                    
                    # Remove duplicates
                    unique_leads = {}
                    for lead in all_leads:
                        username = lead["username"]
                        if username not in unique_leads:
                            unique_leads[username] = lead
                        else:
                            # Merge data, keeping the best information
                            existing = unique_leads[username]
                            if lead["nationality"] != "Unknown":
                                existing["nationality"] = lead["nationality"]
                            if lead["full_name"] != lead["username"]:
                                existing["full_name"] = lead["full_name"]
                            if lead["session_name"] != "Unknown Session":
                                existing["session_name"] = lead["session_name"]
                    
                    # Save to session state
                    st.session_state["selected_leads"] = list(unique_leads.values())
                    st.success(f"✅ Added {len(unique_leads)} leads to message list!")
                    st.rerun()
            
            with col_action2:
                if st.button("📁 Add by Session", key="add_by_session_btn", use_container_width=True):
                    st.session_state["show_session_selector"] = True
            
            # Session selector modal
            if st.session_state.get("show_session_selector", False):
                if st.session_state.authenticated and st.session_state.current_user:
                    user_sessions = self.backend.get_user_sessions(st.session_state.current_user["id"])
                    
                    if user_sessions:
                        session_names = [s["session_name"] for s in user_sessions]
                        selected_session = st.selectbox("Choose Session:", ["Select..."] + session_names, key="session_modal_select")
                        
                        col_add, col_cancel = st.columns(2)
                        with col_add:
                            if st.button("✅ Add", key="confirm_session_add") and selected_session != "Select...":
                                # Find session and add accounts
                                for session in user_sessions:
                                    if session["session_name"] == selected_session:
                                        session_data = session.get("session_data", {})
                                        added_count = 0
                                        
                                        if "selected_leads" not in st.session_state:
                                            st.session_state["selected_leads"] = []
                                        
                                        # Add from usernames with nationality data
                                        if "usernames" in session_data:
                                            nationality_data = session_data.get("nationality_data", {})
                                            for username in session_data["usernames"]:
                                                existing = any(lead["username"] == username for acc in st.session_state["selected_leads"])
                                                if not existing:
                                                    user_data = nationality_data.get(username, {})
                                                    new_account = {
                                                        "username": username,
                                                        "full_name": user_data.get("full_name", username),
                                                        "nationality": user_data.get("nationality", "Unknown"),
                                                        "session_name": selected_session,
                                                        "profile_pic_url": ""
                                                    }
                                                    st.session_state["selected_leads"].append(new_account)
                                                    added_count += 1
                                        
                                        # Add from profiles
                                        if "profiles_data" in session_data:
                                            for profile in session_data["profiles_data"]:
                                                username = profile.get("username", "")
                                                if username:
                                                    existing = any(lead["username"] == username for acc in st.session_state["selected_leads"])
                                                    if not existing:
                                                        new_account = {
                                                            "username": username,
                                                            "full_name": profile.get("full_name", username),
                                                            "nationality": "Unknown",
                                                            "session_name": selected_session,
                                                            "profile_pic_url": profile.get("profile_pic_url", "")
                                                        }
                                                        st.session_state["selected_leads"].append(new_account)
                                                        added_count += 1
                                        
                                        st.session_state["show_session_selector"] = False
                                        if added_count > 0:
                                            st.success(f"✅ Added {added_count} accounts from {selected_session}")
                                        else:
                                            st.info("ℹ️ All accounts already added")
                                        st.rerun()
                                        break
                        
                        with col_cancel:
                            if st.button("❌ Cancel", key="cancel_session_add"):
                                st.session_state["show_session_selector"] = False
                                st.rerun()
                    else:
                        st.info("📭 No sessions found")
                        if st.button("❌ Close", key="close_no_sessions"):
                            st.session_state["show_session_selector"] = False
                            st.rerun()
                else:
                    st.warning("🔑 Login required")
                    if st.button("❌ Close", key="close_login_required"):
                        st.session_state["show_session_selector"] = False
                        st.rerun()
            
            # Show available leads list with add buttons
            st.markdown("#### 📋 Available Leads:")
            available_leads = self.get_all_leads()
            
            if available_leads:
                # Show first 8 leads with add buttons
                for i, lead in enumerate(available_leads[:8]):
                    col_info, col_add = st.columns([4, 1])
                    
                    with col_info:
                        profile_pic_url = lead.get("profile_pic_url", "")
                        first_letter = lead["username"][0].upper() if lead["username"] else "?"
                        
                        # Simple account display
                        if profile_pic_url and profile_pic_url.strip() and not "scontent" in profile_pic_url:
                            avatar_html = f'<img src="{profile_pic_url}" style="width: 30px; height: 30px; border-radius: 50%; margin-right: 10px; object-fit: cover;">'
                        else:
                            avatar_html = f'<div style="width: 30px; height: 30px; border-radius: 50%; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); display: inline-flex; align-items: center; justify-content: center; color: white; font-weight: bold; margin-right: 10px; font-size: 0.8rem;">{first_letter}</div>'
                        
                        st.markdown(f"""
                        <div style="display: flex; align-items: center; padding: 0.5rem; background: #2c2c2c; border-radius: 8px; margin-bottom: 0.5rem;">
                            {avatar_html}
                            <div>
                                <div style="color: white; font-weight: bold; font-size: 0.9rem;">{lead.get("full_name", lead["username"])}</div>
                                <div style="color: #aaa; font-size: 0.8rem;">@{lead["username"]}</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col_add:
                        # Check if already added
                        is_added = any(lead["username"] == lead["username"] for acc in st.session_state.get("selected_accounts", []))
                        
                        if is_added:
                            st.button("✅", key=f"msg_added_{i}", disabled=True, help="Already added")
                        else:
                            if st.button("➕", key=f"msg_add_{i}", help="Add to targets"):
                                if "selected_accounts" not in st.session_state:
                                    st.session_state["selected_leads"] = []
                                
                                st.session_state["selected_leads"].append(account)
                                st.success(f"✅ Added @{lead['username']}")
                                st.rerun()
                
                if len(available_leads) > 8:
                    st.info(f"📋 Showing 8 of {len(available_leads)} leads. Go to **Leads** tab to see all.")
            else:
                if st.session_state.get("authenticated", False):
                    st.info("📭 No leads available in current session. Login to see historical leads from previous sessions.")
                else:
                    st.info("📭 No leads available. Start scraping to see leads here. Login to see historical leads from previous sessions.")
        
        with col_target:
            st.markdown("### 🎯 Target Leads")
            
            # Initialize selected leads
            if "selected_leads" not in st.session_state:
                st.session_state["selected_leads"] = []
            
            # Bulk actions in compact format
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🗑️ Clear All", key="clear_all_leads", use_container_width=True):
                    st.session_state["selected_leads"] = []
                    st.rerun()
            with col2:
                if st.button("📥 Export", key="export_leads_list", use_container_width=True):
                    df = pd.DataFrame(st.session_state["selected_leads"])
                    csv_data = df.to_csv(index=False)
                    st.download_button(
                        "📥 Download CSV",
                        data=csv_data,
                        file_name="selected_leads.csv",
                        mime="text/csv"
                    )
            
            # Show total count
            total_leads = len(st.session_state["selected_leads"])
            if total_leads > 0:
                st.markdown(f"**{total_leads} leads selected**")
                
                # Display selected leads in a compact format
                for i, lead in enumerate(st.session_state["selected_leads"]):
                    with st.container():
                        cols = st.columns([0.1, 0.6, 0.2, 0.1])
                        
                        # Avatar
                        with cols[0]:
                            profile_pic = lead.get("profile_pic_url", "")
                            if profile_pic and "scontent" not in profile_pic:
                                st.image(profile_pic, width=25)
                            else:
                                # Letter avatar
                                st.markdown(f"""
                                <div style="width: 25px; height: 25px; background: linear-gradient(135deg, #1f1f1f 0%, #2d2d2d 100%);
                                            border-radius: 50%; display: flex; align-items: center; justify-content: center;
                                            color: white; font-weight: bold; font-size: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                                    {lead["username"][0].upper()}
                                </div>
                                """, unsafe_allow_html=True)
                        
                        # Username and full name
                        with cols[1]:
                            st.markdown(f"""
                            <div style="margin-left: 5px;">
                                <div style="font-size: 14px; color: #ffffff;">@{lead["username"]}</div>
                                <div style="font-size: 12px; color: #888888;">{lead.get("full_name", "")}</div>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        # Nationality badge
                        with cols[2]:
                            nationality = lead.get("nationality", "Unknown")
                            badge_color = "#1f1f1f" if nationality == "Unknown" else "#2d2d2d"
                            st.markdown(f"""
                            <div style="background: {badge_color}; padding: 2px 8px; border-radius: 12px; 
                                        font-size: 11px; color: #ffffff; text-align: center;">
                                {nationality}
                            </div>
                            """, unsafe_allow_html=True)
                        
                        # Remove button
                        with cols[3]:
                            if st.button("❌", key=f"remove_{i}", help="Remove from targets"):
                                st.session_state["selected_leads"].pop(i)
                                st.rerun()
            else:
                st.info("No leads selected. Use buttons above to add leads.")
                
            # Show total count
            if len(st.session_state["selected_leads"]) > 0:
                st.write(f"**Total:** {len(st.session_state['selected_leads'])} leads")
            
            # Show leads in compact list format
                leads_to_show = st.session_state["selected_leads"][:10]  # Show max 10
                
                for i, lead in enumerate(leads_to_show):
                    # Compact target lead display
                    col_info, col_remove = st.columns([4, 1])
                    
                    with col_info:
                        profile_pic_url = lead.get("profile_pic_url", "")
                        first_letter = lead["username"][0].upper() if lead["username"] else "?"
                        
                        # Compact account display
                        if profile_pic_url and profile_pic_url.strip() and not "scontent" in profile_pic_url:
                            avatar_html = f'<img src="{profile_pic_url}" style="width: 25px; height: 25px; border-radius: 50%; margin-right: 8px; object-fit: cover;">'
                        else:
                            avatar_html = f'<div style="width: 25px; height: 25px; border-radius: 50%; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); display: inline-flex; align-items: center; justify-content: center; color: white; font-weight: bold; margin-right: 8px; font-size: 0.7rem;">{first_letter}</div>'
                        
                        st.markdown(f"""
                        <div style="display: flex; align-items: center; padding: 0.3rem; background: #2c2c2c; border-radius: 6px; margin-bottom: 0.3rem;">
                            {avatar_html}
                            <div>
                                <div style="color: white; font-weight: bold; font-size: 0.85rem;">{lead.get("full_name", lead["username"])}</div>
                                <div style="color: #aaa; font-size: 0.75rem;">@{lead["username"]}</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col_remove:
                        if st.button("❌", key=f"remove_target_{i}", help="Remove"):
                            st.session_state["selected_leads"].pop(i)
                            st.rerun()
                
                if len(st.session_state["selected_leads"]) > 10:
                    st.info(f"Showing 10 of {len(st.session_state['selected_leads'])} leads")
            else:
                st.info("No leads selected. Use buttons above to add leads.")
        
        # Next Steps Section
        st.markdown("---")
        st.markdown("## 🚀 Next Steps")
        
        selected_count = len(st.session_state.get("selected_leads", []))
        template_saved = bool(st.session_state.get("current_template_content", ""))
        
        if selected_count > 0 and template_saved:
            st.success(f"✅ **Ready for Campaign!** You have {selected_count} target leads and a saved message template.")
            st.info("🎯 **Go to Message Campaign tab** to start sending messages to your selected leads.")
        elif selected_count > 0:
            st.warning(f"⚠️ **{selected_count} leads selected** but no message template saved.")
            st.info("💡 **Save your message template** using the '💾 Save' button above, then go to Message Campaign tab.")
        elif template_saved:
            st.warning("⚠️ **Message template saved** but no target leads selected.")
            st.info("💡 **Select target leads** using the buttons above, then go to Message Campaign tab.")
        else:
            st.info("📝 **Complete these steps:**")
            st.markdown("""
            1. **Write your message template** in the text area above
            2. **Save the template** using the '💾 Save' button
            3. **Select target leads** using the buttons above
            4. **Go to Message Campaign tab** to start your campaign
            """)
    
    def render_campaign_navigation(self):
        """Render campaign navigation buttons"""
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("👥 View Leads", key="view_leads_from_campaigns"):
                st.session_state.active_tab = "leads"
                st.rerun()
        with col2:
            st.write("")  # Spacer
        with col3:
            st.write("")  # Spacer
    
    def render_leads_tab(self):
        """Render leads overview tab with modern leads management interface"""
        # Custom CSS for modern design
        st.markdown("""
        <style>
        .main-header {
            background: #2c2c2c;
            padding: 1rem;
            border-bottom: 1px solid #444444;
            margin-bottom: 1rem;
            color: white;
        }
        .filters-panel {
            background: #2c2c2c;
            padding: 1rem;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.3);
            margin-bottom: 1rem;
            color: white;
        }
        .account-card {
            background: #2c2c2c;
            padding: 1rem;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.3);
            margin-bottom: 0.5rem;
            border-left: 4px solid #667eea;
            color: white;
        }
        .profile-avatar {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            font-size: 1.2rem;
        }
        .tag {
            background: #444444;
            color: #ffffff;
            padding: 0.2rem 0.5rem;
            border-radius: 12px;
            font-size: 0.8rem;
            margin-right: 0.5rem;
        }
        .tag.turk {
            background: #4CAF50;
            color: white;
        }
        .tag.foreign {
            background: #FF9800;
            color: white;
        }
        .tag.session {
            background: #9C27B0;
            color: white;
        }
        .tag.historical {
            background: #ff6b35;
            color: white;
        }
        
        /* Leads page specific tab styling */
        .stTabs [data-baseweb="tab"] {
            background: linear-gradient(135deg, #2c2c2c 0%, #1a1a1a 100%) !important;
            color: #ffffff !important;
            border: 1px solid #444444 !important;
        }
        .stTabs [data-baseweb="tab"]:hover {
            background: linear-gradient(135deg, #3c3c3c 0%, #2a2a2a 100%) !important;
            color: #ffffff !important;
        }
        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
            color: #ffffff !important;
        }
        
        /* Input styling for dark theme */
        .stSelectbox > div > div {
            background-color: #2c2c2c !important;
            color: white !important;
        }
        .stTextInput > div > div > input {
            background-color: #2c2c2c !important;
            color: white !important;
            border: 1px solid #444444 !important;
        }
        .stNumberInput > div > div > input {
            background-color: #2c2c2c !important;
            color: white !important;
            border: 1px solid #444444 !important;
        }
        .stCheckbox > div > div {
            background-color: #2c2c2c !important;
        }
        
        /* Button styling */
        .stButton > button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
            color: white !important;
            border: none !important;
        }
        .stButton > button:hover {
            background: linear-gradient(135deg, #764ba2 0%, #667eea 100%) !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Main header
        st.markdown("""
        <div class="main-header">
            <h2 style="margin: 0; color: #ffffff;">👥 Leads Management</h2>
        </div>
        """, unsafe_allow_html=True)
        
        # User Sessions Overview
        if st.session_state.authenticated and st.session_state.current_user:
            self.render_user_sessions_overview()
        
        # Create two columns: filters (left) and leads list (right)
        col1, col2 = st.columns([1, 2])
        
        with col1:
            self.render_filters_panel()
        
        with col2:
            self.render_leads_list()
        
        # Navigation buttons at bottom
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("⬅️ Back to Campaigns", key="back_to_campaigns"):
                st.session_state.active_tab = "campaigns"
                st.rerun()
        with col2:
            if st.button("🔄 Refresh Data", key="refresh_leads"):
                st.rerun()
        with col3:
            if st.button("🗑️ Clear Session", key="clear_session"):
                for key in ["usernames", "raw_results", "profiles_df", "nationality_classifications", "scraping_sessions", "username_sessions"]:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
    
    def render_filters_panel(self):
        """Render filters panel on the left side"""
        st.markdown("""
        <div class="filters-panel">
            <h4 style="margin-top: 0; color: #ffffff;">🔍 Filters</h4>
        </div>
        """, unsafe_allow_html=True)
        
        # Initialize filter states
        if "filter_favorites" not in st.session_state:
            st.session_state.filter_favorites = False
        if "filter_nationality" not in st.session_state:
            st.session_state.filter_nationality = "All"
        if "filter_followers_min" not in st.session_state:
            st.session_state.filter_followers_min = 0
        if "filter_followers_max" not in st.session_state:
            st.session_state.filter_followers_max = 1000000
        if "search_leads" not in st.session_state:
            st.session_state.search_leads = ""
        if "filter_session" not in st.session_state:
            st.session_state.filter_session = "All"
        
        # Only favorites toggle
        st.session_state.filter_favorites = st.checkbox(
            "⭐ Only favorites", 
            value=st.session_state.filter_favorites,
            key="filter_favorites_checkbox"
        )
        
        st.markdown("---")
        
        # Session filter
        sessions = st.session_state.get("scraping_sessions", {})
        if sessions:
            st.markdown("**📁 Session**")
            session_options = ["All"] + [session_info["session_name"] for session_info in sessions.values()]
            st.session_state.filter_session = st.selectbox(
                "Select session",
                options=session_options,
                index=session_options.index(st.session_state.filter_session) if st.session_state.filter_session in session_options else 0,
                key="session_filter"
            )
            st.markdown("---")
        
        # Nationality filter
        st.markdown("**🏳️ Nationality**")
        nationality_options = ["All", "🇹🇷 TÜRK", "🌍 YABANCI"]
        st.session_state.filter_nationality = st.selectbox(
            "Select nationality",
            options=nationality_options,
            index=nationality_options.index(st.session_state.filter_nationality),
            key="nationality_filter"
        )
        
        st.markdown("---")
        
        # Followers range filter
        st.markdown("**👥 Followers Range**")
        col1, col2 = st.columns(2)
        with col1:
            st.session_state.filter_followers_min = st.number_input(
                "Min",
                min_value=0,
                value=st.session_state.filter_followers_min,
                key="followers_min"
            )
        with col2:
            st.session_state.filter_followers_max = st.number_input(
                "Max",
                min_value=0,
                value=st.session_state.filter_followers_max,
                key="followers_max"
            )
        
        st.markdown("---")
        
        # Search leads
        st.markdown("**🔍 Search Leads**")
        st.session_state.search_leads = st.text_input(
            "Search by username or name",
            value=st.session_state.search_leads,
            key="search_leads_input"
        )
        
        # Clear all filters button
        if st.button("🗑️ Clear All Filters", key="clear_filters"):
            st.session_state.filter_favorites = False
            st.session_state.filter_nationality = "All"
            st.session_state.filter_followers_min = 0
            st.session_state.filter_followers_max = 1000000
            st.session_state.search_leads = ""
            st.session_state.filter_session = "All"
            st.rerun()
    
    def render_leads_list(self):
        """Render modern leads list on the right side"""
        # Get all leads
        all_leads = self.get_all_leads()
        
        if not all_leads:
            if st.session_state.get("authenticated", False):
                st.info("📭 No leads available in current session. Historical leads from previous sessions have been checked but none were found. Start a campaign to collect leads.")
            else:
                st.info("📭 No leads available. Start a campaign to collect leads. Login to see historical leads from previous sessions.")
            return
        
        # Apply filters
        filtered_leads = self.apply_filters(all_leads)
        
        # Check if historical leads are being shown
        historical_count = sum(1 for lead in all_leads if lead.get("source", "").startswith("historical_"))
        current_count = len(all_leads) - historical_count
        
        # Header with search and export
        col1, col2 = st.columns([3, 1])
        with col1:
            if historical_count > 0:
                st.markdown(f"**📋 Leads ({len(filtered_leads)} found)** - {current_count} mevcut session, {historical_count} önceki sessionlardan")
            else:
                st.markdown(f"**📋 Leads ({len(filtered_leads)} found)**")
            
            # Show current session info if loaded
            if st.session_state.get("current_session_name"):
                st.info(f"📄 **Current Session:** {st.session_state['current_session_name']}")
        with col2:
            if st.button("📥 Export", key="export_leads"):
                self.export_leads(filtered_leads)
        
        # Sort options
        sort_options = ["Followers (High to Low)", "Followers (Low to High)", "Name (A-Z)", "Name (Z-A)"]
        sort_by = st.selectbox("Sort by", sort_options, key="sort_leads")
        
        # Apply sorting
        sorted_leads = self.sort_leads(filtered_leads, sort_by)
        
        # Display leads with pagination
        leads_per_page = 10
        total_pages = (len(sorted_leads) + leads_per_page - 1) // leads_per_page
        
        if total_pages > 1:
            # Initialize current page if not set
            if "current_page" not in st.session_state:
                st.session_state["current_page"] = 1
            
            # Reset to page 1 if session was loaded
            if st.session_state.get("session_loaded", False):
                st.session_state["current_page"] = 1
                st.session_state["session_loaded"] = False
            
            page = st.selectbox("Page", range(1, total_pages + 1), key="leads_page", index=st.session_state.get("current_page", 1) - 1)
            start_idx = (page - 1) * leads_per_page
            end_idx = min(start_idx + leads_per_page, len(sorted_leads))
            leads_to_show = sorted_leads[start_idx:end_idx]
            st.caption(f"Showing {start_idx + 1}-{end_idx} of {len(sorted_leads)} leads")
            
            # Update current page in session state
            st.session_state["current_page"] = page
        else:
            leads_to_show = sorted_leads
        
        # Display lead cards
        for lead in leads_to_show:
            self.render_lead_card(lead)
    
    def get_all_leads(self):
        """Get all leads from different sources"""
        all_leads = []
        
        # From usernames
        current_usernames = st.session_state.get("usernames", [])
        username_sessions = st.session_state.get("username_sessions", {})
        scraping_sessions = st.session_state.get("scraping_sessions", {})
        
        for username in current_usernames:
            session_id = username_sessions.get(username, "Unknown")
            session_name = scraping_sessions.get(session_id, {}).get("session_name", "Unknown Session")
            
            all_leads.append({
                "username": username,
                "full_name": username,
                "source": "usernames",
                "followers_count": 0,
                "nationality": "Unknown",
                "session_name": session_name
            })
        
        # From profiles_df
        if "profiles_df" in st.session_state and isinstance(st.session_state["profiles_df"], pd.DataFrame) and not st.session_state["profiles_df"].empty:
            profiles_df = st.session_state["profiles_df"]
            for _, row in profiles_df.iterrows():
                username = row.get("username", "")
                session_id = username_sessions.get(username, "Unknown")
                session_name = scraping_sessions.get(session_id, {}).get("session_name", "Unknown Session")
                
                all_leads.append({
                    "username": username,
                    "full_name": row.get("full_name", username),
                    "source": "profiles",
                    "followers_count": row.get("followers_count", 0),
                    "nationality": "Unknown",
                    "session_name": session_name,
                    "profile_pic_url": row.get("profilePicUrl", row.get("profile_pic_url", ""))
                })
        
        # From nationality_classifications
        if "nationality_classifications" in st.session_state and isinstance(st.session_state["nationality_classifications"], pd.DataFrame) and not st.session_state["nationality_classifications"].empty:
            classifications_df = st.session_state["nationality_classifications"]
            for _, row in classifications_df.iterrows():
                username = row.get("username", "")
                session_id = username_sessions.get(username, "Unknown")
                session_name = scraping_sessions.get(session_id, {}).get("session_name", "Unknown Session")
                
                all_leads.append({
                    "username": username,
                    "full_name": row.get("full_name", username),
                    "source": "classifications",
                    "followers_count": row.get("followers_count", 0),
                    "nationality": row.get("Nationality", "Unknown"),
                    "session_name": session_name,
                    "profile_pic_url": row.get("profilePicUrl", row.get("profile_pic_url", ""))
                })
        
        # If no current leads and user is authenticated, get historical leads
        if not all_leads and st.session_state.get("authenticated", False):
            try:
                historical_leads = self.backend.get_all_historical_leads()
                all_leads.extend(historical_leads)
            except Exception as e:
                print(f"⚠️ Error getting historical leads: {e}")
        
        # Remove duplicates and merge data
        unique_leads = {}
        for lead in all_leads:
            username = lead["username"]
            if username not in unique_leads:
                unique_leads[username] = lead
            else:
                # Merge data, keeping the best information
                existing = unique_leads[username]
                if lead["followers_count"] > existing["followers_count"]:
                    existing["followers_count"] = lead["followers_count"]
                if lead["nationality"] != "Unknown":
                    existing["nationality"] = lead["nationality"]
                if lead["full_name"] != lead["username"]:
                    existing["full_name"] = lead["full_name"]
                if lead["session_name"] != "Unknown Session":
                    existing["session_name"] = lead["session_name"]
                if lead.get("profile_pic_url") and lead["profile_pic_url"].strip():
                    existing["profile_pic_url"] = lead["profile_pic_url"]
        
        return list(unique_leads.values())
    
    def apply_filters(self, leads):
        """Apply filters to leads list"""
        filtered = leads.copy()
        
        # Search filter
        if st.session_state.search_leads:
            search_term = st.session_state.search_leads.lower()
            filtered = [lead for lead in filtered if 
                       search_term in lead["username"].lower() or 
                       search_term in lead["full_name"].lower()]
        
        # Session filter
        if st.session_state.filter_session != "All":
            filtered = [lead for lead in filtered if lead["session_name"] == st.session_state.filter_session]
        
        # Nationality filter
        if st.session_state.filter_nationality != "All":
            nationality = st.session_state.filter_nationality
            if "TÜRK" in nationality:
                filtered = [lead for lead in filtered if "TÜRK" in lead["nationality"].upper()]
            elif "YABANCI" in nationality:
                filtered = [lead for lead in filtered if "YABANCI" in lead["nationality"].upper()]
        
        # Followers range filter
        filtered = [lead for lead in filtered if 
                   st.session_state.filter_followers_min <= lead["followers_count"] <= st.session_state.filter_followers_max]
        
        # Favorites filter (placeholder - would need to implement favorites system)
        if st.session_state.filter_favorites:
            # For now, just return all accounts
            pass
        
        return filtered
    
    def sort_leads(self, leads, sort_by):
        """Sort leads based on selected criteria"""
        if sort_by == "Followers (High to Low)":
            return sorted(leads, key=lambda x: x["followers_count"], reverse=True)
        elif sort_by == "Followers (Low to High)":
            return sorted(leads, key=lambda x: x["followers_count"])
        elif sort_by == "Name (A-Z)":
            return sorted(leads, key=lambda x: x["full_name"].lower())
        elif sort_by == "Name (Z-A)":
            return sorted(leads, key=lambda x: x["full_name"].lower(), reverse=True)
        return leads
    
    def render_lead_card(self, lead):
        """Render individual lead card"""
        # Determine nationality tag
        nationality = lead["nationality"]
        if "TÜRK" in nationality.upper():
            tag_class = "turk"
            tag_text = "🇹🇷 TÜRK"
        elif "YABANCI" in nationality.upper():
            tag_class = "foreign"
            tag_text = "🌍 YABANCI"
        else:
            tag_class = ""
            tag_text = "❓ UNKNOWN"
        
        # Get profile photo or fallback to first letter
        profile_pic_url = lead.get("profile_pic_url", "")
        first_letter = lead["username"][0].upper() if lead["username"] else "?"
        
        # Create avatar HTML - use profile photo if available, otherwise letter
        if profile_pic_url and profile_pic_url.strip():
            avatar_html = f"""
            <img src="{profile_pic_url}" 
                 style="width: 50px; height: 50px; border-radius: 50%; object-fit: cover; border: 2px solid #444;" 
                 alt="Profile Photo"
                 onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">
            <div class="profile-avatar" style="display: none; margin-right: 0;">
                {first_letter}
            </div>
            """
        else:
            avatar_html = f"""
            <div class="profile-avatar">
                {first_letter}
            </div>
            """
        
        # Get session name
        session_name = lead.get("session_name", "Unknown Session")
        
        # Create account card using Streamlit components
        with st.container():
            col1, col2 = st.columns([6, 1])
            
            with col1:
                # Avatar and info columns
                col_avatar, col_info = st.columns([1, 4])
                
                with col_avatar:
                    if profile_pic_url and profile_pic_url.strip() and not "scontent" in profile_pic_url:
                        # Only use non-Instagram CDN URLs (they work better)
                        st.markdown(f"""
                        <img src="{profile_pic_url}" 
                             style="width: 50px; height: 50px; border-radius: 50%; object-fit: cover; border: 2px solid #444;" 
                             alt="Profile Photo"
                             onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">
                        """, unsafe_allow_html=True)
                    else:
                        # For Instagram CDN URLs or no URL, show letter avatar with enhanced styling
                        st.markdown(f"""
                        <div style="width: 50px; height: 50px; border-radius: 50%; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 1.2rem; box-shadow: 0 2px 8px rgba(0,0,0,0.3);">
                            {first_letter}
                        </div>
                        """, unsafe_allow_html=True)
                
                with col_info:
                    st.markdown(f"**{lead['full_name']}**")
                    st.markdown(f"@{lead['username']} • {lead['followers_count']:,} followers")
                    st.markdown(f"📁 {session_name}")
                    
                    # Tags - use simple markdown approach for better compatibility
                    
                    # Use simple text with emojis - most compatible approach
                    tags_text = ""
                    if lead.get("source", "").startswith("historical_"):
                        tags_text += "📅 **Önceki Session** • "
                    
                    if "TÜRK" in nationality.upper():
                        tags_text += "🇹🇷 **TÜRK** • "
                    elif "YABANCI" in nationality.upper():
                        tags_text += "🌍 **YABANCI** • "
                    else:
                        tags_text += "❓ **UNKNOWN** • "
                    
                    tags_text += f"📁 **{session_name}**"
                    
                    st.markdown(tags_text)
            
            with col2:
                # Check if account is already in selected accounts for message templates
                is_already_added = False
                if "selected_accounts" in st.session_state:
                    is_already_added = any(lead["username"] == lead["username"] for acc in st.session_state["selected_leads"])
                
                if is_already_added:
                    st.button("✅", key=f"added_{lead['username']}", help="Already added to message list", disabled=True)
                else:
                    if st.button("➕", key=f"add_{lead['username']}", help="Add to message list"):
                        # Initialize selected_accounts if it doesn't exist
                        if "selected_accounts" not in st.session_state:
                            st.session_state["selected_leads"] = []
                        
                        # Add account to message list
                        message_account = {
                            "username": lead["username"],
                            "full_name": lead.get("full_name", lead["username"]),
                            "nationality": lead.get("nationality", "Unknown"),
                            "session_name": lead.get("session_name", "Unknown Session"),
                            "profile_pic_url": lead.get("profile_pic_url", "")
                        }
                        
                        st.session_state["selected_leads"].append(message_account)
                        st.success(f"✅ Added @{lead['username']} to message list!")
                        st.rerun()
            
            st.markdown("---")
    
    def export_leads(self, leads):
        """Export leads to CSV"""
        if leads:
            df = pd.DataFrame(leads)
            csv_data = df.to_csv(index=False)
            st.download_button(
                "📥 Download CSV",
                data=csv_data,
                file_name="leads_export.csv",
                mime="text/csv"
            )
        else:
            st.warning("No leads to export!")
    
    def render_sidebar(self):
        """Render modern sidebar with dark theme"""
        # User info section
        if st.session_state.authenticated and st.session_state.current_user:
            user = st.session_state.current_user
            st.sidebar.markdown(f"""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 1rem; border-radius: 12px; margin-bottom: 1rem; text-align: center;">
                <div style="color: white; font-size: 1.2rem; font-weight: bold; margin-bottom: 0.5rem;">
                    👤 {user.get('full_name', user.get('username', 'User'))}
                </div>
                <div style="color: rgba(255,255,255,0.8); font-size: 0.9rem;">
                    @{user.get('username', 'unknown')}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Logout button
            if st.sidebar.button("🚪 Logout", use_container_width=True):
                self.logout_user()
        # Custom CSS for modern sidebar
        st.sidebar.markdown("""
        <style>
        .sidebar-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 1.5rem 1rem;
            border-radius: 12px;
            margin-bottom: 2rem;
            text-align: center;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        }
        .sidebar-header h2 {
            color: white;
            margin: 0;
            font-size: 1.5rem;
            font-weight: 600;
        }
        .nav-button {
            background: #2c2c2c;
            color: white;
            border: 1px solid #444444;
            padding: 0.8rem 1rem;
            border-radius: 8px;
            margin-bottom: 0.5rem;
            width: 100%;
            text-align: left;
            font-size: 0.9rem;
            transition: all 0.3s ease;
        }
        .nav-button:hover {
            background: #3c3c3c;
            border-color: #667eea;
        }
        .nav-button.active {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-color: #667eea;
        }
        .stats-card {
            background: #2c2c2c;
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 0.8rem;
            border-left: 4px solid;
            color: white;
        }
        .stats-card.sessions {
            border-left-color: #FFD700;
        }
        .stats-card.profiles {
            border-left-color: #FF69B4;
        }
        .stats-card.classifications {
            border-left-color: #87CEEB;
        }
        .stats-number {
            font-size: 1.5rem;
            font-weight: bold;
            margin-bottom: 0.2rem;
        }
        .stats-label {
            font-size: 0.8rem;
            color: #cccccc;
        }
        .activity-item {
            background: #2c2c2c;
            padding: 0.8rem;
            border-radius: 6px;
            margin-bottom: 0.5rem;
            border-left: 3px solid #667eea;
            color: white;
        }
        .activity-title {
            font-size: 0.9rem;
            font-weight: 600;
            margin-bottom: 0.2rem;
        }
        .activity-subtitle {
            font-size: 0.7rem;
            color: #aaaaaa;
        }
        .clear-button {
            background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%);
            color: white;
            border: none;
            padding: 0.8rem 1rem;
            border-radius: 8px;
            width: 100%;
            font-weight: 600;
            margin-top: 1rem;
        }
        .clear-button:hover {
            background: linear-gradient(135deg, #ee5a52 0%, #ff6b6b 100%);
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Sidebar header
        st.sidebar.markdown("""
        <div class="sidebar-header">
            <h2>📊 Dashboard</h2>
        </div>
        """, unsafe_allow_html=True)
        
        # Navigation buttons
        st.sidebar.markdown("### 🧭 Navigation")
        
        # Campaigns button
        campaigns_active = st.session_state.get("active_tab") == "campaigns"
        if st.sidebar.button("🎯 Campaigns", key="nav_campaigns", use_container_width=True):
            st.session_state.active_tab = "campaigns"
            st.rerun()
        
        # Leads button
        leads_active = st.session_state.get("active_tab") == "leads"
        if st.sidebar.button("👥 Leads", key="nav_leads", use_container_width=True):
            st.session_state.active_tab = "leads"
            st.rerun()
        
        # Instagram Account Management
        st.sidebar.markdown("### 📱 Instagram Accounts")
        st.sidebar.caption("Save account info for later use in campaigns")
        
        # Add new Instagram account
        with st.sidebar.expander("➕ Add Instagram Account", expanded=False):
            new_username = st.text_input("Username", key="new_ig_username")
            new_password = st.text_input("Password", type="password", key="new_ig_password")
            account_name = st.text_input("Account Name (optional)", key="new_ig_account_name")
            
            if st.button("💾 Save Account", key="save_ig_account"):
                if new_username and new_password:
                    # Just save account info without testing connection
                    if "instagram_accounts" not in st.session_state:
                        st.session_state.instagram_accounts = []
                    
                    account_info = {
                        "id": f"ig_{len(st.session_state.instagram_accounts) + 1}",  # Simple ID
                        "username": new_username,
                        "account_name": account_name or new_username,
                        "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "status": "Saved",
                        "password_required": True  # Flag to indicate password needed for use
                    }
                    st.session_state.instagram_accounts.append(account_info)
                    st.success(f"✅ Account saved: {account_name or new_username} (@{new_username})")
                    st.info("💡 **Note**: Account will be tested when you use it in campaigns")
                    st.rerun()
                else:
                    st.warning("Please enter both username and password")
        
        # Show saved accounts
        if "instagram_accounts" in st.session_state and st.session_state.instagram_accounts:
            st.sidebar.markdown("**Saved Accounts:**")
            for i, account in enumerate(st.session_state.instagram_accounts):
                col1, col2 = st.sidebar.columns([3, 1])
                with col1:
                    st.sidebar.write(f"📱 {account['account_name']}")
                    st.sidebar.caption(f"@{account['username']} • {account['status']}")
                with col2:
                    if st.sidebar.button("🗑️", key=f"remove_account_{i}", help="Remove account"):
                        st.session_state.instagram_accounts.pop(i)
                        st.rerun()
        else:
            st.sidebar.info("No Instagram accounts saved")
        
        # Database overview
        st.sidebar.markdown("### 📊 Database Overview")
        
        # Sessions count
        sessions_count = len(st.session_state.get("scraping_sessions", {}))
        st.sidebar.markdown(f"""
        <div class="stats-card sessions">
            <div style="display: flex; align-items: center;">
                <span style="font-size: 1.5rem; margin-right: 0.8rem;">📁</span>
                <div>
                    <div class="stats-number">{sessions_count}</div>
                    <div class="stats-label">Sessions</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Profiles count
        profiles_count = 0
        if "profiles_df" in st.session_state and isinstance(st.session_state["profiles_df"], pd.DataFrame):
            profiles_count = len(st.session_state["profiles_df"])
        
        st.sidebar.markdown(f"""
        <div class="stats-card profiles">
            <div style="display: flex; align-items: center;">
                <span style="font-size: 1.5rem; margin-right: 0.8rem;">👤</span>
                <div>
                    <div class="stats-number">{profiles_count}</div>
                    <div class="stats-label">Profiles</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Classifications count
        classifications_count = 0
        if "nationality_classifications" in st.session_state and isinstance(st.session_state["nationality_classifications"], pd.DataFrame):
            classifications_count = len(st.session_state["nationality_classifications"])
        
        st.sidebar.markdown(f"""
        <div class="stats-card classifications">
            <div style="display: flex; align-items: center;">
                <span style="font-size: 1.5rem; margin-right: 0.8rem;">🏳️</span>
                <div>
                    <div class="stats-number">{classifications_count}</div>
                    <div class="stats-label">Classifications</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Recent activity
        st.sidebar.markdown("### 📈 Recent Activity")
        
        # Show recent sessions
        sessions = st.session_state.get("scraping_sessions", {})
        if sessions:
            for session_id, session_info in list(sessions.items())[-3:]:  # Show last 3
                st.sidebar.markdown(f"""
                <div class="activity-item">
                    <div class="activity-title">{session_info['session_name']}</div>
                    <div class="activity-subtitle">{session_info['usernames_count']} accounts • {session_info['scraped_at'][:10]}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.sidebar.markdown("""
            <div class="activity-item">
                <div class="activity-title">No recent activity</div>
                <div class="activity-subtitle">Start a campaign to see activity</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Clear session button
        st.sidebar.markdown("---")
        if st.sidebar.button("🗑️ Clear Session", key="clear_session_sidebar", use_container_width=True):
            for key in ["usernames", "raw_results", "profiles_df", "nationality_classifications", "scraping_sessions", "username_sessions"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
    
    # =========================================================
    # Utility Methods
    # =========================================================
    
    def show_error(self, message):
        """Show error message"""
        st.error(f"❌ {message}")
    
    def show_success(self, message):
        """Show success message"""
        st.success(f"✅ {message}")
    
    def show_warning(self, message):
        """Show warning message"""
        st.warning(f"⚠️ {message}")
    
    def show_info(self, message):
        """Show info message"""
        st.info(f"ℹ️ {message}")
    
    def create_download_button(self, data, filename, label="📥 Download"):
        """Create download button for data"""
        if isinstance(data, pd.DataFrame):
            csv_data = data.to_csv(index=False)
        else:
            csv_data = data
        
        st.download_button(
            label,
            data=csv_data,
            file_name=filename,
            mime="text/csv"
        )
    
    def create_dataframe_display(self, df, title=None, sort_column=None, ascending=False):
        """Create styled dataframe display"""
        if title:
            st.write(f"**{title}**")
        
        if not df.empty:
            if sort_column and sort_column in df.columns:
                df = df.sort_values(sort_column, ascending=ascending)
            
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No data available")
    
    def create_chart(self, data, chart_type="bar", title=None):
        """Create chart from data"""
        if title:
            st.write(f"**{title}**")
        
        if chart_type == "bar":
            st.bar_chart(data)
        elif chart_type == "pie":
            fig, ax = plt.subplots()
            ax.pie(data.values, labels=data.index, autopct='%1.1f%%')
            st.pyplot(fig)
    
    def _normalize_apify_results_to_df(self, items):
        """
        Normalize Apify results to DataFrame with improved field mapping
        """
        rows = []
        for it in items:
            # Debug: Print item structure for first item
            if len(rows) == 0:
                print("DEBUG - Frontend normalize - First item keys:", list(it.keys()) if isinstance(it, dict) else "Not a dict")
                print("DEBUG - Frontend normalize - Sample item:", json.dumps(it, indent=2, default=str)[:500] + "...")
                print("DEBUG - Frontend normalize - Bio field:", it.get("biography", "NOT_FOUND"))
                print("DEBUG - Frontend normalize - Follows field:", it.get("followsCount", "NOT_FOUND"))
                print("DEBUG - Frontend normalize - Followers field:", it.get("followersCount", "NOT_FOUND"))
            
            # Check for error items and skip them
            if isinstance(it, dict) and it.get("error") == "no_items":
                print(f"DEBUG - Skipping error item: {it.get('errorDescription', 'Unknown error')}")
                continue
            
            # Try multiple possible field names for each data point
            username = (it.get("username") or it.get("userName") or it.get("user_name") or "").strip()
            full_name = (it.get("fullName") or it.get("full_name") or it.get("displayName") or it.get("display_name") or "").strip()
            biography = (it.get("biography") or it.get("bio") or it.get("description") or it.get("biography") or "").strip()
            
            # Try to get numeric values with fallbacks
            followers_count = 0
            following_count = 0
            posts_count = 0
            
            # Followers count
            for field in ["followersCount", "followers_count", "followers", "followerCount"]:
                val = it.get(field)
                if val is not None:
                    try:
                        followers_count = int(val) if isinstance(val, (int, float, str)) and str(val).isdigit() else 0
                        break
                    except:
                        continue
            
            # Following count  
            for field in ["followsCount", "followingCount", "following_count", "following", "followingCount"]:
                val = it.get(field)
                if val is not None:
                    try:
                        following_count = int(val) if isinstance(val, (int, float, str)) and str(val).isdigit() else 0
                        break
                    except:
                        continue
            
            # Posts count
            for field in ["postsCount", "posts_count", "posts", "postCount"]:
                val = it.get(field)
                if val is not None:
                    try:
                        posts_count = int(val) if isinstance(val, (int, float, str)) and str(val).isdigit() else 0
                        break
                    except:
                        continue
            
            rows.append({
                "username": username,
                "full_name": full_name,
                "biography": biography,
                "followers_count": followers_count,
                "following_count": following_count,
                "posts_count": posts_count,
                "profile_pic_url": (it.get("profilePicUrl") or it.get("profile_pic_url") or it.get("profilePictureUrl") or it.get("avatar") or "").strip(),
                "external_url": (it.get("externalUrl") or it.get("external_url") or it.get("website") or "").strip(),
                "is_private": it.get("private", False) or it.get("is_private", False),
                "is_verified": it.get("verified", False) or it.get("is_verified", False),
                "business_category": (it.get("businessCategoryName") or it.get("business_category") or it.get("category") or "").strip(),
                "category": (it.get("category") or it.get("businessCategoryName") or "").strip(),
                "is_business_account": it.get("isBusinessAccount", False) or it.get("is_business_account", False),
                "business_email": (it.get("businessEmail") or it.get("business_email") or it.get("email") or "").strip(),
                "business_phone": (it.get("businessPhoneNumber") or it.get("business_phone") or it.get("phone") or "").strip(),
                "business_address": (it.get("businessAddressJson") or it.get("business_address") or it.get("address") or "").strip(),
                "profile_url": f"https://www.instagram.com/{username}/" if username else "",
                "scrape_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            })
        return pd.DataFrame(rows)
    
    # ===============================================
    # AUTHENTICATION UI METHODS
    # ===============================================
    
    def render_auth_ui(self):
        """Render authentication UI (login/register)"""
        st.markdown("""
        <style>
        /* Dark background for login page */
        .stApp {
            background-color: #1a1a1a !important;
        }
        .main .block-container {
            background-color: #1a1a1a !important;
            color: white !important;
        }
        
        /* Auth container styling */
        .auth-container {
            background: #2c2c2c;
            padding: 2rem;
            border-radius: 16px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.5);
            max-width: 420px;
            margin: 3rem auto;
            border: 1px solid #444444;
        }
        .auth-title {
            text-align: center;
            color: white;
            margin-bottom: 2rem;
            font-size: 2.2rem;
            font-weight: bold;
            text-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }
        
        /* Input styling for dark theme */
        .stTextInput > div > div > input {
            background-color: #3c3c3c !important;
            color: white !important;
            border: 1px solid #555555 !important;
            border-radius: 8px !important;
        }
        .stTextInput > div > div > input:focus {
            border-color: #667eea !important;
            box-shadow: 0 0 0 1px #667eea !important;
        }
        .stTextInput label {
            color: white !important;
        }
        
        /* Button styling */
        .stButton > button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            padding: 0.6rem 1.2rem !important;
            transition: all 0.3s ease !important;
        }
        .stButton > button:hover {
            background: linear-gradient(135deg, #764ba2 0%, #667eea 100%) !important;
            transform: translateY(-1px) !important;
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3) !important;
        }
        
        /* Form styling */
        .stForm {
            background: transparent !important;
        }
        .stForm > div {
            background: transparent !important;
        }
        
        /* Error/Success message styling */
        .stAlert {
            background-color: #3c3c3c !important;
            color: white !important;
            border-radius: 8px !important;
        }
        .stSuccess {
            background-color: rgba(40, 167, 69, 0.2) !important;
            border: 1px solid #28a745 !important;
        }
        .stError {
            background-color: rgba(220, 53, 69, 0.2) !important;
            border: 1px solid #dc3545 !important;
        }
        
        /* Hide Streamlit header and footer */
        header[data-testid="stHeader"] {
            display: none !important;
        }
        .stApp > footer {
            display: none !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        
        # Center the authentication form
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown('<div class="auth-container">', unsafe_allow_html=True)
            
            if not st.session_state.show_register:
                # Login Form
                st.markdown('<h2 class="auth-title">🔐 Giriş Yap</h2>', unsafe_allow_html=True)
                
                with st.form("login_form"):
                    username = st.text_input("Username", placeholder="Enter your username")
                    password = st.text_input("Password", type="password", placeholder="Enter your password")
                    
                    col_login, col_register = st.columns(2)
                    with col_login:
                        login_submit = st.form_submit_button("🚀 Giriş Yap", use_container_width=True)
                    with col_register:
                        if st.form_submit_button("📝 Kayıt Ol", use_container_width=True):
                            st.session_state.show_register = True
                            st.rerun()
                
                if login_submit:
                    if username and password:
                        success, message, user = self.backend.login_user(username, password)
                        if success:
                            st.session_state.authenticated = True
                            st.session_state.current_user = user
                            st.success(f"Welcome back, {user['full_name'] or username}!")
                            st.rerun()
                        else:
                            st.error(message)
                    else:
                        st.error("Please fill in all fields")
            
            else:
                # Register Form
                st.markdown('<h2 class="auth-title">📝 Hesap Oluştur</h2>', unsafe_allow_html=True)
                
                with st.form("register_form"):
                    reg_username = st.text_input("Username", placeholder="Choose a username")
                    reg_email = st.text_input("Email", placeholder="Enter your email")
                    reg_full_name = st.text_input("Full Name", placeholder="Enter your full name")
                    reg_password = st.text_input("Password", type="password", placeholder="Choose a password")
                    reg_confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")
                    
                    col_register, col_back = st.columns(2)
                    with col_register:
                        register_submit = st.form_submit_button("✅ Kayıt Ol", use_container_width=True)
                    with col_back:
                        if st.form_submit_button("⬅️ Giriş'e Dön", use_container_width=True):
                            st.session_state.show_register = False
                            st.rerun()
                
                if register_submit:
                    if reg_username and reg_email and reg_password and reg_confirm_password:
                        if reg_password != reg_confirm_password:
                            st.error("Passwords do not match!")
                        elif len(reg_password) < 6:
                            st.error("Password must be at least 6 characters long!")
                        else:
                            success, message = self.backend.register_user(reg_username, reg_email, reg_password, reg_full_name)
                            if success:
                                st.success("Registration successful! Please login.")
                                st.session_state.show_register = False
                                st.rerun()
                            else:
                                st.error(message)
                    else:
                        st.error("Please fill in all required fields")
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    def logout_user(self):
        """Logout current user"""
        st.session_state.authenticated = False
        st.session_state.current_user = None
        st.session_state.show_register = False
        
        # Clear user-specific session data
        keys_to_clear = ["usernames", "profiles_df", "nationality_classifications", 
                        "scraping_sessions", "username_sessions", "selected_accounts",
                        "message_templates"]
        
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        
        st.rerun()
    
    def load_session_data(self, session):
        """Load session data into current session state"""
        try:
            session_data = session.get("session_data", {})
            
            # Debug: Show what's in the session data
            st.write("🔍 **Debug - Session Data Keys:**", list(session_data.keys()))
            
            # Load profiles data if available
            if "profiles_df" in session_data and session_data["profiles_df"]:
                st.session_state["profiles_df"] = session_data["profiles_df"]
                st.success(f"✅ Loaded {len(session_data['profiles_df'])} profiles from session: {session['session_name']}")
            else:
                st.warning("⚠️ No profiles data found in this session")
            
            # Load usernames if available
            if "usernames" in session_data and session_data["usernames"]:
                st.session_state["usernames"] = session_data["usernames"]
                st.info(f"📋 Loaded {len(session_data['usernames'])} usernames")
            else:
                st.warning("⚠️ No usernames data found in this session")
            
            # Load nationality classifications if available
            if "nationality_classifications" in session_data and session_data["nationality_classifications"]:
                st.session_state["nationality_classifications"] = session_data["nationality_classifications"]
                st.info(f"🌍 Loaded nationality data for {len(session_data['nationality_classifications'])} profiles")
            else:
                st.warning("⚠️ No nationality data found in this session")
            
            # Load raw results if available
            if "raw_results" in session_data and session_data["raw_results"]:
                st.session_state["raw_results"] = session_data["raw_results"]
                st.info(f"📊 Loaded raw scraping results")
            else:
                st.warning("⚠️ No raw results found in this session")
            
            # Set current session info
            st.session_state["current_session_name"] = session['session_name']
            st.session_state["current_session_id"] = session['id']
            
            # Force refresh of leads list and reset pagination
            st.session_state["current_page"] = 1  # Reset to first page
            st.session_state["session_loaded"] = True  # Mark that session was loaded
            
        except Exception as e:
            st.error(f"❌ Error loading session data: {str(e)}")
            st.write("🔍 **Debug - Full Error:**", str(e))
    
    def render_user_sessions_overview(self):
        """Render user's saved sessions overview"""
        user_id = st.session_state.current_user["id"]
        user_sessions = self.backend.get_user_sessions(user_id)
        
        
        if user_sessions:
            st.markdown("""
            <div style="background: #2c2c2c; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
                <h3 style="color: #ffffff; margin: 0 0 1rem 0;">📁 Your Saved Sessions</h3>
            </div>
            """, unsafe_allow_html=True)
            
            # Display sessions in columns
            cols = st.columns(min(3, len(user_sessions)))
            
            for idx, session in enumerate(user_sessions[:3]):  # Show latest 3 sessions
                with cols[idx % 3]:
                    session_data = session.get("session_data", {})
                    session_type = session_data.get("session_type", "scraping")
                    username_count = session_data.get("username_count", session_data.get("profile_count", 0))
                    scraping_method = session_data.get("scraping_method", "unknown")
                    created_at = session.get("created_at", "")
                    
                    if created_at:
                        try:
                            from datetime import datetime
                            created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                            formatted_date = created_date.strftime("%Y-%m-%d %H:%M")
                        except:
                            formatted_date = created_at[:16]
                    else:
                        formatted_date = "Unknown"
                    
                    # Session card with click functionality
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.markdown(f"""
                        <div style="background: #3c3c3c; padding: 1rem; border-radius: 8px; border-left: 4px solid #667eea; margin-bottom: 0.5rem; cursor: pointer;" onclick="selectSession('{session['id']}')">
                            <div style="color: #ffffff; font-weight: bold; margin-bottom: 0.5rem;">
                                📄 {session['session_name']}
                            </div>
                            <div style="color: #aaaaaa; font-size: 0.9rem;">
                                📊 {username_count} accounts
                            </div>
                            <div style="color: #aaaaaa; font-size: 0.9rem;">
                                🛠️ {scraping_method.title()}
                            </div>
                            <div style="color: #aaaaaa; font-size: 0.8rem; margin-top: 0.5rem;">
                                🕒 {formatted_date}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    with col2:
                        if st.button("👁️", key=f"view_session_{session['id']}", help="View Session Data"):
                            # Debug: Show session info
                            st.write("🔍 **Debug - Session Info:**")
                            st.write(f"Session ID: {session['id']}")
                            st.write(f"Session Name: {session['session_name']}")
                            st.write(f"Session Data Keys: {list(session.get('session_data', {}).keys())}")
                            
                            # Load session data
                            self.load_session_data(session)
                            st.rerun()
            
            # Show all sessions in expander
            with st.expander(f"📋 View All Sessions ({len(user_sessions)})"):
                for session in user_sessions:
                    session_data = session.get("session_data", {})
                    username_count = session_data.get("username_count", session_data.get("profile_count", 0))
                    scraping_method = session_data.get("scraping_method", "unknown")
                    created_at = session.get("created_at", "")
                    
                    if created_at:
                        try:
                            created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                            formatted_date = created_date.strftime("%Y-%m-%d %H:%M")
                        except:
                            formatted_date = created_at[:16]
                    else:
                        formatted_date = "Unknown"
                    
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        st.markdown(f"""
                        **{session['session_name']}**  
                        📊 {username_count} accounts • 🛠️ {scraping_method.title()} • 🕒 {formatted_date}
                        """)
                    with col2:
                        if st.button("👁️", key=f"view_session_expander_{session['id']}", help="View Session Data"):
                            # Load session data
                            self.load_session_data(session)
                            st.rerun()
                    with col3:
                        if st.button("🗑️", key=f"delete_session_{session['id']}", help="Delete Session"):
                            success, msg = self.backend.delete_user_session(user_id, session['id'])
                            if success:
                                st.success("Session deleted!")
                                st.rerun()
                            else:
                                st.error(f"Failed to delete: {msg}")
        else:
            st.info("📭 No saved sessions yet. Start scraping to create your first session!")
    
    def render_message_campaign_tab(self):
        """Render Instagram Message Campaign tab (Selenium Automation only)"""
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 1rem; border-radius: 10px; margin-bottom: 2rem; text-align: center;">
            <h2 style="margin: 0; color: #ffffff;">📱 Instagram Message Campaign</h2>
            <p style="margin: 0.5rem 0 0 0; color: #ffffff; opacity: 0.9;">Selenium Automation</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Service selection (only Selenium now)
        service_choice = "Selenium Automation"
        
        # Important notice about following accounts
        st.info("""
        ⚠️ **Important Notice**: 
        - **Account Selection**: Choose from saved Instagram accounts in the sidebar
        - **Password Required**: Enter password for selected account when sending messages
        - **Followed accounts**: Direct "Message" button is available
        - **Non-followed accounts**: System will try three dots menu → "Mesaj Gönder" button
        - **Instagram policy**: Some accounts may require following first
        """)
        
        # Configuration section
        st.markdown("### 🔧 Configuration")
        
        # Selenium Automation Configuration
        col1, col2 = st.columns(2)
        
        with col1:
            # Instagram Account Selection
            if "instagram_accounts" in st.session_state and st.session_state.instagram_accounts:
                account_options = [f"{acc['account_name']} (@{acc['username']})" for acc in st.session_state.instagram_accounts]
                selected_account = st.selectbox(
                    "Select Instagram Account",
                    options=account_options,
                    help="Choose which Instagram account to use for messaging"
                )
                
                # Get selected account details
                selected_index = account_options.index(selected_account)
                selected_account_info = st.session_state.instagram_accounts[selected_index]
                instagram_username = selected_account_info['username']
                instagram_password = "***"  # We don't store passwords, will need to re-authenticate
                
                st.info(f"📱 Selected: {selected_account_info['account_name']} (@{selected_account_info['username']})")
                
                # Password input for selected account
                st.markdown("**Password for selected account:**")
                account_password = st.text_input(
                    f"Password for @{selected_account_info['username']}",
                type="password",
                    key=f"password_{selected_account_info['username']}",
                    help="Enter password to use this account for messaging"
                )
                
                if account_password:
                    instagram_password = account_password
            else:
                st.warning("⚠️ No Instagram accounts saved. Please add an account in the sidebar first.")
                instagram_username = None
                instagram_password = None
                
        with col2:
            # Manual credentials option (fallback)
            st.markdown("**Manual Login (if needed):**")
            manual_username = st.text_input(
                "Manual Username",
                help="Enter username manually if account not in list"
            )
            manual_password = st.text_input(
                "Manual Password", 
                type="password",
                help="Enter password manually if account not in list"
            )
            
            if manual_username and manual_password:
                instagram_username = manual_username
                instagram_password = manual_password
            
            delay_seconds = st.slider(
                "Delay between messages (seconds)",
                min_value=5,
                max_value=60,
                value=10,
                help="Delay between sending messages to avoid rate limiting"
            )
            
            # Message Template Section
            st.markdown("### 📝 Message Template")
            
            # Get message template from message templates tab
            current_template = st.session_state.get("current_template_content", "")
            
            if current_template:
                st.success("✅ Message template loaded from Message Templates tab")
                message_template = st.text_area(
                    "Message Template",
                    value=current_template,
                    height=150,
                    help="Message template from Message Templates tab. You can edit it here if needed.",
                    key="selenium_message_template"
                )
            else:
                st.warning("⚠️ No message template selected. Please go to **Message Templates** tab to create a message template.")
                message_template = st.text_area(
                    "Message Template",
                    value="Merhaba!\n\nInstagram'da profilinizi gördüm ve çok etkileyici!\n\nBen [username] hesabından yazıyorum. Sizinle bağlantı kurmak istiyorum.\n\nUmarım bu mesaj sizi rahatsız etmez.\n\nİyi günler!",
                    height=150,
                    help="Message template with placeholders like [username]. Note: Emojis will be automatically removed to avoid ChromeDriver issues.",
                    key="selenium_message_template"
                )
                st.info("💡 **Tip:** Go to Message Templates tab to create and save your message templates.")
            
            # Target Accounts Section
            st.markdown("### 🎯 Target Accounts")
            
            # Get selected accounts from message templates
            selected_accounts = st.session_state.get("selected_accounts", [])
            
            if selected_accounts:
                st.success(f"✅ {len(selected_accounts)} target accounts selected from Message Templates")
                
                # Show selected accounts in a compact format
                with st.expander(f"📋 View Selected Accounts ({len(selected_accounts)})", expanded=False):
                    for i, lead in enumerate(selected_accounts):
                        col_info, col_remove = st.columns([4, 1])
                        
                        with col_info:
                            profile_pic = lead.get("profile_pic_url", "")
                            if profile_pic and "scontent" not in profile_pic:
                                st.image(profile_pic, width=30)
                            else:
                                first_letter = lead["username"][0].upper() if lead["username"] else "?"
                                st.markdown(f"""
                                <div style="width: 30px; height: 30px; border-radius: 50%; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); display: inline-flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 0.8rem;">{first_letter}</div>
                                """, unsafe_allow_html=True)
                            
                            st.write(f"**{lead.get('full_name', lead['username'])}** (@{lead['username']})")
                        
                        with col_remove:
                            if st.button("❌", key=f"remove_campaign_{i}", help="Remove from campaign"):
                                st.session_state["selected_leads"].pop(i)
                                st.rerun()
                
                # Extract usernames for campaign
                selenium_target_users = [lead["username"] for lead in selected_accounts if lead.get("username")]
                
                # Show summary
                st.info(f"📊 **Campaign Summary:** {len(selenium_target_users)} accounts will receive messages")
                
            else:
                st.warning("⚠️ No target accounts selected. Please go to **Message Templates** tab to select target accounts.")
                st.info("💡 **Tip:** In Message Templates tab, you can add accounts from your scraping sessions or manually select accounts.")
                selenium_target_users = []
            
            # Selenium Send Messages Button
            if st.button("🚀 Start Selenium Message Campaign", type="primary", key="selenium_send_button"):
                if not instagram_username or not instagram_password:
                    st.error("❌ Please enter your Instagram username and password")
                elif not selenium_target_users:
                    st.error("❌ No target accounts selected. Please go to Message Templates tab to select target accounts.")
                elif not message_template:
                    st.error("❌ Please enter a message template")
                else:
                    with st.spinner("🤖 Starting Selenium automation..."):
                        try:
                            # Send messages via Selenium
                            results = self.backend.send_selenium_instagram_messages(
                                usernames=selenium_target_users,
                                message_template=message_template,
                                username=instagram_username,
                                password=instagram_password,
                                delay_seconds=delay_seconds
                            )
                            
                            if results['success']:
                                st.success(f"✅ Selenium campaign completed!")
                                st.success(f"📊 Total sent: {results['total_sent']}")
                                
                                # Check for follow-related failures
                                if 'results' in results and 'failure_details' in results['results']:
                                    follow_failures = [f for f in results['results']['failure_details'] if 'not followed' in f.get('error', '').lower()]
                                    if follow_failures:
                                        st.warning(f"⚠️ **{len(follow_failures)} accounts require following first**")
                                        with st.expander("👥 Accounts that need to be followed"):
                                            for failure in follow_failures:
                                                st.write(f"• @{failure.get('username', 'Unknown')}: {failure.get('error', '')}")
                                
                                # Show detailed results
                                with st.expander("📋 Detailed Results"):
                                    st.json(results['results'])
                            else:
                                error_msg = results['error']
                                if "not followed" in error_msg.lower() or "follow" in error_msg.lower():
                                    st.warning(f"⚠️ **Follow Required**: {error_msg}")
                                    st.info("💡 **Solution**: Some accounts need to be followed first. Check the detailed results below for specific accounts that require following.")
                                elif "three dots" in error_msg.lower() or "manual interaction" in error_msg.lower():
                                    st.warning(f"⚠️ **Manual Action Required**: {error_msg}")
                                    st.info("💡 **Solution**: Some accounts may require manual interaction or following. Check the detailed results below for specific accounts.")
                                else:
                                    st.error(f"❌ Selenium campaign failed: {error_msg}")
                                
                                # Show troubleshooting tips for common errors
                                if "Login failed" in results['error']:
                                    st.warning("""
**🔧 Login Troubleshooting Tips:**

1. **Check your credentials**: Make sure username and password are correct
2. **2FA enabled**: If you have 2FA enabled, the browser will wait for you to enter the code
3. **Account locked**: Instagram might have temporarily locked your account
4. **Wrong password**: Try logging in manually first to verify credentials
5. **Rate limiting**: Wait a few minutes and try again

**💡 Try this:**
- Open Instagram in your browser and log in manually first
- Make sure your account is not restricted
- Check if Instagram sent you any security notifications
                                    """)
                                
                                if 'results' in results and results['results']:
                                    with st.expander("📋 Error Details"):
                                        st.json(results['results'])
                                        
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
        
        with col2:
            # Single Message Section
            st.markdown("### 💬 Single Message")
            
            st.info("💡 **Send a single message to any Instagram account**")
            
            # Single message form
            with st.form("single_message_form"):
                # Account selection for single message
                if "instagram_accounts" in st.session_state and st.session_state.instagram_accounts:
                    single_account_options = [f"{acc['account_name']} (@{acc['username']})" for acc in st.session_state.instagram_accounts]
                    single_selected_account = st.selectbox(
                        "Select Account for Single Message",
                        options=single_account_options,
                        help="Choose which Instagram account to use for this single message"
                    )
                    
                    # Get selected account details
                    single_selected_index = single_account_options.index(single_selected_account)
                    single_selected_account_info = st.session_state.instagram_accounts[single_selected_index]
                    single_instagram_username = single_selected_account_info['username']
                    
                    # Password for single message
                    single_account_password = st.text_input(
                        f"Password for @{single_selected_account_info['username']}",
                        type="password",
                        key=f"single_password_{single_selected_account_info['username']}",
                        help="Enter password to use this account"
                    )
                    
                    single_instagram_password = single_account_password if single_account_password else None
                else:
                    st.warning("⚠️ No Instagram accounts saved. Please add an account in the sidebar first.")
                    single_instagram_username = None
                    single_instagram_password = None
                
                single_target_username = st.text_input(
                    "Target Username",
                    placeholder="Enter Instagram username (without @)",
                    help="The Instagram username to send message to"
                )
                
                single_message_content = st.text_area(
                    "Message Content",
                    placeholder="Type your message here...",
                    height=120,
                    help="The message content to send"
                )
                
                single_send_button = st.form_submit_button("📤 Send Single Message", type="primary")
                
                if single_send_button:
                    if not single_instagram_username or not single_instagram_password:
                        st.error("❌ Please select an Instagram account and enter its password")
                    elif not single_target_username:
                        st.error("❌ Please enter a target username")
                    elif not single_message_content:
                        st.error("❌ Please enter a message content")
                    else:
                        with st.spinner("📤 Sending single message..."):
                            try:
                                # Send single message via Selenium
                                single_results = self.backend.send_selenium_instagram_messages(
                                    usernames=[single_target_username],
                                    message_template=single_message_content,
                                    username=single_instagram_username,
                                    password=single_instagram_password,
                                    delay_seconds=5  # Shorter delay for single message
                                )
                                
                                if single_results['success']:
                                    st.success(f"✅ Message sent successfully to @{single_target_username}!")
                                    if single_results.get('total_sent', 0) > 0:
                                        st.success(f"📊 Message delivered successfully")
                                else:
                                    error_msg = single_results['error']
                                    if "not followed" in error_msg.lower() or "follow" in error_msg.lower():
                                        st.warning(f"⚠️ **Follow Required**: {error_msg}")
                                        st.info("💡 **Solution**: You need to follow @{single_target_username} first before sending messages. Go to their profile and click 'Follow', then try sending the message again.")
                                    elif "three dots" in error_msg.lower() or "manual interaction" in error_msg.lower():
                                        st.warning(f"⚠️ **Manual Action Required**: {error_msg}")
                                        st.info("💡 **Solution**: This account may require manual interaction. Try following the account first, or the account may have restricted messaging.")
                                    else:
                                        st.error(f"❌ Failed to send message: {error_msg}")
                                    
                            except Exception as e:
                                st.error(f"❌ Error sending message: {str(e)}")
            
        
        # End of Selenium Automation Configuration

    # End of render_message_campaign_tab method
