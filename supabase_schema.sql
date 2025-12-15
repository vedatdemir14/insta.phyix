-- Supabase Database Schema for Instagram Scraper
-- Run this in Supabase Dashboard > SQL Editor

-- 1. Instagram Accounts Table
CREATE TABLE IF NOT EXISTS instagram_accounts (
    id VARCHAR(255) PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    display_name VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    last_updated TIMESTAMP DEFAULT NOW()
);

-- 2. Leads Table (for scraped Instagram profiles)
CREATE TABLE IF NOT EXISTS leads (
    id VARCHAR(255) PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    full_name VARCHAR(500),
    bio TEXT,
    followers_count INTEGER DEFAULT 0,
    following_count INTEGER DEFAULT 0,
    posts_count INTEGER DEFAULT 0,
    is_verified BOOLEAN DEFAULT false,
    profile_pic_url TEXT,
    nationality VARCHAR(100),
    confidence DECIMAL(5,2) DEFAULT 0.00,
    session_name VARCHAR(255),
    scraped_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    last_updated TIMESTAMP DEFAULT NOW()
);

-- 3. Sessions Table (for tracking scraping sessions)
CREATE TABLE IF NOT EXISTS sessions (
    id VARCHAR(255) PRIMARY KEY,
    session_name VARCHAR(255) NOT NULL,
    lead_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    last_updated TIMESTAMP DEFAULT NOW()
);

-- 4. Users Table (for authentication)
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(255) PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    last_updated TIMESTAMP DEFAULT NOW()
);

-- 5. Message Templates Table
CREATE TABLE IF NOT EXISTS message_templates (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    last_updated TIMESTAMP DEFAULT NOW()
);

-- 6. Campaigns Table
CREATE TABLE IF NOT EXISTS campaigns (
    id VARCHAR(255) PRIMARY KEY,
    campaign_name VARCHAR(255) NOT NULL,
    campaign_type VARCHAR(100) NOT NULL,
    target_usernames TEXT[], -- Array of usernames
    message_template_id VARCHAR(255),
    instagram_account_id VARCHAR(255),
    status VARCHAR(50) DEFAULT 'pending',
    total_sent INTEGER DEFAULT 0,
    successful INTEGER DEFAULT 0,
    failed INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    last_updated TIMESTAMP DEFAULT NOW()
);

-- Add indexes for better performance
CREATE INDEX IF NOT EXISTS idx_leads_username ON leads(username);
CREATE INDEX IF NOT EXISTS idx_leads_nationality ON leads(nationality);
CREATE INDEX IF NOT EXISTS idx_leads_session_name ON leads(session_name);
CREATE INDEX IF NOT EXISTS idx_leads_created_at ON leads(created_at);

CREATE INDEX IF NOT EXISTS idx_sessions_name ON sessions(session_name);
CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON sessions(created_at);

CREATE INDEX IF NOT EXISTS idx_campaigns_type ON campaigns(campaign_type);
CREATE INDEX IF NOT EXISTS idx_campaigns_status ON campaigns(status);
CREATE INDEX IF NOT EXISTS idx_campaigns_created_at ON campaigns(created_at);

-- Enable Row Level Security (RLS)
ALTER TABLE instagram_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE message_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE campaigns ENABLE ROW LEVEL SECURITY;

-- Create policies to allow all operations (adjust as needed for your security requirements)
CREATE POLICY "Allow all operations on instagram_accounts" ON instagram_accounts
    FOR ALL USING (true);

CREATE POLICY "Allow all operations on leads" ON leads
    FOR ALL USING (true);

CREATE POLICY "Allow all operations on sessions" ON sessions
    FOR ALL USING (true);

CREATE POLICY "Allow all operations on users" ON users
    FOR ALL USING (true);

CREATE POLICY "Allow all operations on message_templates" ON message_templates
    FOR ALL USING (true);

CREATE POLICY "Allow all operations on campaigns" ON campaigns
    FOR ALL USING (true);

-- Insert some default message templates
INSERT INTO message_templates (id, name, content) VALUES
('welcome', 'Hoş Geldin Mesajı', 'Merhaba {username}! Instagram hesabınızı beğendim. Takip etmek ister misiniz? :)'),
('follow_back', 'Takip Et Mesajı', 'Merhaba! Hesabınızı çok beğendim. Karşılıklı takip yapalım mı? :)'),
('collaboration', 'İş Birliği Mesajı', 'Merhaba {username}! İş birliği yapmak ister misiniz? Birlikte güzel projeler çıkarabiliriz! :)'),
('compliment', 'Övgü Mesajı', 'Harika paylaşımlarınız var! Çok beğendim. Devam edin! :)'),
('question', 'Soru Mesajı', 'Merhaba! {username} hesabınızda gördüğüm bir şey hakkında soru sormak istiyorum. Cevap verebilir misiniz?')
ON CONFLICT (id) DO NOTHING;

-- Verify table creation
SELECT 'Tables created successfully' as status;
SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name IN ('instagram_accounts', 'leads', 'sessions', 'users', 'message_templates', 'campaigns');

