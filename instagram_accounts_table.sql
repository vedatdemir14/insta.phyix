-- Instagram Accounts Table Creation SQL
-- Run this in Supabase Dashboard > SQL Editor

CREATE TABLE IF NOT EXISTS instagram_accounts (
    id VARCHAR(255) PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    display_name VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    last_updated TIMESTAMP DEFAULT NOW()
);

-- Add RLS (Row Level Security) policies if needed
ALTER TABLE instagram_accounts ENABLE ROW LEVEL SECURITY;

-- Create policy to allow all operations (adjust as needed for your security requirements)
CREATE POLICY "Allow all operations on instagram_accounts" ON instagram_accounts
    FOR ALL USING (true);

-- Insert a test record (optional)
-- INSERT INTO instagram_accounts (id, username, password, display_name) 
-- VALUES ('test_account_1', 'test_user', 'test_password', 'Test User');

-- Verify table creation
SELECT * FROM instagram_accounts;
