# デプロイガイド

## Railway + Vercel 構成でのデプロイ手順

### 1. Railway バックエンドデプロイ

#### 前提条件
- GitHubリポジトリにコードがpush済み
- Railway PostgreSQL + Redisサービスが作成済み

#### デプロイ手順

1. **Railway Dashboard**にアクセス
   - https://railway.app/dashboard

2. **新しいプロジェクト作成**
   - "New Project" → "Deploy from GitHub repo"
   - このリポジトリを選択

3. **環境変数設定**
   
   **必須環境変数:**
   ```
   ENVIRONMENT=production
   OPENAI_API_KEY=sk-proj-your-key
   TWITTER_CLIENT_ID=your-client-id
   TWITTER_CLIENT_SECRET=your-client-secret
   TWITTER_REDIRECT_URI=https://your-railway-domain.railway.app/callback
   ENCRYPTION_KEY=your-32-character-encryption-key
   CORS_ORIGINS=https://your-vercel-domain.vercel.app
   ```

   **自動設定される環境変数:**
   ```
   DATABASE_URL=postgresql://... (PostgreSQLサービスから)
   REDIS_URL=redis://... (Redisサービスから)
   PORT=8000 (Railwayが自動設定)
   ```

4. **デプロイ確認**
   - デプロイ完了後、`https://your-domain.railway.app/health` でヘルスチェック
   - `https://your-domain.railway.app/docs` でAPI仕様書確認

### 2. Vercel フロントエンドデプロイ

#### 前提条件
- Next.jsプロジェクトが `frontend/` ディレクトリに存在
- Railway バックエンドが稼働中

#### デプロイ手順

1. **Vercel Dashboard**にアクセス
   - https://vercel.com/dashboard

2. **新しいプロジェクト作成**
   - "New Project" → GitHubリポジトリを選択
   - Root Directory: `frontend`
   - Framework Preset: Next.js

3. **環境変数設定**
   ```
   NEXT_PUBLIC_API_URL=https://your-railway-domain.railway.app
   ```

4. **デプロイ設定**
   - Build Command: `npm run build`
   - Output Directory: `.next`
   - Install Command: `npm install`

5. **カスタムドメイン設定**（オプション）
   - Vercel Dashboardから独自ドメインを設定可能

### 3. 環境変数の相互参照設定

デプロイ後、以下の設定を更新：

1. **Railway環境変数を更新**
   ```
   CORS_ORIGINS=https://your-vercel-domain.vercel.app
   TWITTER_REDIRECT_URI=https://your-railway-domain.railway.app/callback
   ```

2. **Twitter Developer Console**
   - Callback URL: `https://your-railway-domain.railway.app/callback`
   - Website URL: `https://your-vercel-domain.vercel.app`

### 4. デプロイ後の確認事項

#### バックエンド確認
- [ ] `/health` エンドポイントが200を返す
- [ ] `/docs` でSwagger UIが表示される
- [ ] PostgreSQL接続が正常
- [ ] Redis接続が正常

#### フロントエンド確認
- [ ] サイトが正常に表示される
- [ ] バックエンドAPIとの通信が正常
- [ ] Twitter認証フローが動作する

#### 統合テスト
- [ ] ログイン → ダッシュボード → 投稿の一連の流れ
- [ ] エラーが発生しないことを確認

### 5. トラブルシューティング

#### よくある問題

**Railway デプロイエラー**
```bash
# ログ確認
railway logs

# 環境変数確認
railway variables

# 再デプロイ
railway up --detach
```

**CORS エラー**
- `CORS_ORIGINS` 環境変数にVercelドメインが含まれているか確認
- プロトコル（https://）が正しく設定されているか確認

**データベース接続エラー**
- `DATABASE_URL` が正しく設定されているか確認
- PostgreSQLサービスが稼働しているか確認

**Redis接続エラー**
- `REDIS_URL` が正しく設定されているか確認
- Redisサービスが稼働しているか確認

### 6. 監視とメンテナンス

#### Railway 監視
- メトリクス: CPU、メモリ、ネットワーク使用量
- ログ: アプリケーションログとエラーログ
- アラート: サービス停止時の通知設定

#### Vercel 監視
- Analytics: ページビュー、パフォーマンス
- Function Logs: サーバーサイド処理のログ
- Deployment Status: デプロイ状況の確認

### 7. 自動デプロイ設定

#### GitHub Actions（オプション）
```yaml
# .github/workflows/deploy.yml
name: Deploy
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to Railway
        uses: railway/cli@v2
        with:
          token: ${{ secrets.RAILWAY_TOKEN }}
```

#### 自動デプロイの利点
- コード変更時の自動デプロイ
- テスト実行後のデプロイ
- ロールバック機能

これで Railway + Vercel 構成での完全なデプロイが完了します。

