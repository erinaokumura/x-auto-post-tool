import requests
import redis
import json
import time
import httpx
from typing import Optional, Dict, Any
from fastapi import HTTPException
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
        return redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, decode_responses=True)

redis_client = get_redis_client()

async def fetch_latest_commit_message_async(repository: str) -> str:
    """非同期でGitHub APIから最新のコミットメッセージを取得（推奨）"""
    cache_key = f"github_commit:{repository}"
    
    # キャッシュから取得を試行（5分間キャッシュ）
    try:
        cached_data = redis_client.get(cache_key)
        if cached_data:
            logger.info(f"GitHub APIキャッシュヒット: {repository}")
            return json.loads(cached_data)["commit_message"]
    except Exception as e:
        logger.warning(f"キャッシュ取得エラー: {e}")
    
    url = settings.GITHUB_API_URL.format(repo=repository)
    
    # HTTPヘッダーでレート制限情報を含む
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "x-auto-post-tool/1.0"
    }
    
    # GitHub認証トークンが設定されている場合は使用（レート制限緩和）
    if hasattr(settings, 'GITHUB_TOKEN') and settings.GITHUB_TOKEN:
        headers["Authorization"] = f"token {settings.GITHUB_TOKEN}"
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(url, headers=headers)
            
            # レート制限情報をログ出力
            if "X-RateLimit-Remaining" in resp.headers:
                remaining = resp.headers["X-RateLimit-Remaining"]
                reset_time = resp.headers.get("X-RateLimit-Reset", "")
                logger.info(f"GitHub API残り回数: {remaining}, リセット時刻: {reset_time}")
            
            if resp.status_code == 403 and "rate limit" in resp.text.lower():
                raise HTTPException(status_code=429, detail="GitHub APIレート制限に達しました。しばらく待ってから再試行してください。")
            
            if resp.status_code != 200:
                error_detail = f"GitHub API エラー: {resp.status_code}"
                try:
                    error_data = resp.json()
                    if "message" in error_data:
                        error_detail += f" - {error_data['message']}"
                except:
                    pass
                raise HTTPException(status_code=resp.status_code, detail=error_detail)
            
            data = resp.json()
            if not data:
                raise HTTPException(status_code=404, detail="コミット情報が見つかりません")
            
            commit_message = data[0]["commit"]["message"]
            
            # キャッシュに保存（5分間）
            try:
                cache_data = {
                    "commit_message": commit_message,
                    "timestamp": time.time()
                }
                redis_client.setex(cache_key, 300, json.dumps(cache_data))
                logger.info(f"GitHub APIレスポンスをキャッシュ: {repository}")
            except Exception as e:
                logger.warning(f"キャッシュ保存エラー: {e}")
            
            return commit_message
            
        except httpx.TimeoutException:
            raise HTTPException(status_code=408, detail="GitHub API接続タイムアウト")
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"GitHub API接続エラー: {str(e)}")

def fetch_latest_commit_message(repository: str) -> str:
    """同期版（後方互換性のため保持）"""
    url = settings.GITHUB_API_URL.format(repo=repository)
    
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "x-auto-post-tool/1.0"
    }
    
    if hasattr(settings, 'GITHUB_TOKEN') and settings.GITHUB_TOKEN:
        headers["Authorization"] = f"token {settings.GITHUB_TOKEN}"
    
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        
        if resp.status_code == 403 and "rate limit" in resp.text.lower():
            raise HTTPException(status_code=429, detail="GitHub APIレート制限に達しました。")
        
        if resp.status_code != 200:
            error_detail = f"GitHub API エラー: {resp.status_code}"
            try:
                error_data = resp.json()
                if "message" in error_data:
                    error_detail += f" - {error_data['message']}"
            except:
                pass
            raise HTTPException(status_code=resp.status_code, detail=error_detail)
        
        data = resp.json()
        if not data:
            raise HTTPException(status_code=404, detail="コミット情報が見つかりません")
        
        commit_message = data[0]["commit"]["message"]
        return commit_message
        
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=408, detail="GitHub API接続タイムアウト")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=503, detail=f"GitHub API接続エラー: {str(e)}") 