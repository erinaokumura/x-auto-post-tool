# X（Twitter）API調査・認証設定

## 概要
X（Twitter）API v2を使用してツイート投稿機能を実装します。

## API v2の基本情報
- **エンドポイント**: `https://api.twitter.com/2/tweets`
- **認証**: Bearer Token（OAuth 2.0）
- **メソッド**: POST

## 認証設定手順

### 1. X Developer Portalでの設定
1. [X Developer Portal](https://developer.twitter.com/) にアクセス
2. アプリケーションを作成
3. **OAuth 2.0** を有効化
4. **Client ID** と **Client Secret** を取得

### 2. アクセストークンの取得
- **Bearer Token** を取得（アプリケーション認証用）
- または **User Access Token** を取得（ユーザー認証用）

## API使用例

### ツイート投稿（POST /2/tweets）
```json
{
  "text": "投稿したいツイート内容"
}
```

### レスポンス例
```json
{
  "data": {
    "id": "1234567890",
    "text": "投稿したいツイート内容"
  }
}
```

## 実装時の注意点
- **レート制限**: 300ツイート/15分（User Access Token使用時）
- **文字数制限**: 280文字
- **エラーハンドリング**: 認証エラー、レート制限エラー等の処理が必要

## 必要なパッケージ
```bash
pip install tweepy
```

## 参考リンク
- [X API v2 Documentation](https://developer.twitter.com/en/docs/twitter-api)
- [Tweepy Documentation](https://docs.tweepy.org/)

## 次のステップ
1. X Developer Portalでアプリケーション作成
2. 認証情報の取得
3. Tweepyを使った実装
4. エラーハンドリングの追加 