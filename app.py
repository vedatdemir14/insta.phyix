# --- Windows asyncio policy fix (must be at the very top) ---
import sys, asyncio
if sys.platform.startswith("win"):
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    except Exception:
        pass

# -------------------------------------------------------------
import streamlit as st
from backend import InstagramBackend
from frontend import InstagramFrontend

# =========================================================
# Configuration - Now uses environment variables
# =========================================================
# Configuration is now handled in InstagramBackend.__init__()
# using environment variables from .env file

# =========================================================
# Main Application
# =========================================================

def main():
    """Main application entry point"""
    try:
        # Initialize backend (now uses environment variables)
        backend = InstagramBackend()
        
        # Create user tables if they don't exist
        try:
            backend.create_user_tables()
        except Exception as e:
            print(f"⚠️ User tables creation warning: {e}")
        
        # Initialize frontend
        frontend = InstagramFrontend(backend)
        
        # Render main UI
        frontend.render_main_ui()
    
    except Exception as e:
        st.error(f"❌ Application error: {str(e)}")
        st.error("Please check your configuration and try again.")

if __name__ == "__main__":
    main()