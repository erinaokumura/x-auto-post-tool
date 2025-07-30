from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.api import twitter as twitter_api
from app.api.twitter import get_post_tweet_with_tweepy

def test_post_tweet(monkeypatch):
    # サービス層をモック
    def mock_post_tweet_with_tweepy(tweet):
        return {"status": "ok"}
    monkeypatch.setenv("TWITTER_CLIENT_ID", "dummy")
    monkeypatch.setenv("TWITTER_CLIENT_SECRET", "dummy")
    monkeypatch.setenv("TWITTER_ACCESS_TOKEN", "dummy")
    monkeypatch.setenv("TWITTER_ACCESS_TOKEN_SECRET", "dummy")

    # テスト用アプリを生成し、依存性をオーバーライド
    app = FastAPI()
    app.include_router(twitter_api.router, prefix="/api")
    app.dependency_overrides[get_post_tweet_with_tweepy] = lambda: mock_post_tweet_with_tweepy
    client = TestClient(app)

    response = client.post("/api/post_tweet", json={"tweet": "テストツイート"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok" 