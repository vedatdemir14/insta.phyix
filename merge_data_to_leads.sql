-- Merge Instagram Profiles and Nationality Classifications to Leads Table
-- Bu script mevcut verileri leads tablosuna birleştirir

-- 1. Önce mevcut leads tablosunu temizle (isteğe bağlı)
-- DELETE FROM leads;

-- 2. Instagram profiles ve nationality classifications verilerini birleştir
INSERT INTO leads (
    id,
    username,
    full_name,
    bio,
    followers_count,
    following_count,
    posts_count,
    is_verified,
    profile_pic_url,
    nationality,
    confidence,
    session_name,
    scraped_at,
    created_at,
    last_updated
)
SELECT 
    -- Unique ID oluştur
    'lead_' || ip.id::text as id,
    ip.username,
    ip.full_name,
    ip.biography as bio,
    COALESCE(ip.followers_count, 0) as followers_count,
    COALESCE(ip.following_count, 0) as following_count,
    COALESCE(ip.posts_count, 0) as posts_count,
    COALESCE(ip.is_verified, false) as is_verified,
    COALESCE(ip.profile_pic_url, '') as profile_pic_url,
    COALESCE(nc.nationality, 'UNKNOWN') as nationality,
    COALESCE(nc.confidence, 0.0) as confidence,
    COALESCE(ip.session_id, 'unknown_session') as session_name,
    COALESCE(ip.scraped_at, NOW()) as scraped_at,
    NOW() as created_at,
    NOW() as last_updated
FROM instagram_profiles ip
LEFT JOIN nationality_classifications nc ON ip.username = nc.username
WHERE ip.username IS NOT NULL
ON CONFLICT (id) DO UPDATE SET
    full_name = EXCLUDED.full_name,
    bio = EXCLUDED.bio,
    followers_count = EXCLUDED.followers_count,
    following_count = EXCLUDED.following_count,
    posts_count = EXCLUDED.posts_count,
    is_verified = EXCLUDED.is_verified,
    profile_pic_url = EXCLUDED.profile_pic_url,
    nationality = EXCLUDED.nationality,
    confidence = EXCLUDED.confidence,
    session_name = EXCLUDED.session_name,
    scraped_at = EXCLUDED.scraped_at,
    last_updated = NOW();

-- 3. Session bilgilerini güncelle
INSERT INTO sessions (id, session_name, lead_count, created_at, last_updated)
SELECT 
    'session_' || session_id as id,
    session_id as session_name,
    COUNT(*) as lead_count,
    MIN(created_at) as created_at,
    NOW() as last_updated
FROM leads 
WHERE session_name IS NOT NULL
GROUP BY session_id
ON CONFLICT (id) DO UPDATE SET
    lead_count = EXCLUDED.lead_count,
    last_updated = NOW();

-- 4. Sonuçları kontrol et
SELECT 
    'Leads Count' as metric,
    COUNT(*) as value
FROM leads
UNION ALL
SELECT 
    'Sessions Count' as metric,
    COUNT(*) as value
FROM sessions
UNION ALL
SELECT 
    'Nationality Distribution' as metric,
    COUNT(*) as value
FROM leads 
WHERE nationality IS NOT NULL
GROUP BY nationality;

-- 5. Örnek veri göster
SELECT 
    username,
    full_name,
    bio,
    nationality,
    confidence,
    session_name
FROM leads 
ORDER BY created_at DESC 
LIMIT 10;

