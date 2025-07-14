from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any
import requests
import os
from openai import OpenAI
from .post import post_tweet as post_tweet_api
import tweepy

app = FastAPI()

oauth2_handler = None

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
def generate_tweet_with_openai(commit_message: str, repository: str, language: str = 'ja') -> str:
    client = OpenAI(api_key=get_openai_api_key())
    if language == 'en':
        prompt = f"""
You are an indie developer who is good at sharing information on X (formerly Twitter).
Based on the following GitHub commit message, generate an engaging English tweet (within 140 characters, include at least one hashtag, in the style of Pieter Levels).

Repository: {repository}
Commit message: {commit_message}
"""
    else:
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
        content = response.choices[0].message.content if response.choices[0].message else None
        if content is None:
            raise HTTPException(status_code=500, detail="OpenAI APIからツイート案の生成に失敗しました")
        tweet = content.strip()
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

# Tweepy認証用関数
def get_tweepy_client():
    consumer_key = os.getenv("TWITTER_CLIENT_ID")
    consumer_secret = os.getenv("TWITTER_CLIENT_SECRET")
    access_token = os.getenv("TWITTER_ACCESS_TOKEN")
    access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
    if not all([consumer_key, consumer_secret, access_token, access_token_secret]):
        raise HTTPException(status_code=500, detail="Twitter API認証情報が不足しています")
    auth = tweepy.OAuth1UserHandler(
        consumer_key, consumer_secret, access_token, access_token_secret
    )
    api = tweepy.API(auth)
    return api

@app.post("/api/post_tweet", response_model=PostTweetResponse)
def post_tweet(req: PostTweetRequest) -> Any:
    # Tweepyでツイート投稿
    try:
        api = get_tweepy_client()
        api.update_status(status=req.tweet)
        return PostTweetResponse(status="ok")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Twitter APIエラー: {str(e)}")

# --- ここからTwitter認証・投稿API ---

class TwitterAuthRequest(BaseModel):
    # 認可フロー開始用
    pass

class TwitterAuthResponse(BaseModel):
    authorization_url: str
    state: str

@app.post("/api/twitter_auth", response_model=TwitterAuthResponse)
def twitter_auth() -> Any:
    global oauth2_handler
    CLIENT_ID = os.getenv("TWITTER_CLIENT_ID")
    CLIENT_SECRET = os.getenv("TWITTER_CLIENT_SECRET")
    REDIRECT_URI = os.getenv("TWITTER_REDIRECT_URI", "http://127.0.0.1:8000/callback")
    SCOPES = ["tweet.write", "tweet.read", "users.read", "offline.access"]
    if not CLIENT_ID or not CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="Twitter Client ID/Secretが設定されていません")
    oauth2_handler = tweepy.OAuth2UserHandler(
        client_id=CLIENT_ID,
        redirect_uri=REDIRECT_URI,
        scope=SCOPES,
        client_secret=CLIENT_SECRET
    )
    url = oauth2_handler.get_authorization_url()
    return TwitterAuthResponse(authorization_url=url, state=oauth2_handler.state())

class TwitterTokenRequest(BaseModel):
    redirect_response: str
    tweet_text: str

class TwitterTokenResponse(BaseModel):
    status: str
    tweet_response: Any

@app.post("/api/post_tweet_with_auth", response_model=TwitterTokenResponse)
def post_tweet_with_auth(req: TwitterTokenRequest) -> Any:
    CLIENT_ID = os.getenv("TWITTER_CLIENT_ID")
    CLIENT_SECRET = os.getenv("TWITTER_CLIENT_SECRET")
    REDIRECT_URI = os.getenv("TWITTER_REDIRECT_URI", "http://127.0.0.1:8000/callback")
    SCOPES = ["tweet.write", "tweet.read", "users.read", "offline.access"]
    if not CLIENT_ID or not CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="Twitter Client ID/Secretが環境変数に設定されていません")
    auth = tweepy.OAuth2UserHandler(
        client_id=CLIENT_ID,
        redirect_uri=REDIRECT_URI,
        scope=SCOPES,
        client_secret=CLIENT_SECRET
    )
    token = auth.fetch_token(authorization_response=req.redirect_response)
    # post.pyのpost_tweetを呼び出して投稿
    response = post_tweet_api(token["access_token"], req.tweet_text)
    return TwitterTokenResponse(status="ok", tweet_response=response.json())

class AutoPostTweetRequest(BaseModel):
    repository: str
    redirect_response: str
    language: str = 'ja'

class AutoPostTweetResponse(BaseModel):
    status: str
    tweet_text: str
    tweet_response: Any

@app.post("/api/auto_post_tweet", response_model=AutoPostTweetResponse)
def auto_post_tweet(req: AutoPostTweetRequest) -> Any:
    global oauth2_handler
    # 1. GitHub APIから最新コミットを取得
    GITHUB_API_URL = "https://api.github.com/repos/{repo}/commits"
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
    # 2. OpenAIでツイート案を生成（言語指定対応）
    tweet_text = generate_tweet_with_openai(commit_message, req.repository, req.language)
    # 3. X認証→投稿
    if oauth2_handler is None:
        raise HTTPException(status_code=500, detail="認証フローが初期化されていません")
    token = oauth2_handler.fetch_token(authorization_response=req.redirect_response)
    response = post_tweet_api(token["access_token"], tweet_text)
    return AutoPostTweetResponse(status="ok", tweet_text=tweet_text, tweet_response=response.json()) 