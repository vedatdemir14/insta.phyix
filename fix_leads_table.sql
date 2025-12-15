-- Fix leads table by adding missing bio column
-- Run this in Supabase Dashboard > SQL Editor

-- First, check if leads table exists and its structure
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'leads' AND table_schema = 'public';

-- Add bio column if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'leads' AND column_name = 'bio' AND table_schema = 'public'
    ) THEN
        ALTER TABLE leads ADD COLUMN bio TEXT;
        RAISE NOTICE 'Added bio column to leads table';
    ELSE
        RAISE NOTICE 'Bio column already exists in leads table';
    END IF;
END $$;

-- Also ensure other required columns exist
DO $$ 
BEGIN
    -- Add followers_count if missing
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'leads' AND column_name = 'followers_count' AND table_schema = 'public'
    ) THEN
        ALTER TABLE leads ADD COLUMN followers_count INTEGER DEFAULT 0;
        RAISE NOTICE 'Added followers_count column to leads table';
    END IF;
    
    -- Add following_count if missing
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'leads' AND column_name = 'following_count' AND table_schema = 'public'
    ) THEN
        ALTER TABLE leads ADD COLUMN following_count INTEGER DEFAULT 0;
        RAISE NOTICE 'Added following_count column to leads table';
    END IF;
    
    -- Add posts_count if missing
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'leads' AND column_name = 'posts_count' AND table_schema = 'public'
    ) THEN
        ALTER TABLE leads ADD COLUMN posts_count INTEGER DEFAULT 0;
        RAISE NOTICE 'Added posts_count column to leads table';
    END IF;
    
    -- Add is_verified if missing
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'leads' AND column_name = 'is_verified' AND table_schema = 'public'
    ) THEN
        ALTER TABLE leads ADD COLUMN is_verified BOOLEAN DEFAULT false;
        RAISE NOTICE 'Added is_verified column to leads table';
    END IF;
    
    -- Add profile_pic_url if missing
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'leads' AND column_name = 'profile_pic_url' AND table_schema = 'public'
    ) THEN
        ALTER TABLE leads ADD COLUMN profile_pic_url TEXT;
        RAISE NOTICE 'Added profile_pic_url column to leads table';
    END IF;
    
    -- Add nationality if missing
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'leads' AND column_name = 'nationality' AND table_schema = 'public'
    ) THEN
        ALTER TABLE leads ADD COLUMN nationality VARCHAR(100);
        RAISE NOTICE 'Added nationality column to leads table';
    END IF;
    
    -- Add confidence if missing
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'leads' AND column_name = 'confidence' AND table_schema = 'public'
    ) THEN
        ALTER TABLE leads ADD COLUMN confidence DECIMAL(5,2) DEFAULT 0.00;
        RAISE NOTICE 'Added confidence column to leads table';
    END IF;
    
    -- Add session_name if missing
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'leads' AND column_name = 'session_name' AND table_schema = 'public'
    ) THEN
        ALTER TABLE leads ADD COLUMN session_name VARCHAR(255);
        RAISE NOTICE 'Added session_name column to leads table';
    END IF;
    
    -- Add scraped_at if missing
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'leads' AND column_name = 'scraped_at' AND table_schema = 'public'
    ) THEN
        ALTER TABLE leads ADD COLUMN scraped_at TIMESTAMP DEFAULT NOW();
        RAISE NOTICE 'Added scraped_at column to leads table';
    END IF;
    
    -- Add last_updated if missing
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'leads' AND column_name = 'last_updated' AND table_schema = 'public'
    ) THEN
        ALTER TABLE leads ADD COLUMN last_updated TIMESTAMP DEFAULT NOW();
        RAISE NOTICE 'Added last_updated column to leads table';
    END IF;
END $$;

-- Verify the table structure
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns 
WHERE table_name = 'leads' AND table_schema = 'public'
ORDER BY ordinal_position;
