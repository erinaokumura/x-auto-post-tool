# 環境設定ガイド

このプロジェクトでは開発環境と本番環境で異なる設定ファイルを使用します。

## 環境設定ファイルの構成

### 開発環境
- ファイル: `.env.development`
- 用途: ローカル開発時
- Railway環境: Development環境のRedis/PostgreSQLを使用

### 本番環境
- ファイル: `.env.production` 
- 用途: Railway本番デプロイ時
- Railway環境: Production環境のRedis/PostgreSQLを使用

## セットアップ手順

### 1. 開発環境設定

```bash
# テンプレートをコピー
cp env.development.template .env.development

# .env.development を編集して実際の値を設定
```

### 2. 本番環境設定

```bash
# テンプレートをコピー
cp env.production.template .env.production

# .env.production を編集して実際の値を設定
```

## 環境の切り替え

環境変数 `ENVIRONMENT` で使用する設定ファイルが決まります：

- `ENVIRONMENT=development` → `.env.development` を使用
- `ENVIRONMENT=production` → `.env.production` を使用

## Railway環境設定

### Development環境
1. Railway Dashboard → Development環境
2. Redis: 新しいサービスとして追加
3. 環境変数 `REDIS_URL` をコピーして `.env.development` に設定

### Production環境  
1. Railway Dashboard → Production環境
2. Redis: 新しいサービスとして追加
3. 環境変数 `REDIS_URL` をコピーして `.env.production` に設定
4. または Railway の Environment Variables に直接設定

## 重要な設定項目

### 必須設定
- `OPENAI_API_KEY`: OpenAI APIキー
- `TWITTER_CLIENT_ID`: Twitter/X Client ID
- `TWITTER_CLIENT_SECRET`: Twitter/X Client Secret
- `DATABASE_URL`: PostgreSQL接続URL
- `REDIS_URL`: Redis接続URL
- `ENCRYPTION_KEY`: 32文字以上の暗号化キー

### 環境固有設定
- `TWITTER_REDIRECT_URI`: 
  - 開発: `http://127.0.0.1:8000/callback`
  - 本番: `https://your-domain.railway.app/callback`
- `CORS_ORIGINS`:
  - 開発: `http://localhost:3000,http://127.0.0.1:3000`
  - 本番: `https://your-frontend.vercel.app`
- `OAUTHLIB_INSECURE_TRANSPORT`:
  - 開発: `1` (HTTP許可)
  - 本番: `0` (HTTPS必須)

## セキュリティ注意事項

1. `.env.*` ファイルは絶対にGitにコミットしない
2. 本番環境では可能な限りRailwayの環境変数機能を使用
3. 暗号化キーは環境ごとに異なる値を使用
4. APIキーは定期的にローテーション

## トラブルシューティング

### 環境設定ファイルが読み込まれない
- `ENVIRONMENT` 環境変数が正しく設定されているか確認
- ファイル名が正確か確認（`.env.development`, `.env.production`）
- ファイルのエンコーディングがUTF-8か確認

### Redis接続エラー
- `REDIS_URL` が正しく設定されているか確認
- Railway Redis サービスが起動しているか確認
- 接続文字列の形式が正しいか確認: `redis://user:password@host:port`
