from app.config import settings
import tweepy
import requests
import httpx
import asyncio
import time
import redis
import json
from typing import Dict, Any, Optional, List
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

# Redisクライアント（投稿履歴・レート制限管理）
# Redis接続（本番環境対応）
def get_redis_client():
    redis_url = settings.get_redis_url()
    if settings.REDIS_URL:
        return redis.from_url(redis_url, decode_responses=True)
    else:
        return redis.from_url(settings.get_redis_url(), decode_responses=True)

redis_client = get_redis_client()

def get_tweepy_client():
    consumer_key = settings.TWITTER_CLIENT_ID
    consumer_secret = settings.TWITTER_CLIENT_SECRET
    access_token = settings.TWITTER_ACCESS_TOKEN
    access_token_secret = settings.TWITTER_ACCESS_TOKEN_SECRET
    if not all([consumer_key, consumer_secret, access_token, access_token_secret]):
        raise HTTPException(status_code=500, detail="Twitter API認証情報が不足しています")
    auth = tweepy.OAuth1UserHandler(
        consumer_key, consumer_secret, access_token, access_token_secret
    )
    api = tweepy.API(auth)
    return api

def post_tweet_with_tweepy(tweet: str):
    try:
        api = get_tweepy_client()
        api.update_status(status=tweet)
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Twitter APIエラー: {str(e)}")

async def post_tweet_v2_async(access_token: str, tweet_text: str, retry_count: int = 3) -> Dict[str, Any]:
    """非同期版Twitter API v2投稿（リトライ機能付き）"""
    url = "https://api.twitter.com/2/tweets"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    json_data = {
        "text": tweet_text
    }
    
    for attempt in range(retry_count):
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, headers=headers, json=json_data)
                
                # レート制限対応
                if response.status_code == 429:
                    wait_time = int(response.headers.get("x-rate-limit-reset", 900))
                    logger.warning(f"Twitter APIレート制限。{wait_time}秒待機...")
                    
                    if attempt < retry_count - 1:
                        await asyncio.sleep(min(wait_time, 60))  # 最大60秒待機
                        continue
                    else:
                        raise HTTPException(status_code=429, detail="Twitter APIレート制限により投稿できませんでした")
                
                # 成功
                if response.status_code == 201:
                    result = response.json()
                    
                    # 投稿履歴をRedisに保存
                    try:
                        post_data = {
                            "tweet_id": result.get("data", {}).get("id"),
                            "text": tweet_text,
                            "timestamp": time.time(),
                            "status": "success"
                        }
                        redis_client.setex(f"tweet_history:{result.get('data', {}).get('id')}", 86400, json.dumps(post_data))
                    except Exception as e:
                        logger.warning(f"投稿履歴保存エラー: {e}")
                    
                    return result
                
                # その他のエラー
                error_detail = f"Twitter API v2エラー: {response.status_code} - {response.text}"
                
                # 一時的なエラーの場合はリトライ
                if response.status_code in [500, 502, 503, 504] and attempt < retry_count - 1:
                    wait_time = (2 ** attempt) + 1  # 指数バックオフ
                    logger.warning(f"一時的エラー。{wait_time}秒後にリトライ... (試行 {attempt + 1}/{retry_count})")
                    await asyncio.sleep(wait_time)
                    continue
                
                raise HTTPException(status_code=response.status_code, detail=error_detail)
                
        except httpx.TimeoutException:
            if attempt < retry_count - 1:
                logger.warning(f"タイムアウト。リトライ... (試行 {attempt + 1}/{retry_count})")
                await asyncio.sleep((2 ** attempt) + 1)
                continue
            raise HTTPException(status_code=408, detail="Twitter API接続タイムアウト")
        
        except httpx.RequestError as e:
            if attempt < retry_count - 1:
                logger.warning(f"接続エラー。リトライ... (試行 {attempt + 1}/{retry_count}): {str(e)}")
                await asyncio.sleep((2 ** attempt) + 1)
                continue
            raise HTTPException(status_code=503, detail=f"Twitter API接続エラー: {str(e)}")
    
    raise HTTPException(status_code=500, detail="Twitter投稿に失敗しました（全リトライ試行完了）")

def post_tweet_v2(access_token: str, tweet_text: str):
    """同期版（後方互換性のため保持）"""
    url = "https://api.twitter.com/2/tweets"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    json_data = {
        "text": tweet_text
    }
    
    try:
        response = requests.post(url, headers=headers, json=json_data, timeout=30)
        
        if response.status_code == 429:
            raise HTTPException(status_code=429, detail="Twitter APIレート制限に達しました")
        
        if response.status_code != 201:
            raise HTTPException(status_code=response.status_code, detail=f"Twitter API v2エラー: {response.text}")
        
        result = response.json()
        
        # 投稿履歴保存
        try:
            post_data = {
                "tweet_id": result.get("data", {}).get("id"),
                "text": tweet_text,
                "timestamp": time.time(),
                "status": "success"
            }
            redis_client.setex(f"tweet_history:{result.get('data', {}).get('id')}", 86400, json.dumps(post_data))
        except Exception as e:
            logger.warning(f"投稿履歴保存エラー: {e}")
        
        return result
        
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=408, detail="Twitter API接続タイムアウト")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=503, detail=f"Twitter API接続エラー: {str(e)}")

async def batch_post_tweets(tweets_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """複数のツイートを効率的に投稿"""
    results = []
    
    # 同時実行数を制限（APIレート制限対策）
    semaphore = asyncio.Semaphore(3)
    
    async def post_single_tweet(tweet_data):
        async with semaphore:
            try:
                access_token = tweet_data["access_token"]
                tweet_text = tweet_data["tweet_text"]
                
                result = await post_tweet_v2_async(access_token, tweet_text)
                return {
                    "success": True,
                    "tweet_id": result.get("data", {}).get("id"),
                    "original_data": tweet_data
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "original_data": tweet_data
                }
    
    # 並列実行
    tasks = [post_single_tweet(tweet_data) for tweet_data in tweets_data]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    return results

def get_tweet_history(tweet_id: str) -> Optional[Dict[str, Any]]:
    """投稿履歴を取得"""
    try:
        data = redis_client.get(f"tweet_history:{tweet_id}")
        if data:
            return json.loads(data)
    except Exception as e:
        logger.warning(f"投稿履歴取得エラー: {e}")
    return None

def is_duplicate_tweet(tweet_text: str, window_hours: int = 24) -> bool:
    """重複投稿チェック"""
    try:
        # 過去24時間の投稿をチェック
        keys = redis_client.keys("tweet_history:*")
        for key in keys:
            data = redis_client.get(key)
            if data:
                post_data = json.loads(data)
                if post_data.get("text") == tweet_text:
                    post_time = post_data.get("timestamp", 0)
                    if time.time() - post_time < window_hours * 3600:
                        return True
    except Exception as e:
        logger.warning(f"重複チェックエラー: {e}")
    
    return False 