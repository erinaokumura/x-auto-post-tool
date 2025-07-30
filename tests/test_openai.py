from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.api import openai as openai_api
from app.api.openai import get_fetch_latest_commit_message, get_generate_tweet_with_openai

def test_generate_tweet(monkeypatch):
    # サービス層をモック
    def mock_fetch_latest_commit_message(repo):
        return "fix: バグ修正"
    def mock_generate_tweet_with_openai(commit_message, repository, language='ja'):
        return f"リポジトリ{repository}のコミット: {commit_message}"
    monkeypatch.setenv("OPENAI_API_KEY", "dummy-key")

    # テスト用アプリを生成し、依存性をオーバーライド
    app = FastAPI()
    app.include_router(openai_api.router, prefix="/api")
    app.dependency_overrides[get_fetch_latest_commit_message] = lambda: mock_fetch_latest_commit_message
    app.dependency_overrides[get_generate_tweet_with_openai] = lambda: mock_generate_tweet_with_openai
    client = TestClient(app)

    response = client.post("/api/generate_tweet", json={"repository": "user/repo"})
    assert response.status_code == 200
    data = response.json()
    assert data["commit_message"] == "fix: バグ修正"
    assert data["tweet_draft"].startswith("リポジトリuser/repo") 