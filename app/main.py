from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any
import requests
import os
from openai import OpenAI

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

# OpenAI APIキーを環境変数から取得
def get_openai_api_key():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OpenAI APIキーが設定されていません")
    return api_key

# OpenAI APIでツイート案を生成
def generate_tweet_with_openai(commit_message: str, repository: str) -> str:
    client = OpenAI(api_key=get_openai_api_key())
    prompt = f"""
あなたはX（旧Twitter）で情報発信が得意な個人開発者です。
以下のGitHubコミットメッセージをもとに、インプレッションが伸びるような日本語のツイート文を1つ考えてください。

リポジトリ: {repository}
コミットメッセージ: {commit_message}

#ルール
- 140文字以内
- ハッシュタグを1つ以上含める
- Pieter Levels風の熱量や人間味を意識
"""
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
            temperature=0.8
        )
        tweet = response.choices[0].message.content.strip()
        return tweet
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI APIエラー: {str(e)}")

@app.post("/api/generate_tweet", response_model=GenerateTweetResponse)
def generate_tweet(req: GenerateTweetRequest) -> Any:
    # GitHub APIから最新コミットを取得
    url = GITHUB_API_URL.format(repo=req.repository)
    resp = requests.get(url)
    if resp.status_code != 200:
        error_detail = f"GitHub API エラー: {resp.status_code}"
        try:
            error_data = resp.json()
            if "message" in error_data:
                error_detail += f" - {error_data['message']}"
        except:
            pass
        raise HTTPException(status_code=404, detail=error_detail)
    data = resp.json()
    if not data:
        raise HTTPException(status_code=404, detail="コミット情報が見つかりません")
    commit_message = data[0]["commit"]["message"]
    # OpenAIでツイート案を生成
    tweet_draft = generate_tweet_with_openai(commit_message, req.repository)
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