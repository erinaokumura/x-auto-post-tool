"""
システム管理・監視APIエンドポイント
"""
from fastapi import APIRouter, Depends, HTTPException
from app.utils.error_handler import get_error_statistics
from app.services.oauth_service import OAuthService
from app.db import get_db
from app.api.auth import get_current_user
from app.models import User
from sqlalchemy.orm import Session
import redis
import time
import psutil
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/health")
def health_check():
    """ヘルスチェック（詳細版）"""
    health_data = {
        "status": "healthy",
        "timestamp": time.time(),
        "services": {}
    }
    
    # データベース接続チェック
    try:
        from app.db import get_db
        db = next(get_db())
        db.execute("SELECT 1")
        health_data["services"]["database"] = "healthy"
    except Exception as e:
        health_data["services"]["database"] = f"unhealthy: {str(e)}"
        health_data["status"] = "degraded"
    
    # Redis接続チェック
    try:
        from app.config import settings
        # Redis接続（本番環境対応）
        redis_url = settings.get_redis_url()
        if settings.REDIS_URL:
            redis_client = redis.from_url(redis_url)
        else:
            redis_client = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)
        redis_client.ping()
        health_data["services"]["redis"] = "healthy"
    except Exception as e:
        health_data["services"]["redis"] = f"unhealthy: {str(e)}"
        health_data["status"] = "degraded"
    
    # 外部API接続チェック（簡単なチェック）
    health_data["services"]["external_apis"] = {
        "github": "not_tested",
        "openai": "not_tested", 
        "twitter": "not_tested"
    }
    
    return health_data

@router.get("/metrics")
def get_system_metrics():
    """システムメトリクスを取得"""
    try:
        metrics = {
            "timestamp": time.time(),
            "system": {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory": {
                    "percent": psutil.virtual_memory().percent,
                    "available_gb": round(psutil.virtual_memory().available / (1024**3), 2),
                    "used_gb": round(psutil.virtual_memory().used / (1024**3), 2)
                },
                "disk": {
                    "percent": psutil.disk_usage('/').percent,
                    "free_gb": round(psutil.disk_usage('/').free / (1024**3), 2)
                }
            },
            "error_statistics": get_error_statistics()
        }
        
        # Redis統計
        try:
            from app.config import settings
            # Redis接続（本番環境対応）
            if settings.REDIS_URL:
                redis_client = redis.from_url(settings.get_redis_url(), decode_responses=True)
            else:
                redis_client = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, decode_responses=True)
            redis_info = redis_client.info()
            metrics["redis"] = {
                "used_memory_mb": round(redis_info.get("used_memory", 0) / (1024**2), 2),
                "connected_clients": redis_info.get("connected_clients", 0),
                "total_commands_processed": redis_info.get("total_commands_processed", 0)
            }
        except:
            metrics["redis"] = {"status": "unavailable"}
        
        return metrics
    except Exception as e:
        logger.error(f"メトリクス取得エラー: {e}")
        raise HTTPException(status_code=500, detail=f"メトリクス取得失敗: {str(e)}")

@router.get("/cache/stats")
def get_cache_statistics():
    """キャッシュ統計を取得"""
    try:
        from app.config import settings
        redis_client = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, decode_responses=True)
        
        # キャッシュキー統計
        github_keys = redis_client.keys("github_commit:*")
        openai_keys = redis_client.keys("openai_tweet:*")
        tweet_history_keys = redis_client.keys("tweet_history:*")
        
        cache_stats = {
            "timestamp": time.time(),
            "github_cache": {
                "total_keys": len(github_keys),
                "sample_keys": github_keys[:5] if github_keys else []
            },
            "openai_cache": {
                "total_keys": len(openai_keys),
                "sample_keys": openai_keys[:5] if openai_keys else []
            },
            "tweet_history": {
                "total_keys": len(tweet_history_keys),
                "sample_keys": tweet_history_keys[:5] if tweet_history_keys else []
            },
            "redis_info": {
                "keyspace": redis_client.info("keyspace"),
                "memory": redis_client.info("memory")
            }
        }
        
        return cache_stats
    except Exception as e:
        logger.error(f"キャッシュ統計取得エラー: {e}")
        raise HTTPException(status_code=500, detail=f"キャッシュ統計取得失敗: {str(e)}")

@router.post("/cache/clear")
def clear_cache(
    cache_type: str = "all",
    user: User = Depends(get_current_user)
):
    """キャッシュをクリア（管理者機能）"""
    try:
        from app.config import settings
        redis_client = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, decode_responses=True)
        
        cleared_count = 0
        
        if cache_type == "all" or cache_type == "github":
            github_keys = redis_client.keys("github_commit:*")
            if github_keys:
                cleared_count += redis_client.delete(*github_keys)
        
        if cache_type == "all" or cache_type == "openai":
            openai_keys = redis_client.keys("openai_tweet:*")
            if openai_keys:
                cleared_count += redis_client.delete(*openai_keys)
        
        if cache_type == "all" or cache_type == "tweet_history":
            tweet_keys = redis_client.keys("tweet_history:*")
            if tweet_keys:
                cleared_count += redis_client.delete(*tweet_keys)
        
        logger.info(f"キャッシュクリア実行: {cache_type}, {cleared_count}個のキーを削除, ユーザー: {user.id}")
        
        return {
            "message": f"{cache_type}キャッシュをクリアしました",
            "cleared_keys": cleared_count,
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"キャッシュクリアエラー: {e}")
        raise HTTPException(status_code=500, detail=f"キャッシュクリア失敗: {str(e)}")

@router.get("/performance/history")
def get_performance_history():
    """パフォーマンス履歴を取得"""
    try:
        from app.config import settings
        redis_client = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, decode_responses=True)
        
        # パフォーマンス履歴データを取得（最新50件）
        performance_data = redis_client.lrange("performance_history", 0, 49)
        
        history = []
        for data_json in performance_data:
            try:
                import json
                data = json.loads(data_json)
                history.append(data)
            except:
                continue
        
        return {
            "performance_history": history,
            "total_records": len(history),
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"パフォーマンス履歴取得エラー: {e}")
        raise HTTPException(status_code=500, detail=f"パフォーマンス履歴取得失敗: {str(e)}")

@router.get("/api/usage_stats")  
def get_api_usage_stats():
    """API使用統計を取得"""
    try:
        from app.config import settings
        redis_client = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, decode_responses=True)
        
        # API使用回数統計
        api_stats = {}
        
        # レート制限キーから使用状況を推測
        rate_limit_keys = redis_client.keys("*_rate_limit:*")
        
        for key in rate_limit_keys:
            try:
                parts = key.split(":")
                if len(parts) >= 2:
                    api_name = parts[0].replace("_rate_limit", "")
                    count = redis_client.get(key)
                    if api_name not in api_stats:
                        api_stats[api_name] = 0
                    api_stats[api_name] += int(count) if count else 0
            except:
                continue
        
        return {
            "api_usage": api_stats,
            "timestamp": time.time(),
            "note": "過去24時間の概算使用量"
        }
    except Exception as e:
        logger.error(f"API使用統計取得エラー: {e}")
        raise HTTPException(status_code=500, detail=f"API使用統計取得失敗: {str(e)}")
