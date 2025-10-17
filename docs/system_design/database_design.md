# データベース設計書

## 概要

x-auto-post-toolのデータベース設計書です。スモールスタートを考慮し、必要最小限の構造から段階的に拡張できる設計にしています。

## 設計方針

### 1. 段階的アプローチ
- **Phase 1**: 基本的なユーザー管理と投稿履歴
- **Phase 2**: OAuth認証の永続化
- **Phase 3**: 高度な設定と分析機能

### 2. スケーラビリティ
- インデックスの適切な設計
- 正規化と非正規化のバランス
- 将来の機能拡張を考慮した設計

### 3. セキュリティ
- 機密情報の暗号化
- 適切なアクセス制御
- 監査ログの実装

## テーブル設計

### 1. ユーザーテーブル (users)

```sql
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
```

#### カラム説明
- **id**: 主キー（自動採番）
- **email**: ユーザーのメールアドレス（一意制約）
- **username**: ユーザー名（一意制約、オプション）
- **display_name**: 表示名
- **avatar_url**: アバター画像のURL
- **is_active**: アカウントの有効/無効フラグ
- **is_verified**: メール認証済みフラグ
- **created_at**: アカウント作成日時
- **updated_at**: 最終更新日時
- **last_login_at**: 最終ログイン日時
- **login_count**: ログイン回数

#### インデックス
```sql
-- メールアドレスでの高速検索
CREATE INDEX idx_users_email ON users(email);

-- ユーザー名での高速検索
CREATE INDEX idx_users_username ON users(username);

-- アクティブユーザーの検索
CREATE INDEX idx_users_active ON users(is_active) WHERE is_active = TRUE;

-- 作成日時でのソート
CREATE INDEX idx_users_created_at ON users(created_at);
```

#### 制約
```sql
-- メールアドレスの形式チェック
ALTER TABLE users ADD CONSTRAINT chk_email_format 
CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$');

-- ユーザー名の形式チェック（英数字とアンダースコアのみ）
ALTER TABLE users ADD CONSTRAINT chk_username_format 
CHECK (username ~* '^[a-zA-Z0-9_]+$');
```

### 2. OAuthトークンテーブル (oauth_tokens)

```sql
CREATE TABLE oauth_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL, -- 'twitter', 'github' など
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    token_type VARCHAR(50) DEFAULT 'Bearer',
    expires_at TIMESTAMP WITH TIME ZONE,
    scope TEXT, -- 権限スコープ
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);
```

#### カラム説明
- **id**: 主キー（自動採番）
- **user_id**: ユーザーID（外部キー）
- **provider**: OAuthプロバイダー名
- **access_token**: アクセストークン（暗号化推奨）
- **refresh_token**: リフレッシュトークン（暗号化推奨）
- **token_type**: トークンタイプ（通常は'Bearer'）
- **expires_at**: トークンの有効期限
- **scope**: 取得した権限スコープ
- **created_at**: 作成日時
- **updated_at**: 更新日時
- **is_active**: トークンの有効/無効フラグ

#### インデックス
```sql
-- ユーザーとプロバイダーの組み合わせで高速検索
CREATE UNIQUE INDEX idx_oauth_tokens_user_provider 
ON oauth_tokens(user_id, provider) WHERE is_active = TRUE;

-- 有効期限での検索
CREATE INDEX idx_oauth_tokens_expires_at 
ON oauth_tokens(expires_at) WHERE is_active = TRUE;

-- プロバイダーでの検索
CREATE INDEX idx_oauth_tokens_provider 
ON oauth_tokens(provider, is_active);
```

#### 制約
```sql
-- ユーザーとプロバイダーの組み合わせは一意
ALTER TABLE oauth_tokens ADD CONSTRAINT uq_user_provider 
UNIQUE (user_id, provider);

-- プロバイダーの値チェック
ALTER TABLE oauth_tokens ADD CONSTRAINT chk_provider 
CHECK (provider IN ('twitter', 'github', 'linkedin'));
```

### 3. 投稿履歴テーブル (post_history)

```sql
CREATE TABLE post_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    repository VARCHAR(255) NOT NULL, -- GitHubリポジトリ名
    commit_message TEXT NOT NULL, -- コミットメッセージ
    tweet_text TEXT NOT NULL, -- 実際に投稿されたツイート
    tweet_id VARCHAR(255), -- Xの投稿ID
    language VARCHAR(10) DEFAULT 'ja', -- 言語設定
    status VARCHAR(50) NOT NULL DEFAULT 'pending', -- 投稿ステータス
    error_message TEXT, -- エラーメッセージ（失敗時）
    retry_count INTEGER DEFAULT 0, -- リトライ回数
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    posted_at TIMESTAMP WITH TIME ZONE, -- 実際の投稿日時
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

#### カラム説明
- **id**: 主キー（自動採番）
- **user_id**: ユーザーID（外部キー）
- **repository**: GitHubリポジトリ名
- **commit_message**: 元のコミットメッセージ
- **tweet_text**: AI生成されたツイート内容
- **tweet_id**: Xの投稿ID（成功時のみ）
- **language**: 言語設定（ja/en）
- **status**: 投稿ステータス（pending/success/failed/retrying）
- **error_message**: エラーメッセージ
- **retry_count**: リトライ回数
- **created_at**: 作成日時
- **posted_at**: 実際の投稿日時
- **updated_at**: 更新日時

#### インデックス
```sql
-- ユーザーと作成日時での検索
CREATE INDEX idx_post_history_user_created 
ON post_history(user_id, created_at DESC);

-- ステータスでの検索
CREATE INDEX idx_post_history_status 
ON post_history(status, created_at);

-- リポジトリでの検索
CREATE INDEX idx_post_history_repository 
ON post_history(repository, created_at DESC);

-- 投稿日時での検索
CREATE INDEX idx_post_history_posted_at 
ON post_history(posted_at DESC);
```

#### 制約
```sql
-- ステータスの値チェック
ALTER TABLE post_history ADD CONSTRAINT chk_status 
CHECK (status IN ('pending', 'success', 'failed', 'retrying'));

-- 言語の値チェック
ALTER TABLE post_history ADD CONSTRAINT chk_language 
CHECK (language IN ('ja', 'en'));

-- リトライ回数の制限
ALTER TABLE post_history ADD CONSTRAINT chk_retry_count 
CHECK (retry_count >= 0 AND retry_count <= 5);
```

### 4. 設定テーブル (user_settings)

```sql
CREATE TABLE user_settings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    setting_key VARCHAR(100) NOT NULL,
    setting_value TEXT,
    setting_type VARCHAR(50) DEFAULT 'string', -- string, boolean, integer, json
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

#### カラム説明
- **id**: 主キー（自動採番）
- **user_id**: ユーザーID（外部キー）
- **setting_key**: 設定キー
- **setting_value**: 設定値
- **setting_type**: 設定値の型
- **description**: 設定の説明
- **created_at**: 作成日時
- **updated_at**: 更新日時

#### インデックス
```sql
-- ユーザーと設定キーの組み合わせで高速検索
CREATE UNIQUE INDEX idx_user_settings_user_key 
ON user_settings(user_id, setting_key);

-- 設定キーでの検索
CREATE INDEX idx_user_settings_key 
ON user_settings(setting_key);
```

#### 制約
```sql
-- ユーザーと設定キーの組み合わせは一意
ALTER TABLE user_settings ADD CONSTRAINT uq_user_setting_key 
UNIQUE (user_id, setting_key);

-- 設定タイプの値チェック
ALTER TABLE user_settings ADD CONSTRAINT chk_setting_type 
CHECK (setting_type IN ('string', 'boolean', 'integer', 'json'));
```

## 初期データ

### 設定の初期値
```sql
-- デフォルト設定の挿入
INSERT INTO user_settings (user_id, setting_key, setting_value, setting_type, description) VALUES
(1, 'default_language', 'ja', 'string', 'デフォルトの投稿言語'),
(1, 'auto_post_enabled', 'true', 'boolean', '自動投稿の有効/無効'),
(1, 'max_retry_count', '3', 'integer', '最大リトライ回数'),
(1, 'notification_enabled', 'true', 'boolean', '通知の有効/無効');
```

## マイグレーション戦略

### 1. 初期マイグレーション
```sql
-- 001_initial_schema.sql
-- ユーザーテーブル作成
-- OAuthトークンテーブル作成
-- 投稿履歴テーブル作成
-- 設定テーブル作成
```

### 2. 段階的マイグレーション
- 各機能追加時にマイグレーションファイルを作成
- ロールバック可能な設計
- データ整合性の保証

## セキュリティ考慮事項

### 1. データ暗号化
- OAuthトークンの暗号化
- 機密設定値の暗号化

### 2. アクセス制御
- 行レベルセキュリティ（RLS）
- 適切な権限設定

### 3. 監査ログ
- 重要な操作のログ記録
- データ変更の追跡

## パフォーマンス最適化

### 1. インデックス戦略
- 検索頻度の高いカラムにインデックス
- 複合インデックスの活用
- 部分インデックスの使用

### 2. クエリ最適化
- N+1問題の回避
- 適切なJOINの使用
- ページネーションの実装

### 3. データアーカイブ
- 古い投稿履歴のアーカイブ
- パーティショニングの検討

## 今後の拡張予定

### Phase 2
- 投稿分析テーブル
- ユーザー統計テーブル
- 通知履歴テーブル

### Phase 3
- マルチプラットフォーム対応
- 高度な分析機能
- チーム機能 