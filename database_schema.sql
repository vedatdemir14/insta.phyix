-- Supabase veritabanı şeması
-- Bu SQL kodlarını Supabase SQL Editor'da çalıştırın

-- 1. Links tablosu - Ana link bilgileri
CREATE TABLE IF NOT EXISTS links (
    id BIGSERIAL PRIMARY KEY,
    url TEXT NOT NULL UNIQUE,
    title TEXT,
    domain TEXT NOT NULL,
    content_type TEXT, -- 'page', 'post', 'category', etc.
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_processed BOOLEAN DEFAULT FALSE,
    status_code INTEGER,
    content_length INTEGER
);

-- 2. Keywords tablosu - Link'ler için keyword'ler
CREATE TABLE IF NOT EXISTS keywords (
    id BIGSERIAL PRIMARY KEY,
    link_id BIGINT REFERENCES links(id) ON DELETE CASCADE,
    keyword TEXT NOT NULL,
    relevance_score FLOAT DEFAULT 1.0,
    source TEXT DEFAULT 'ai_generated', -- 'ai_generated', 'manual', 'extracted'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Link_relationships tablosu - Link'ler arası ilişkiler
CREATE TABLE IF NOT EXISTS link_relationships (
    id BIGSERIAL PRIMARY KEY,
    parent_link_id BIGINT REFERENCES links(id) ON DELETE CASCADE,
    child_link_id BIGINT REFERENCES links(id) ON DELETE CASCADE,
    relationship_type TEXT DEFAULT 'internal', -- 'internal', 'external', 'category'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(parent_link_id, child_link_id)
);

-- 4. Scraping_sessions tablosu - Tarama oturumları
CREATE TABLE IF NOT EXISTS scraping_sessions (
    id BIGSERIAL PRIMARY KEY,
    base_url TEXT NOT NULL,
    domain TEXT NOT NULL,
    total_links_found INTEGER DEFAULT 0,
    total_pages_visited INTEGER DEFAULT 0,
    scraping_depth INTEGER DEFAULT 1,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    status TEXT DEFAULT 'running' -- 'running', 'completed', 'failed'
);

-- 5. Session_links tablosu - Oturum-link ilişkisi
CREATE TABLE IF NOT EXISTS session_links (
    id BIGSERIAL PRIMARY KEY,
    session_id BIGINT REFERENCES scraping_sessions(id) ON DELETE CASCADE,
    link_id BIGINT REFERENCES links(id) ON DELETE CASCADE,
    discovered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(session_id, link_id)
);

-- 6. Articles tablosu - Scraping sonuçları ve keyword'ler
CREATE TABLE IF NOT EXISTS articles (
    id BIGSERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    url TEXT NOT NULL UNIQUE,
    keyword TEXT,
    domain TEXT,
    content_type TEXT DEFAULT 'article',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_processed BOOLEAN DEFAULT FALSE,
    status_code INTEGER,
    content_length INTEGER
);

-- İndeksler (performans için)
CREATE INDEX IF NOT EXISTS idx_links_domain ON links(domain);
CREATE INDEX IF NOT EXISTS idx_links_url ON links(url);
CREATE INDEX IF NOT EXISTS idx_links_processed ON links(is_processed);
CREATE INDEX IF NOT EXISTS idx_keywords_link_id ON keywords(link_id);
CREATE INDEX IF NOT EXISTS idx_keywords_keyword ON keywords(keyword);
CREATE INDEX IF NOT EXISTS idx_link_relationships_parent ON link_relationships(parent_link_id);
CREATE INDEX IF NOT EXISTS idx_link_relationships_child ON link_relationships(child_link_id);
CREATE INDEX IF NOT EXISTS idx_scraping_sessions_domain ON scraping_sessions(domain);
CREATE INDEX IF NOT EXISTS idx_session_links_session ON session_links(session_id);

-- RLS (Row Level Security) politikaları
ALTER TABLE links ENABLE ROW LEVEL SECURITY;
ALTER TABLE keywords ENABLE ROW LEVEL SECURITY;
ALTER TABLE link_relationships ENABLE ROW LEVEL SECURITY;
ALTER TABLE scraping_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE session_links ENABLE ROW LEVEL SECURITY;
ALTER TABLE articles ENABLE ROW LEVEL SECURITY;

-- Herkesin okuma/yazma yapabilmesi için (geliştirme aşamasında)
CREATE POLICY "Enable all operations for all users" ON links FOR ALL USING (true);
CREATE POLICY "Enable all operations for all users" ON keywords FOR ALL USING (true);
CREATE POLICY "Enable all operations for all users" ON link_relationships FOR ALL USING (true);
CREATE POLICY "Enable all operations for all users" ON scraping_sessions FOR ALL USING (true);
CREATE POLICY "Enable all operations for all users" ON session_links FOR ALL USING (true);
CREATE POLICY "Enable all operations for all users" ON articles FOR ALL USING (true);

-- Trigger fonksiyonu - updated_at otomatik güncelleme
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger'lar
CREATE TRIGGER update_links_updated_at BEFORE UPDATE ON links
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Örnek veri ekleme (test için)
INSERT INTO links (url, title, domain, content_type, status_code, content_length) 
VALUES 
    ('https://example.com/', 'Example Homepage', 'example.com', 'homepage', 200, 50000),
    ('https://example.com/about', 'About Us', 'example.com', 'page', 200, 30000)
ON CONFLICT (url) DO NOTHING;

-- Keywords örneği
INSERT INTO keywords (link_id, keyword, relevance_score, source)
SELECT l.id, k.keyword, k.relevance_score, k.source
FROM links l,
(VALUES 
    ('homepage', 1.0, 'ai_generated'),
    ('main page', 0.9, 'ai_generated'),
    ('about', 0.8, 'ai_generated'),
    ('company', 0.7, 'ai_generated')
) AS k(keyword, relevance_score, source)
WHERE l.url = 'https://example.com/';


