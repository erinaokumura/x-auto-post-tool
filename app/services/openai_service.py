import os
import redis
import json
import time
import hashlib
from typing import Optional, AsyncIterator
from fastapi import HTTPException
from openai import OpenAI, AsyncOpenAI
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Redisクライアント（キャッシュ用）
# Redis接続（本番環境対応）
def get_redis_client():
    redis_url = settings.get_redis_url()
    if settings.REDIS_URL:
        return redis.from_url(redis_url, decode_responses=True)
    else:
        return redis.from_url(settings.get_redis_url(), decode_responses=True)

redis_client = get_redis_client()

def get_openai_api_key():
    api_key = settings.OPENAI_API_KEY
    if not api_key:
        raise HTTPException(status_code=500, detail="OpenAI APIキーが設定されていません")
    return api_key

def _create_cache_key(commit_message: str, repository: str, language: str) -> str:
    """キャッシュキーを生成"""
    content = f"{commit_message}:{repository}:{language}"
    return f"openai_tweet:{hashlib.md5(content.encode()).hexdigest()}"

def _build_optimized_prompt(commit_message: str, repository: str, language: str) -> str:
    """最適化されたプロンプトを構築"""
    # プロンプトをより効率的に構築（トークン数削減）
    if language == 'en':
        return f"""Create engaging tweet (max 140 chars) for:
Repo: {repository}
Commit: {commit_message}
Style: Pieter Levels (indie dev)
Include hashtags."""
    else:
        return f"""以下のコミットから魅力的なツイート（140字以内）を作成:
リポジトリ: {repository}
コミット: {commit_message}
要件: ハッシュタグ含む、個人開発者風、熱量のある表現"""

async def generate_tweet_with_openai_async(
    commit_message: str, 
    repository: str, 
    language: str = 'ja',
    use_cache: bool = True
) -> str:
    """非同期版OpenAI API呼び出し（推奨）"""
    cache_key = _create_cache_key(commit_message, repository, language)
    
    # キャッシュ確認（24時間キャッシュ）
    if use_cache:
        try:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                logger.info(f"OpenAI APIキャッシュヒット: {cache_key[:20]}...")
                return json.loads(cached_data)["tweet"]
        except Exception as e:
            logger.warning(f"キャッシュ取得エラー: {e}")
    
    client = AsyncOpenAI(api_key=get_openai_api_key())
    prompt = _build_optimized_prompt(commit_message, repository, language)
    
    try:
        # GPT-4o-miniを使用（コスト効率が良い）
        response = await client.chat.completions.create(
            model="gpt-4o-mini",  # より安価で高性能
            messages=[{"role": "user", "content": prompt}],
            max_tokens=80,  # トークン数削減
            temperature=0.7,  # 一貫性向上
            top_p=0.9,  # 品質向上
        )
        
        content = response.choices[0].message.content if response.choices[0].message else None
        if content is None:
            raise HTTPException(status_code=500, detail="OpenAI APIからツイート案の生成に失敗しました")
        
        tweet = content.strip()
        
        # キャッシュに保存（24時間）
        if use_cache:
            try:
                cache_data = {
                    "tweet": tweet,
                    "timestamp": time.time(),
                    "model": "gpt-4o-mini"
                }
                redis_client.setex(cache_key, 86400, json.dumps(cache_data))
                logger.info(f"OpenAI APIレスポンスをキャッシュ: {cache_key[:20]}...")
            except Exception as e:
                logger.warning(f"キャッシュ保存エラー: {e}")
        
        return tweet
        
    except Exception as e:
        logger.error(f"OpenAI API非同期エラー: {str(e)}")
        raise HTTPException(status_code=500, detail=f"OpenAI APIエラー: {str(e)}")

async def generate_tweet_stream_async(
    commit_message: str, 
    repository: str, 
    language: str = 'ja'
) -> AsyncIterator[str]:
    """ストリーミング版（リアルタイム表示用）"""
    client = AsyncOpenAI(api_key=get_openai_api_key())
    prompt = _build_optimized_prompt(commit_message, repository, language)
    
    try:
        stream = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=80,
            temperature=0.7,
            stream=True
        )
        
        async for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content
                
    except Exception as e:
        logger.error(f"OpenAI APIストリーミングエラー: {str(e)}")
        raise HTTPException(status_code=500, detail=f"OpenAI APIストリーミングエラー: {str(e)}")

def generate_tweet_with_openai(commit_message: str, repository: str, language: str = 'ja') -> str:
    """同期版（後方互換性のため保持）"""
    cache_key = _create_cache_key(commit_message, repository, language)
    
    # キャッシュ確認
    try:
        cached_data = redis_client.get(cache_key)
        if cached_data:
            logger.info(f"OpenAI APIキャッシュヒット: {cache_key[:20]}...")
            return json.loads(cached_data)["tweet"]
    except Exception as e:
        logger.warning(f"キャッシュ取得エラー: {e}")
    
    client = OpenAI(api_key=get_openai_api_key())
    prompt = _build_optimized_prompt(commit_message, repository, language)
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=80,
            temperature=0.7,
            top_p=0.9,
        )
        
        content = response.choices[0].message.content if response.choices[0].message else None
        if content is None:
            raise HTTPException(status_code=500, detail="OpenAI APIからツイート案の生成に失敗しました")
        
        tweet = content.strip()
        
        # キャッシュに保存
        try:
            cache_data = {
                "tweet": tweet,
                "timestamp": time.time(),
                "model": "gpt-4o-mini"
            }
            redis_client.setex(cache_key, 86400, json.dumps(cache_data))
        except Exception as e:
            logger.warning(f"キャッシュ保存エラー: {e}")
        
        return tweet
        
    except Exception as e:
        logger.error(f"OpenAI API同期エラー: {str(e)}")
        raise HTTPException(status_code=500, detail=f"OpenAI APIエラー: {str(e)}")

def batch_generate_tweets(requests: list, language: str = 'ja') -> list:
    """複数のツイート案を一括生成（効率向上）"""
    results = []
    client = OpenAI(api_key=get_openai_api_key())
    
    for req in requests:
        commit_message = req.get("commit_message")
        repository = req.get("repository")
        
        try:
            tweet = generate_tweet_with_openai(commit_message, repository, language)
            results.append({"success": True, "tweet": tweet, "repository": repository})
        except Exception as e:
            results.append({"success": False, "error": str(e), "repository": repository})
    
    return results 