# X Auto Post Tool Frontend

Next.js + TypeScript + Tailwind CSSで構築されたフロントエンドアプリケーション。

## セットアップ

### 1. 依存関係のインストール

```bash
cd frontend
npm install
```

### 2. 環境変数の設定（手動設定）

開発環境では環境変数を手動で設定してから起動します。

#### 開発環境での起動手順

PowerShellで以下のコマンドを実行：

```powershell
# 開発環境の環境変数を設定
$env:NODE_ENV="development"
$env:BACKEND_URL="https://x-auto-post-tool-development.up.railway.app"

# 開発サーバーを起動
npm run dev
```

#### 本番環境での起動手順

```powershell
# 本番環境の環境変数を設定
$env:NODE_ENV="production"
$env:BACKEND_URL="https://your-production-backend-url.com"

# ビルドと起動
npm run build
npm run start
```

#### 注意事項

- PowerShellのセッションを閉じると環境変数がリセットされます
- 新しいターミナルを開く際は再度環境変数を設定してください
- フロントエンドから直接バックエンドAPIを呼び出すため、CORS設定が必要です

#### デフォルト値

環境変数が設定されていない場合、デフォルトでローカルの `http://localhost:8000` を使用します。

### 3. 開発サーバーの起動

環境変数を設定後に起動：

```bash
npm run dev
```

http://localhost:3000 でアプリケーションが起動します。

### 4. 本番ビルド

```bash
npm run build
npm run start
```

## ページ構成

- `/` - ホームページ
- `/login` - X (Twitter) OAuth認証ページ
- `/callback` - OAuth認証コールバックページ
- `/dashboard` - メインダッシュボード（ツイート生成・投稿）

## API連携

Next.jsのrewrite機能により、`/api/*`のリクエストはFastAPIサーバーにプロキシされます。バックエンドURLは環境変数`BACKEND_URL`で設定できます（デフォルト: `http://localhost:8000`）。

## 使用技術

- **Next.js 14** - Reactフレームワーク（App Router）
- **TypeScript** - 型安全な開発
- **Tailwind CSS** - ユーティリティファーストCSS
- **Axios** - HTTP クライアント

## 環境要件

- Node.js 18以上
- FastAPIサーバーが実行中（URLは環境変数`BACKEND_URL`で指定）

## 環境変数

| 変数名 | 説明 | デフォルト値 | 例 |
|--------|------|-------------|-----|
| `BACKEND_URL` | バックエンドサーバーのURL | `http://localhost:8000` | `https://x-auto-post-tool-development.up.railway.app` |
| `NODE_ENV` | 実行環境 | `development` | `development`, `production` |

## 利用可能なスクリプト

| スクリプト | 説明 | 環境変数 |
|------------|------|----------|
| `npm run dev` | 開発サーバー | 手動設定が必要 |
| `npm run build` | 本番ビルド | 手動設定が必要 |
| `npm run start` | 本番サーバー起動 | 手動設定が必要 |
| `npm run lint` | ESLintチェック | 不要 |

### クイックスタート（開発環境）

```powershell
# PowerShellで実行
$env:NODE_ENV="development"
$env:BACKEND_URL="https://x-auto-post-tool-development.up.railway.app"
npm run dev
``` 