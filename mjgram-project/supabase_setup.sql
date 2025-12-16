-- ========================================
-- MJgram Supabase 데이터베이스 설정
-- ========================================

-- 1. Users 테이블
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT UNIQUE NOT NULL,
    username TEXT UNIQUE NOT NULL,
    avatar TEXT,
    bio TEXT,
    github_username TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 2. Posts 테이블
CREATE TABLE IF NOT EXISTS posts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    type TEXT NOT NULL CHECK (type IN ('image', 'code', 'project')),
    content TEXT,
    image_url TEXT,
    code TEXT,
    language TEXT,
    github_repo_url TEXT,
    tech_stack TEXT,
    github_data JSONB,
    likes_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 3. Likes 테이블
CREATE TABLE IF NOT EXISTS likes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    post_id UUID REFERENCES posts(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(post_id, user_id)
);

-- 4. Comments 테이블
CREATE TABLE IF NOT EXISTS comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    post_id UUID REFERENCES posts(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ========================================
-- 함수: 좋아요 증가
-- ========================================
CREATE OR REPLACE FUNCTION increment_likes(post_id UUID)
RETURNS void AS $$
BEGIN
    UPDATE posts SET likes_count = likes_count + 1 WHERE id = post_id;
END;
$$ LANGUAGE plpgsql;

-- ========================================
-- 함수: 좋아요 감소
-- ========================================
CREATE OR REPLACE FUNCTION decrement_likes(post_id UUID)
RETURNS void AS $$
BEGIN
    UPDATE posts SET likes_count = GREATEST(likes_count - 1, 0) WHERE id = post_id;
END;
$$ LANGUAGE plpgsql;

-- ========================================
-- 트리거: 회원가입 시 users 테이블에 자동 추가
-- ========================================
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.users (id, email, username, avatar)
    VALUES (
        NEW.id,
        NEW.email,
        SPLIT_PART(NEW.email, '@', 1),
        UPPER(SUBSTRING(NEW.email FROM 1 FOR 1))
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 트리거 생성
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION handle_new_user();

-- ========================================
-- RLS (Row Level Security) 설정
-- ========================================

-- Users 테이블 RLS
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users are viewable by everyone" ON users;
CREATE POLICY "Users are viewable by everyone" ON users
    FOR SELECT USING (true);

DROP POLICY IF EXISTS "Users can update own profile" ON users;
CREATE POLICY "Users can update own profile" ON users
    FOR UPDATE USING (auth.uid() = id);

DROP POLICY IF EXISTS "Users can insert own profile" ON users;
CREATE POLICY "Users can insert own profile" ON users
    FOR INSERT WITH CHECK (auth.uid() = id);

-- Posts 테이블 RLS
ALTER TABLE posts ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Posts are viewable by everyone" ON posts;
CREATE POLICY "Posts are viewable by everyone" ON posts
    FOR SELECT USING (true);

DROP POLICY IF EXISTS "Users can create posts" ON posts;
CREATE POLICY "Users can create posts" ON posts
    FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own posts" ON posts;
CREATE POLICY "Users can update own posts" ON posts
    FOR UPDATE USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own posts" ON posts;
CREATE POLICY "Users can delete own posts" ON posts
    FOR DELETE USING (auth.uid() = user_id);

-- Likes 테이블 RLS
ALTER TABLE likes ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Likes are viewable by everyone" ON likes;
CREATE POLICY "Likes are viewable by everyone" ON likes
    FOR SELECT USING (true);

DROP POLICY IF EXISTS "Users can like posts" ON likes;
CREATE POLICY "Users can like posts" ON likes
    FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can unlike posts" ON likes;
CREATE POLICY "Users can unlike posts" ON likes
    FOR DELETE USING (auth.uid() = user_id);

-- Comments 테이블 RLS
ALTER TABLE comments ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Comments are viewable by everyone" ON comments;
CREATE POLICY "Comments are viewable by everyone" ON comments
    FOR SELECT USING (true);

DROP POLICY IF EXISTS "Users can create comments" ON comments;
CREATE POLICY "Users can create comments" ON comments
    FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own comments" ON comments;
CREATE POLICY "Users can delete own comments" ON comments
    FOR DELETE USING (auth.uid() = user_id);

-- ========================================
-- Realtime 활성화
-- ========================================
ALTER PUBLICATION supabase_realtime ADD TABLE posts;
ALTER PUBLICATION supabase_realtime ADD TABLE likes;
ALTER PUBLICATION supabase_realtime ADD TABLE comments;

-- ========================================
-- Storage Bucket 생성 (Dashboard에서 수동 설정)
-- ========================================
-- Bucket name: posts
-- Public: true
-- File size limit: 50MB
-- Allowed MIME types: image/*, video/*

-- ========================================
-- 완료!
-- ========================================
-- 이제 MJgram이 실시간으로 작동합니다! 🎉
