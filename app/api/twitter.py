from fastapi import APIRouter, HTTPException, Depends, Request
from app.schemas.twitter import (
    PostTweetRequest, PostTweetResponse,
    TwitterAuthRequest, TwitterAuthResponse,
    TwitterTokenRequest, TwitterTokenResponse,
    AutoPostTweetRequest, AutoPostTweetResponse
)
from app.services.twitter_service import post_tweet_v2, post_tweet_v2_async, is_duplicate_tweet
from app.services.oauth_service import OAuthService
from app.db import get_db
from app.api.auth import get_current_user
from app.models import User
from app.middleware.rate_limiter import user_limiter
from app.utils.error_handler import (
    TwitterAPIError, RateLimitError, create_error_response, 
    twitter_circuit_breaker, log_error
)
from sqlalchemy.orm import Session
import time
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/post_tweet", response_model=PostTweetResponse)
@user_limiter.limit("10/minute")  # 1分間に10回まで
def post_tweet(
    request: Request,
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
        response = post_tweet_v2(access_token, req.tweet_text)
        tweet_id = response.get("data", {}).get("id") if response else None
        return PostTweetResponse(
            success=True,
            tweet_id=tweet_id,
            message="ツイートが正常に投稿されました"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ツイート投稿エラー: {str(e)}")

@router.post("/auto_post_tweet", response_model=AutoPostTweetResponse)
@user_limiter.limit("5/minute")  # より厳しい制限（AI処理を含むため）
def auto_post_tweet(
    request: Request,
    req: AutoPostTweetRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """認証済みユーザーのトークンを使用して自動投稿（最適化版）"""
    from app.services.github_service import fetch_latest_commit_message
    from app.services.openai_service import generate_tweet_with_openai
    from app.utils.error_handler import GitHubAPIError, OpenAIAPIError
    
    start_time = time.time()
    context = {
        "user_id": user.id,
        "repository": req.repository,
        "language": req.language
    }
    
    # サーキットブレーカーチェック
    if not twitter_circuit_breaker.can_execute():
        raise RateLimitError("Twitter", reset_time=twitter_circuit_breaker.recovery_timeout)
    
    oauth_service = OAuthService(db)
    access_token = oauth_service.get_decrypted_access_token(user.id, "twitter")
    
    if not access_token:
        raise HTTPException(status_code=401, detail="Twitter認証が必要です")
    
    try:
        # 1. GitHub APIから最新コミットを取得
        try:
            commit_message = fetch_latest_commit_message(req.repository)
        except Exception as e:
            twitter_circuit_breaker.on_failure()
            raise GitHubAPIError(f"コミット取得失敗: {str(e)}", context=context)
        
        # 2. OpenAIでツイート案を生成（言語指定対応）
        try:
            tweet_text = generate_tweet_with_openai(commit_message, req.repository, req.language)
        except Exception as e:
            raise OpenAIAPIError(f"ツイート生成失敗: {str(e)}", context=context)
        
        # 3. 重複チェック
        if is_duplicate_tweet(tweet_text):
            logger.warning(f"重複ツイート検出: {tweet_text[:50]}...")
            raise TwitterAPIError("重複する内容のツイートが検出されました", context=context)
        
        # 4. Xに投稿
        try:
            response = post_tweet_v2(access_token, tweet_text)
            twitter_circuit_breaker.on_success()
        except Exception as e:
            twitter_circuit_breaker.on_failure()
            raise TwitterAPIError(f"投稿失敗: {str(e)}", context=context)
        
        # 実行時間ログ
        execution_time = time.time() - start_time
        logger.info(f"自動投稿完了: {execution_time:.2f}秒, ユーザー: {user.id}")
        
        return AutoPostTweetResponse(
            status="ok", 
            tweet_text=tweet_text, 
            tweet_response=response
        )
        
    except (GitHubAPIError, OpenAIAPIError, TwitterAPIError) as service_error:
        return create_error_response(service_error, request=request, context=context)
    except Exception as e:
        twitter_circuit_breaker.on_failure()
        log_error(e, context=context, request=request)
        raise HTTPException(status_code=500, detail=f"自動投稿エラー: {str(e)}")

@router.post("/auto_post_tweet_async", response_model=AutoPostTweetResponse)
@user_limiter.limit("5/minute")  
async def auto_post_tweet_async(
    request: Request,
    req: AutoPostTweetRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """非同期版自動投稿（推奨）"""
    from app.services.github_service import fetch_latest_commit_message_async
    from app.services.openai_service import generate_tweet_with_openai_async
    
    start_time = time.time()
    context = {
        "user_id": user.id,
        "repository": req.repository,
        "language": req.language,
        "async_version": True
    }
    
    if not twitter_circuit_breaker.can_execute():
        raise RateLimitError("Twitter", reset_time=twitter_circuit_breaker.recovery_timeout)
    
    oauth_service = OAuthService(db)
    access_token = oauth_service.get_decrypted_access_token(user.id, "twitter")
    
    if not access_token:
        raise HTTPException(status_code=401, detail="Twitter認証が必要です")
    
    try:
        # 1. GitHub APIから最新コミットを取得（非同期）
        try:
            commit_message = await fetch_latest_commit_message_async(req.repository)
        except Exception as e:
            raise GitHubAPIError(f"コミット取得失敗: {str(e)}", context=context)
        
        # 2. OpenAIでツイート案を生成（非同期）
        try:
            tweet_text = await generate_tweet_with_openai_async(commit_message, req.repository, req.language)
        except Exception as e:
            raise OpenAIAPIError(f"ツイート生成失敗: {str(e)}", context=context)
        
        # 3. 重複チェック
        if is_duplicate_tweet(tweet_text):
            logger.warning(f"重複ツイート検出: {tweet_text[:50]}...")
            raise TwitterAPIError("重複する内容のツイートが検出されました", context=context)
        
        # 4. Xに投稿（非同期）
        try:
            response = await post_tweet_v2_async(access_token, tweet_text)
            twitter_circuit_breaker.on_success()
        except Exception as e:
            twitter_circuit_breaker.on_failure()
            raise TwitterAPIError(f"投稿失敗: {str(e)}", context=context)
        
        # 実行時間ログ
        execution_time = time.time() - start_time
        logger.info(f"非同期自動投稿完了: {execution_time:.2f}秒, ユーザー: {user.id}")
        
        return AutoPostTweetResponse(
            status="ok", 
            tweet_text=tweet_text, 
            tweet_response=response
        )
        
    except (GitHubAPIError, OpenAIAPIError, TwitterAPIError) as service_error:
        return create_error_response(service_error, request=request, context=context)
    except Exception as e:
        twitter_circuit_breaker.on_failure()
        log_error(e, context=context, request=request)
        raise HTTPException(status_code=500, detail=f"非同期自動投稿エラー: {str(e)}")

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