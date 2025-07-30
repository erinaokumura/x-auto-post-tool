# X Auto Post Tool Frontend

Next.js + TypeScript + Tailwind CSSで構築されたフロントエンドアプリケーション。

## セットアップ

### 1. 依存関係のインストール

```bash
cd frontend
npm install
```

### 2. 開発サーバーの起動

```bash
npm run dev
```

http://localhost:3000 でアプリケーションが起動します。

### 3. 本番ビルド

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

Next.jsのrewrite機能により、`/api/*`のリクエストはFastAPIサーバー(`http://localhost:8000`)にプロキシされます。

## 使用技術

- **Next.js 14** - Reactフレームワーク（App Router）
- **TypeScript** - 型安全な開発
- **Tailwind CSS** - ユーティリティファーストCSS
- **Axios** - HTTP クライアント

## 環境要件

- Node.js 18以上
- FastAPIサーバーが`http://localhost:8000`で実行中 