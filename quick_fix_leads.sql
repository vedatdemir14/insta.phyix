-- Quick fix for leads table - add missing columns
-- Run this in Supabase Dashboard > SQL Editor

-- Add bio column (as biography to match instagram_profiles table)
ALTER TABLE leads ADD COLUMN IF NOT EXISTS biography TEXT;

-- Add other missing columns
ALTER TABLE leads ADD COLUMN IF NOT EXISTS followers_count INTEGER DEFAULT 0;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS following_count INTEGER DEFAULT 0;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS posts_count INTEGER DEFAULT 0;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS is_verified BOOLEAN DEFAULT false;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS profile_pic_url TEXT;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS nationality VARCHAR(100);
ALTER TABLE leads ADD COLUMN IF NOT EXISTS confidence DECIMAL(5,2) DEFAULT 0.00;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS session_name VARCHAR(255);
ALTER TABLE leads ADD COLUMN IF NOT EXISTS scraped_at TIMESTAMP DEFAULT NOW();
ALTER TABLE leads ADD COLUMN IF NOT EXISTS last_updated TIMESTAMP DEFAULT NOW();

-- Verify the table structure
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'leads' AND table_schema = 'public'
ORDER BY ordinal_position;

