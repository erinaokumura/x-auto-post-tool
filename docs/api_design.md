# API設計（2024/06時点 最新版）

## 概要
- GitHubリポジトリ名を指定し、最新コミットからAIでツイート案を生成
- X（Twitter）APIのOAuth2.0認証を経て、ワンクリックで自動投稿まで実行可能

---

## 1. ツイート案生成API
- **エンドポイント**: `/api/generate_tweet`
- **メソッド**: POST
- **リクエスト例**:
```json
{
  "repository": "user/repo"
}
```
- **レスポンス例**:
```json
{
  "commit_message": "fix: バグ修正",
  "tweet_draft": "user/repo の最新コミット: fix: バグ修正 #個人開発"
}
```

---

## 2. X認証用URL発行API
- **エンドポイント**: `/api/twitter_auth`
- **メソッド**: POST
- **リクエスト例**: 空でOK
- **レスポンス例**:
```json
{
  "authorization_url": "https://twitter.com/i/oauth2/authorize?...",
  "state": "..."
}
```
- **使い方**: 返ってきた `authorization_url` にブラウザでアクセスし、X認証を許可。リダイレクト先URLをコピー。

---

## 3. 完全自動化API（ツイート案生成→X投稿まで一括）
- **エンドポイント**: `/api/auto_post_tweet`
- **メソッド**: POST
- **リクエスト例**:
```json
{
  "repository": "user/repo",
  "redirect_response": "http://127.0.0.1:8000/callback?state=...&code=..."
}
```
- **レスポンス例**:
```json
{
  "status": "ok",
  "tweet_text": "user/repo の最新コミット: fix: バグ修正 #個人開発",
  "tweet_response": { "data": { "id": "...", "text": "..." } }
}
```
- **使い方**:
  1. `/api/twitter_auth` で認可URLを取得し、X認証を完了
  2. リダイレクト先URLを `redirect_response` に指定して本APIを呼び出す
  3. 最新コミット取得→AIツイート生成→X投稿まで一括で実行

---

## 備考
- 認証フローの状態はグローバル変数で一時管理（単一ユーザー・単一セッション用）
- 本番運用時はセッション管理やDB保存が必要
- すべてのAPIは `/docs`（Swagger UI）からも試せます 