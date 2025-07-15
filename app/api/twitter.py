from fastapi import APIRouter, HTTPException, Depends
from app.schemas.twitter import (
    PostTweetRequest, PostTweetResponse,
    TwitterAuthRequest, TwitterAuthResponse,
    TwitterTokenRequest, TwitterTokenResponse,
    AutoPostTweetRequest, AutoPostTweetResponse
)

def get_post_tweet_with_tweepy():
    from app.services.twitter_service import post_tweet_with_tweepy
    return post_tweet_with_tweepy

from app.services.twitter_service import post_tweet_v2
from app.auth.twitter_oauth import get_authorization_url, fetch_token
from app.services.github_service import fetch_latest_commit_message
from app.services.openai_service import generate_tweet_with_openai

router = APIRouter()

global_oauth2_handler = None

@router.post("/post_tweet", response_model=PostTweetResponse)
def post_tweet(req: PostTweetRequest, post_tweet_with_tweepy=Depends(get_post_tweet_with_tweepy)):
    result = post_tweet_with_tweepy(req.tweet)
    return PostTweetResponse(**result)

@router.post("/twitter_auth", response_model=TwitterAuthResponse)
def twitter_auth():
    global global_oauth2_handler
    url, state, handler = get_authorization_url()
    global_oauth2_handler = handler
    return TwitterAuthResponse(authorization_url=url, state=state)

@router.post("/post_tweet_with_auth", response_model=TwitterTokenResponse)
def post_tweet_with_auth(req: TwitterTokenRequest):
    global global_oauth2_handler
    if global_oauth2_handler is None:
        raise HTTPException(status_code=500, detail="認証フローが初期化されていません")
    token = fetch_token(global_oauth2_handler, req.redirect_response)
    response = post_tweet_v2(token["access_token"], req.tweet_text)
    return TwitterTokenResponse(status="ok", tweet_response=response)

@router.post("/auto_post_tweet", response_model=AutoPostTweetResponse)
def auto_post_tweet(req: AutoPostTweetRequest):
    global global_oauth2_handler
    # 1. GitHub APIから最新コミットを取得
    commit_message = fetch_latest_commit_message(req.repository)
    # 2. OpenAIでツイート案を生成（言語指定対応）
    tweet_text = generate_tweet_with_openai(commit_message, req.repository, req.language)
    # 3. X認証→投稿
    if global_oauth2_handler is None:
        raise HTTPException(status_code=500, detail="認証フローが初期化されていません")
    token = fetch_token(global_oauth2_handler, req.redirect_response)
    response = post_tweet_v2(token["access_token"], tweet_text)
    return AutoPostTweetResponse(status="ok", tweet_text=tweet_text, tweet_response=response) 