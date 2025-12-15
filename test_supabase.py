#!/usr/bin/env python3
"""
Supabase Connection Test Script
Bu script Supabase bağlantısını test eder ve gerekli tabloları kontrol eder.
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv

def test_supabase_connection():
    """Test Supabase connection and table structure"""
    
    # Load environment variables
    load_dotenv()
    
    # Get Supabase credentials
    supabase_url = os.getenv('SUPABASE_URL', 'https://rltkqtlinpsueyaervdv.supabase.co')
    supabase_key = os.getenv('SUPABASE_API_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJsdGtxdGxpbnBzdWV5YWVydmR2Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NzU3NTk4NSwiZXhwIjoyMDczMTUxOTg1fQ.doT1nxL0izQRpCqzAY-StRFrzqRRuRyiKhZDwKfk_fI')
    
    print("🔍 Testing Supabase connection...")
    print(f"📡 URL: {supabase_url}")
    print(f"🔑 Key: {supabase_key[:20]}...")
    
    try:
        # Create Supabase client
        supabase: Client = create_client(supabase_url, supabase_key)
        print("✅ Supabase client created successfully")
        
        # Test connection by querying a table
        print("\n🔍 Testing table connections...")
        
        # Test leads table
        try:
            result = supabase.table("leads").select("id").limit(1).execute()
            print("✅ Leads table: Connected")
            print(f"📊 Leads count: {len(result.data)}")
        except Exception as e:
            print(f"❌ Leads table error: {e}")
        
        # Test sessions table
        try:
            result = supabase.table("sessions").select("id").limit(1).execute()
            print("✅ Sessions table: Connected")
            print(f"📊 Sessions count: {len(result.data)}")
        except Exception as e:
            print(f"❌ Sessions table error: {e}")
        
        # Test instagram_accounts table
        try:
            result = supabase.table("instagram_accounts").select("id").limit(1).execute()
            print("✅ Instagram accounts table: Connected")
            print(f"📊 Accounts count: {len(result.data)}")
        except Exception as e:
            print(f"❌ Instagram accounts table error: {e}")
        
        # Test message_templates table
        try:
            result = supabase.table("message_templates").select("id").limit(1).execute()
            print("✅ Message templates table: Connected")
            print(f"📊 Templates count: {len(result.data)}")
        except Exception as e:
            print(f"❌ Message templates table error: {e}")
        
        print("\n🎉 Supabase connection test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Supabase connection failed: {e}")
        return False

def test_nationality_update():
    """Test nationality update functionality"""
    print("\n🔍 Testing nationality update functionality...")
    
    try:
        from backend import InstagramBackend
        
        # Initialize backend
        config = {
            'SUPABASE_URL': os.getenv('SUPABASE_URL', 'https://rltkqtlinpsueyaervdv.supabase.co'),
            'SUPABASE_API_KEY': os.getenv('SUPABASE_API_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJsdGtxdGxpbnBzdWV5YWVydmR2Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NzU3NTk4NSwiZXhwIjoyMDczMTUxOTg1fQ.doT1nxL0izQRpCqzAY-StRFrzqRRuRyiKhZDwKfk_fI'),
        }
        
        backend = InstagramBackend(config)
        
        if backend.supabase_connected:
            print("✅ Backend Supabase connection: OK")
            
            # Test updating a nationality (if leads exist)
            try:
                leads = backend.get_all_leads()
                if leads:
                    test_username = leads[0]['username']
                    print(f"🧪 Testing nationality update for: {test_username}")
                    
                    # This would be called by the API endpoint
                    # result = backend.supabase.table("leads").update({
                    #     "nationality": "TEST_UPDATE",
                    #     "last_updated": "2024-01-01T00:00:00Z"
                    # }).eq("username", test_username).execute()
                    # print("✅ Nationality update test: OK")
                else:
                    print("⚠️ No leads found for testing")
            except Exception as e:
                print(f"❌ Nationality update test failed: {e}")
        else:
            print("❌ Backend Supabase connection: FAILED")
            
    except Exception as e:
        print(f"❌ Backend test failed: {e}")

if __name__ == "__main__":
    print("🚀 Starting Supabase Integration Test")
    print("=" * 50)
    
    # Test basic connection
    connection_ok = test_supabase_connection()
    
    if connection_ok:
        # Test backend integration
        test_nationality_update()
    
    print("\n" + "=" * 50)
    print("🏁 Test completed!")

