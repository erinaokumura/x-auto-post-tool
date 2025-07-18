-- 初期スキーママイグレーション
-- 作成日: 2024年
-- 説明: x-auto-post-toolの初期データベーススキーマ

-- ユーザーテーブル作成
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE,
    display_name VARCHAR(100),
    avatar_url TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP WITH TIME ZONE,
    login_count INTEGER DEFAULT 0
);

-- ユーザーテーブルのインデックス作成
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_active ON users(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_users_created_at ON users(created_at);

-- ユーザーテーブルの制約作成
ALTER TABLE users ADD CONSTRAINT chk_email_format 
CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$');

ALTER TABLE users ADD CONSTRAINT chk_username_format 
CHECK (username IS NULL OR username ~* '^[a-zA-Z0-9_]+$');

-- OAuthトークンテーブル作成
CREATE TABLE oauth_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL,
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    token_type VARCHAR(50) DEFAULT 'Bearer',
    expires_at TIMESTAMP WITH TIME ZONE,
    scope TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- OAuthトークンテーブルのインデックス作成
CREATE UNIQUE INDEX idx_oauth_tokens_user_provider 
ON oauth_tokens(user_id, provider) WHERE is_active = TRUE;

CREATE INDEX idx_oauth_tokens_expires_at 
ON oauth_tokens(expires_at) WHERE is_active = TRUE;

CREATE INDEX idx_oauth_tokens_provider 
ON oauth_tokens(provider, is_active);

-- OAuthトークンテーブルの制約作成
ALTER TABLE oauth_tokens ADD CONSTRAINT uq_user_provider 
UNIQUE (user_id, provider);

ALTER TABLE oauth_tokens ADD CONSTRAINT chk_provider 
CHECK (provider IN ('twitter', 'github', 'linkedin'));

-- 投稿履歴テーブル作成
CREATE TABLE post_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    repository VARCHAR(255) NOT NULL,
    commit_message TEXT NOT NULL,
    tweet_text TEXT NOT NULL,
    tweet_id VARCHAR(255),
    language VARCHAR(10) DEFAULT 'ja',
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    posted_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 投稿履歴テーブルのインデックス作成
CREATE INDEX idx_post_history_user_created 
ON post_history(user_id, created_at DESC);

CREATE INDEX idx_post_history_status 
ON post_history(status, created_at);

CREATE INDEX idx_post_history_repository 
ON post_history(repository, created_at DESC);

CREATE INDEX idx_post_history_posted_at 
ON post_history(posted_at DESC);

-- 投稿履歴テーブルの制約作成
ALTER TABLE post_history ADD CONSTRAINT chk_status 
CHECK (status IN ('pending', 'success', 'failed', 'retrying'));

ALTER TABLE post_history ADD CONSTRAINT chk_language 
CHECK (language IN ('ja', 'en'));

ALTER TABLE post_history ADD CONSTRAINT chk_retry_count 
CHECK (retry_count >= 0 AND retry_count <= 5);

-- 設定テーブル作成
CREATE TABLE user_settings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    setting_key VARCHAR(100) NOT NULL,
    setting_value TEXT,
    setting_type VARCHAR(50) DEFAULT 'string',
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 設定テーブルのインデックス作成
CREATE UNIQUE INDEX idx_user_settings_user_key 
ON user_settings(user_id, setting_key);

CREATE INDEX idx_user_settings_key 
ON user_settings(setting_key);

-- 設定テーブルの制約作成
ALTER TABLE user_settings ADD CONSTRAINT uq_user_setting_key 
UNIQUE (user_id, setting_key);

ALTER TABLE user_settings ADD CONSTRAINT chk_setting_type 
CHECK (setting_type IN ('string', 'boolean', 'integer', 'json'));

-- 更新日時を自動更新するためのトリガー関数作成
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 各テーブルに更新日時トリガーを設定
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_oauth_tokens_updated_at BEFORE UPDATE ON oauth_tokens
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_post_history_updated_at BEFORE UPDATE ON post_history
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_settings_updated_at BEFORE UPDATE ON user_settings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- コメント追加
COMMENT ON TABLE users IS 'ユーザー情報テーブル';
COMMENT ON TABLE oauth_tokens IS 'OAuth認証トークンテーブル';
COMMENT ON TABLE post_history IS '投稿履歴テーブル';
COMMENT ON TABLE user_settings IS 'ユーザー設定テーブル';

COMMENT ON COLUMN users.email IS 'ユーザーのメールアドレス';
COMMENT ON COLUMN users.username IS 'ユーザー名（一意）';
COMMENT ON COLUMN users.display_name IS '表示名';
COMMENT ON COLUMN users.is_active IS 'アカウントの有効/無効フラグ';
COMMENT ON COLUMN users.is_verified IS 'メール認証済みフラグ';

COMMENT ON COLUMN oauth_tokens.provider IS 'OAuthプロバイダー（twitter, github, linkedin）';
COMMENT ON COLUMN oauth_tokens.access_token IS 'アクセストークン（暗号化推奨）';
COMMENT ON COLUMN oauth_tokens.refresh_token IS 'リフレッシュトークン（暗号化推奨）';
COMMENT ON COLUMN oauth_tokens.expires_at IS 'トークンの有効期限';

COMMENT ON COLUMN post_history.repository IS 'GitHubリポジトリ名';
COMMENT ON COLUMN post_history.commit_message IS '元のコミットメッセージ';
COMMENT ON COLUMN post_history.tweet_text IS 'AI生成されたツイート内容';
COMMENT ON COLUMN post_history.tweet_id IS 'Xの投稿ID（成功時のみ）';
COMMENT ON COLUMN post_history.language IS '言語設定（ja/en）';
COMMENT ON COLUMN post_history.status IS '投稿ステータス（pending/success/failed/retrying）';
COMMENT ON COLUMN post_history.retry_count IS 'リトライ回数';

COMMENT ON COLUMN user_settings.setting_key IS '設定キー';
COMMENT ON COLUMN user_settings.setting_value IS '設定値';
COMMENT ON COLUMN user_settings.setting_type IS '設定値の型（string/boolean/integer/json）';
COMMENT ON COLUMN user_settings.description IS '設定の説明'; 