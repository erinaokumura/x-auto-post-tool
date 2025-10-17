# API フロー概要

## クイックリファレンス

### 1. 認証フロー（初回）
```
ユーザー → ログイン → Twitter認証 → コールバック → セッション作成 → ダッシュボード
```

### 2. ツイート投稿フロー（認証後）
```
リポジトリ入力 → GitHub API → OpenAI → ツイート生成 → 編集 → Twitter投稿
```

## 主要エンドポイント

| エンドポイント | メソッド | 説明 | 認証 |
|---|---|---|---|
| `/api/auth/twitter/login` | GET | Twitter認証開始 | 不要 |
| `/api/auth/twitter/callback` | POST | OAuth コールバック処理 | 不要 |
| `/api/generate_tweet` | POST | ツイート文生成 | 必要 |
| `/api/post_tweet` | POST | ツイート投稿 | 必要 |
| `/api/auth/me` | GET | 現在のユーザー情報 | 必要 |

## データフロー

### 認証データ
```
Twitter OAuth → 暗号化 → PostgreSQL
セッションID → Redis (TTL: 30分)
```

### ツイートデータ
```
GitHub Repo → コミット情報 → OpenAI → ツイート文 → Twitter API
```

## セキュリティ

### レート制限
- OAuth: 30回/分
- ツイート生成: 10回/分
- ツイート投稿: 10回/分

### 認証チェック
1. セッションクッキー確認
2. Redis でセッション検証
3. DB でユーザー存在確認
4. 復号化されたOAuthトークン使用

## 障害対応

### サーキットブレーカー
- GitHub API: 3回失敗で遮断
- OpenAI API: 5回失敗で遮断
- Twitter API: 3回失敗で遮断

### エラーレスポンス
```json
{
  "detail": "エラーメッセージ",
  "error_code": "TWITTER_API_ERROR",
  "context": {
    "user_id": 123,
    "repository": "owner/repo"
  }
}
```
