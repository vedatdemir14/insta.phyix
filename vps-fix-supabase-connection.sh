#!/bin/bash
# Fix Supabase connection issue on VPS

cd /opt/instagram-scraper

echo "🔍 Checking .env file..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found! Creating it..."
    cat > .env << 'ENVEOF'
SUPABASE_URL=https://rltkqtlinpsueyaervdv.supabase.co
SUPABASE_API_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJsdGtxdGxpbnBzdWV5YWVydmR2Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NzU3NTk4NSwiZXhwIjoyMDczMTUxOTg1fQ.doT1nxL0izQRpCqzAY-StRFrzqRRuRyiKhZDwKfk_fI
APIFY_API_TOKEN=apify_api_VeivXy54nUuP7jP3zdPStvnY1bdy6P12ohvn
OPENROUTER_API_KEY=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
UNIPILE_API_KEY=k8IpFvnp.1H5f5alAgW2gK5M+J4GvW2M1lavbPHdsZfUGXBbEF+U=
UNIPILE_BASE_URL=https://api21.unipile.com:15121
DEEPL_API_KEY=721f4e0a-7600-425a-9bd4-7c4282e7770c:fx
ENVEOF
    echo "✅ .env file created"
else
    echo "✅ .env file exists"
    echo "📋 Checking SUPABASE_URL..."
    if grep -q "SUPABASE_URL" .env; then
        echo "✅ SUPABASE_URL found"
        grep "SUPABASE_URL" .env
    else
        echo "❌ SUPABASE_URL not found in .env"
        echo "📝 Adding SUPABASE_URL..."
        echo "SUPABASE_URL=https://rltkqtlinpsueyaervdv.supabase.co" >> .env
    fi
    
    echo "📋 Checking SUPABASE_API_KEY..."
    if grep -q "SUPABASE_API_KEY" .env; then
        echo "✅ SUPABASE_API_KEY found"
    else
        echo "❌ SUPABASE_API_KEY not found in .env"
        echo "📝 Adding SUPABASE_API_KEY..."
        echo "SUPABASE_API_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJsdGtxdGxpbnBzdWV5YWVydmR2Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NzU3NTk4NSwiZXhwIjoyMDczMTUxOTg1fQ.doT1nxL0izQRpCqzAY-StRFrzqRRuRyiKhZDwKfk_fI" >> .env
    fi
fi

echo ""
echo "🔄 Restarting backend container..."
docker compose restart backend

echo ""
echo "⏳ Waiting 5 seconds..."
sleep 5

echo ""
echo "📊 Checking backend logs..."
docker compose logs --tail=20 backend

echo ""
echo "🧪 Testing Supabase connection..."
docker compose exec backend python3 -c "
import os
from supabase import create_client, Client

url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_API_KEY')

if url and key:
    try:
        supabase: Client = create_client(url, key)
        print('✅ Supabase client created successfully')
        # Test connection
        result = supabase.table('users').select('count').execute()
        print('✅ Supabase connection test successful')
    except Exception as e:
        print(f'❌ Supabase connection failed: {e}')
else:
    print('❌ SUPABASE_URL or SUPABASE_API_KEY not set')
"


