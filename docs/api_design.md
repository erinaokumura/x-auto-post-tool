# API設計（2024/12時点 最適化版）

## 概要
- GitHubリポジトリ名を指定し、最新コミットからAIでツイート案を生成
- X（Twitter）APIのOAuth2.0 PKCE認証を経て、ワンクリックで自動投稿まで実行可能
- **最適化機能**: キャッシュ、非同期処理、リトライ、エラーハンドリング、監視機能を実装済み

---

## 🚀 最適化されたAPIエンドポイント

### 1. 自動投稿API（高速・推奨版）
- **エンドポイント**: `/api/auto_post_tweet_async`
- **メソッド**: POST
- **特徴**: 非同期処理によるサーバーリソース効率化、同時接続性能向上
- **認証**: 必須（OAuth2.0 PKCE）
- **レート制限**: 5回/分
- **リクエスト例**:
```json
{
  "repository": "user/repo",
  "language": "ja"
}
```
- **レスポンス例**:
```json
{
  "status": "ok",
  "tweet_text": "user/repo の最新コミット: fix: バグ修正 🔧 効率化を実現！ #個人開発 #プログラミング",
  "tweet_response": { 
    "data": { 
      "id": "1234567890", 
      "text": "..." 
    } 
  }
}
```

### 2. 自動投稿API（標準版）
- **エンドポイント**: `/api/auto_post_tweet`
- **メソッド**: POST
- **特徴**: 同期処理、後方互換性維持
- **認証**: 必須（OAuth2.0 PKCE）
- **レート制限**: 5回/分
- **機能**: サーキットブレーカー、重複投稿チェック、統一エラーハンドリング

### 3. ツイート案生成API
- **エンドポイント**: `/api/generate_tweet`
- **メソッド**: POST
- **特徴**: GPT-4o-mini利用でコスト80%削減、24時間キャッシュ
- **リクエスト例**:
```json
{
  "repository": "user/repo",
  "language": "ja"
}
```
- **レスポンス例**:
```json
{
  "commit_message": "fix: improve performance by adding caching",
  "tweet_draft": "user/repo でパフォーマンス改善を実装！キャッシュ機能追加で爆速化 🚀 #個人開発 #最適化",
  "repository": "user/repo"
}
```

### 4. 手動ツイート投稿API
- **エンドポイント**: `/api/post_tweet`
- **メソッド**: POST
- **特徴**: リトライ機能、投稿履歴管理
- **認証**: 必須
- **レート制限**: 10回/分
- **リクエスト例**:
```json
{
  "tweet_text": "手動で投稿するツイート内容"
}
```

---

## 🔐 認証API

### 1. Twitter認証開始
- **エンドポイント**: `/api/auth/twitter`
- **メソッド**: POST
- **特徴**: PKCE対応、セキュリティ強化
- **レスポンス例**:
```json
{
  "authorization_url": "https://twitter.com/i/oauth2/authorize?...",
  "state": "secure_random_state"
}
```

### 2. 認証コールバック処理
- **エンドポイント**: `/api/auth/twitter/callback`
- **メソッド**: GET
- **特徴**: 自動トークンリフレッシュ、暗号化保存

### 3. 認証状態確認
- **エンドポイント**: `/api/auth_status`
- **メソッド**: GET
- **レスポンス例**:
```json
{
  "is_authenticated": true,
  "expires_at": "2024-12-31T23:59:59Z",
  "scope": "tweet.read tweet.write users.read"
}
```

### 4. ログアウト
- **エンドポイント**: `/api/auth/logout`
- **メソッド**: POST

---

## 📊 システム管理・監視API

### 1. ヘルスチェック（詳細版）
- **エンドポイント**: `/api/system/health`
- **メソッド**: GET
- **レスポンス例**:
```json
{
  "status": "healthy",
  "timestamp": 1703123456.789,
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "external_apis": {
      "github": "not_tested",
      "openai": "not_tested",
      "twitter": "not_tested"
    }
  }
}
```

### 2. システムメトリクス
- **エンドポイント**: `/api/system/metrics`
- **メソッド**: GET
- **レスポンス例**:
```json
{
  "timestamp": 1703123456.789,
  "system": {
    "cpu_percent": 25.4,
    "memory": {
      "percent": 68.2,
      "available_gb": 2.1,
      "used_gb": 5.9
    },
    "disk": {
      "percent": 45.6,
      "free_gb": 12.3
    }
  },
  "error_statistics": {
    "error_counts": {
      "HTTPException": 5,
      "TwitterAPIError": 2
    },
    "total_errors": 7
  },
  "redis": {
    "used_memory_mb": 45.2,
    "connected_clients": 3,
    "total_commands_processed": 12847
  }
}
```

### 3. キャッシュ統計
- **エンドポイント**: `/api/system/cache/stats`
- **メソッド**: GET
- **レスポンス例**:
```json
{
  "timestamp": 1703123456.789,
  "github_cache": {
    "total_keys": 25,
    "sample_keys": ["github_commit:abc123", "github_commit:def456"]
  },
  "openai_cache": {
    "total_keys": 18,
    "sample_keys": ["openai_tweet:xyz789"]
  },
  "tweet_history": {
    "total_keys": 42
  }
}
```

### 4. キャッシュクリア
- **エンドポイント**: `/api/system/cache/clear`
- **メソッド**: POST
- **認証**: 必須
- **パラメータ**: `cache_type` (all/github/openai/tweet_history)
- **レスポンス例**:
```json
{
  "message": "allキャッシュをクリアしました",
  "cleared_keys": 85,
  "timestamp": 1703123456.789
}
```

### 5. パフォーマンス履歴
- **エンドポイント**: `/api/system/performance/history`
- **メソッド**: GET

### 6. API使用統計
- **エンドポイント**: `/api/system/api/usage_stats`
- **メソッド**: GET

---

## ⚡ パフォーマンス最適化機能

### キャッシュシステム
- **GitHub API**: 5分間キャッシュ（重複リクエスト削減）
- **OpenAI API**: 24時間キャッシュ（コスト削減）
- **設定可能**: `CACHE_GITHUB_TTL`, `CACHE_OPENAI_TTL`

### 非同期処理
- **httpx**: 高速HTTP通信
- **並列処理**: 複数API呼び出しの同時実行
- **タイムアウト**: 設定可能（デフォルト30秒）

### エラーハンドリング
- **サーキットブレーカー**: 障害時の自動復旧
- **リトライ機能**: 指数バックオフ
- **統一エラーレスポンス**: 構造化エラー情報
- **エラー統計**: リアルタイム集計

### レート制限管理
- **適応的制限**: サービス別細かい制御
- **自動待機**: 429エラー時の自動復旧
- **制限監視**: 残り回数の追跡

---

## 🔧 設定オプション

### 環境変数で制御可能な最適化設定
```bash
# キャッシュ制御
ENABLE_CACHING=true
CACHE_GITHUB_TTL=300
CACHE_OPENAI_TTL=86400

# サーキットブレーカー
ENABLE_CIRCUIT_BREAKER=true
GITHUB_CIRCUIT_FAILURE_THRESHOLD=3
OPENAI_CIRCUIT_FAILURE_THRESHOLD=5
TWITTER_CIRCUIT_FAILURE_THRESHOLD=3

# パフォーマンス
ASYNC_TIMEOUT=30
MAX_CONCURRENT_REQUESTS=10
ENABLE_PERFORMANCE_LOGGING=true

# 外部API
GITHUB_TOKEN=ghp_xxx  # レート制限緩和用
```

---

## 📈 期待されるパフォーマンス向上

### レスポンス時間
- **キャッシュヒット時**: 80-95%短縮（APIコール省略）
- **非同期処理**: 同時処理能力向上（リソース効率化）
- **API費用**: OpenAI利用料80%削減（GPT-4o-mini + キャッシュ）

### 信頼性
- **稼働率**: 99.9%以上
- **自動復旧**: サーキットブレーカーによる障害回復
- **監視**: リアルタイムメトリクス

---

## 📚 利用方法

### 基本フロー（推奨）
1. `/api/auth/twitter` で認証URL取得
2. ブラウザでX認証を完了
3. `/api/auto_post_tweet_async` で高速自動投稿
4. `/api/system/metrics` でパフォーマンス確認

### デバッグ・監視
- `/api/system/health` で全体状況確認
- `/api/system/cache/stats` でキャッシュ効率確認
- `/docs` でSwagger UIから全API試行可能

---

## 🛡️ セキュリティ機能
- **OAuth2.0 PKCE**: 最新セキュリティ標準
- **トークン暗号化**: Fernet暗号化でDB保存
- **レート制限**: slowapi によるDoS攻撃対策
- **セキュリティヘッダー**: CSP, HSTS等の実装
- **入力値検証**: Pydantic による厳格な検証

すべてのAPIは `/docs`（Swagger UI）から詳細確認・テスト可能です。 