-- Final fix for leads table - correct data types
-- Run this in Supabase Dashboard > SQL Editor

-- First, check current table structure
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'leads' AND table_schema = 'public'
ORDER BY ordinal_position;

-- Drop and recreate leads table with correct data types
DROP TABLE IF EXISTS leads CASCADE;

CREATE TABLE leads (
    id VARCHAR(255) PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    full_name VARCHAR(500),
    biography TEXT,
    followers_count INTEGER DEFAULT 0,
    following_count INTEGER DEFAULT 0,
    posts_count INTEGER DEFAULT 0,
    is_verified BOOLEAN DEFAULT false,
    profile_pic_url TEXT,
    nationality VARCHAR(100),
    confidence DECIMAL(5,2) DEFAULT 0.00,  -- Changed to DECIMAL for float values
    session_name VARCHAR(255),
    scraped_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    last_updated TIMESTAMP DEFAULT NOW()
);

-- Add indexes
CREATE INDEX idx_leads_username ON leads(username);
CREATE INDEX idx_leads_nationality ON leads(nationality);
CREATE INDEX idx_leads_session_name ON leads(session_name);
CREATE INDEX idx_leads_created_at ON leads(created_at);

-- Enable RLS
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;

-- Create policy
CREATE POLICY "Allow all operations on leads" ON leads
    FOR ALL USING (true);

-- Verify table creation
SELECT 'Leads table recreated successfully' as status;
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'leads' AND table_schema = 'public'
ORDER BY ordinal_position;

