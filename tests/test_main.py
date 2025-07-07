from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_generate_tweet():
    response = client.post("/api/generate_tweet", json={"repository": "user/repo"})
    assert response.status_code == 200
    data = response.json()
    assert "commit_message" in data
    assert "tweet_draft" in data
    assert data["commit_message"] == "fix: バグ修正"
    assert data["tweet_draft"].startswith("リポジトリuser/repo")

def test_post_tweet():
    response = client.post("/api/post_tweet", json={"tweet": "テストツイート"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok" 