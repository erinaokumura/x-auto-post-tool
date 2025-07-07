from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any
import requests

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI!"}

class GenerateTweetRequest(BaseModel):
    repository: str

class GenerateTweetResponse(BaseModel):
    commit_message: str
    tweet_draft: str

GITHUB_API_URL = "https://api.github.com/repos/{repo}/commits"

@app.post("/api/generate_tweet", response_model=GenerateTweetResponse)
def generate_tweet(req: GenerateTweetRequest) -> Any:
    # GitHub APIから最新コミットを取得
    url = GITHUB_API_URL.format(repo=req.repository)
    resp = requests.get(url)
    if resp.status_code != 200:
        raise HTTPException(status_code=404, detail="GitHubリポジトリが見つかりません")
    data = resp.json()
    if not data:
        raise HTTPException(status_code=404, detail="コミット情報が見つかりません")
    commit_message = data[0]["commit"]["message"]
    # ツイート案を生成（現状はシンプルなテンプレート）
    tweet_draft = f"{req.repository} の最新コミット: {commit_message} #個人開発"
    return GenerateTweetResponse(
        commit_message=commit_message,
        tweet_draft=tweet_draft
    )

class PostTweetRequest(BaseModel):
    tweet: str

class PostTweetResponse(BaseModel):
    status: str

@app.post("/api/post_tweet", response_model=PostTweetResponse)
def post_tweet(req: PostTweetRequest) -> Any:
    # TODO: X（Twitter）APIでツイート投稿
    # ここではダミーで成功を返す
    return PostTweetResponse(status="ok") 