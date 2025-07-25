from fastapi import APIRouter, HTTPException, Depends
from app.schemas.twitter import (
    PostTweetRequest, PostTweetResponse,
    TwitterAuthRequest, TwitterAuthResponse,
    TwitterTokenRequest, TwitterTokenResponse,
    AutoPostTweetRequest, AutoPostTweetResponse
)
from app.services.twitter_service import post_tweet_v2
from app.services.oauth_service import OAuthService
from app.db import get_db
from app.api.auth import get_current_user
from app.models import User
from sqlalchemy.orm import Session

router = APIRouter()

@router.post("/post_tweet", response_model=PostTweetResponse)
def post_tweet(
    req: PostTweetRequest, 
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """認証済みユーザーのトークンを使用してツイート投稿"""
    oauth_service = OAuthService(db)
    access_token = oauth_service.get_decrypted_access_token(user.id, "twitter")
    
    if not access_token:
        raise HTTPException(status_code=401, detail="Twitter認証が必要です")
    
    try:
        response = post_tweet_v2(access_token, req.tweet)
        return PostTweetResponse(status="ok", tweet_response=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ツイート投稿エラー: {str(e)}")

@router.post("/auto_post_tweet", response_model=AutoPostTweetResponse)
def auto_post_tweet(
    req: AutoPostTweetRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """認証済みユーザーのトークンを使用して自動投稿"""
    from app.services.github_service import fetch_latest_commit_message
    from app.services.openai_service import generate_tweet_with_openai
    
    oauth_service = OAuthService(db)
    access_token = oauth_service.get_decrypted_access_token(user.id, "twitter")
    
    if not access_token:
        raise HTTPException(status_code=401, detail="Twitter認証が必要です")
    
    try:
        # 1. GitHub APIから最新コミットを取得
        commit_message = fetch_latest_commit_message(req.repository)
        
        # 2. OpenAIでツイート案を生成（言語指定対応）
        tweet_text = generate_tweet_with_openai(commit_message, req.repository, req.language)
        
        # 3. Xに投稿
        response = post_tweet_v2(access_token, tweet_text)
        
        return AutoPostTweetResponse(
            status="ok", 
            tweet_text=tweet_text, 
            tweet_response=response
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"自動投稿エラー: {str(e)}")

@router.get("/auth_status")
def twitter_auth_status(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Twitter認証状態を確認"""
    oauth_service = OAuthService(db)
    oauth_token = oauth_service.get_valid_token(user.id, "twitter")
    
    return {
        "is_authenticated": oauth_token is not None,
        "expires_at": oauth_token.expires_at if oauth_token else None,
        "scope": oauth_token.scope if oauth_token else None
    } 