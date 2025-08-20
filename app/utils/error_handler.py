"""
統一エラーハンドリングとログ管理システム
"""
import logging
import time
import traceback
from typing import Dict, Any, Optional
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
import redis
import json
from app.config import settings

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Redis接続（エラー統計用）
try:
    # Redis接続（本番環境対応）
    redis_url = settings.get_redis_url()
    if settings.REDIS_URL:
        redis_client = redis.from_url(redis_url, decode_responses=True)
    else:
        redis_client = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, decode_responses=True)
except Exception as e:
    logger.warning(f"Redis接続エラー（エラー統計無効）: {e}")
    redis_client = None

class ServiceError(Exception):
    """サービス固有のエラー基底クラス"""
    def __init__(self, message: str, error_code: str = None, details: Dict[str, Any] = None):
        self.message = message
        self.error_code = error_code or "UNKNOWN_ERROR"
        self.details = details or {}
        super().__init__(self.message)

class GitHubAPIError(ServiceError):
    """GitHub API関連エラー"""
    def __init__(self, message: str, status_code: int = None, **kwargs):
        super().__init__(message, "GITHUB_API_ERROR", {"status_code": status_code, **kwargs})

class OpenAIAPIError(ServiceError):
    """OpenAI API関連エラー"""
    def __init__(self, message: str, model: str = None, **kwargs):
        super().__init__(message, "OPENAI_API_ERROR", {"model": model, **kwargs})

class TwitterAPIError(ServiceError):
    """Twitter API関連エラー"""
    def __init__(self, message: str, status_code: int = None, **kwargs):
        super().__init__(message, "TWITTER_API_ERROR", {"status_code": status_code, **kwargs})

class RateLimitError(ServiceError):
    """レート制限エラー"""
    def __init__(self, service: str, reset_time: int = None, **kwargs):
        message = f"{service} APIレート制限に達しました"
        super().__init__(message, "RATE_LIMIT_ERROR", {"service": service, "reset_time": reset_time, **kwargs})

def log_error(error: Exception, context: Dict[str, Any] = None, request: Request = None):
    """エラーログを記録"""
    error_data = {
        "timestamp": time.time(),
        "error_type": type(error).__name__,
        "error_message": str(error),
        "traceback": traceback.format_exc(),
        "context": context or {},
    }
    
    if request:
        error_data["request_info"] = {
            "method": request.method,
            "url": str(request.url),
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
        }
    
    # 詳細ログ出力
    logger.error(f"エラー発生: {error_data}")
    
    # Redis統計に記録
    if redis_client:
        try:
            error_key = f"error_stats:{type(error).__name__}"
            redis_client.incr(error_key)
            redis_client.expire(error_key, 86400)  # 24時間保持
            
            # 詳細エラー情報（最新100件）
            detailed_key = "error_details"
            redis_client.lpush(detailed_key, json.dumps(error_data))
            redis_client.ltrim(detailed_key, 0, 99)  # 最新100件のみ保持
        except Exception as e:
            logger.warning(f"エラー統計記録失敗: {e}")

def create_error_response(
    error: Exception, 
    status_code: int = 500,
    request: Request = None,
    context: Dict[str, Any] = None
) -> JSONResponse:
    """統一エラーレスポンスを生成"""
    
    # エラーログ記録
    log_error(error, context, request)
    
    # レスポンス用エラー情報
    error_response = {
        "error": True,
        "error_type": type(error).__name__,
        "message": str(error),
        "timestamp": time.time(),
    }
    
    # ServiceErrorの詳細情報を含める
    if isinstance(error, ServiceError):
        error_response["error_code"] = error.error_code
        error_response["details"] = error.details
        
        # 適切なHTTPステータスコードを設定
        if isinstance(error, RateLimitError):
            status_code = 429
        elif isinstance(error, (GitHubAPIError, OpenAIAPIError, TwitterAPIError)):
            status_code = error.details.get("status_code", 502)
    
    # 本番環境では詳細なエラー情報を隠す
    if settings.ENVIRONMENT == "production":
        error_response.pop("traceback", None)
        if status_code >= 500:
            error_response["message"] = "内部サーバーエラーが発生しました"
    
    return JSONResponse(
        status_code=status_code,
        content=error_response
    )

async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """グローバル例外ハンドラー"""
    return create_error_response(exc, request=request)

def get_error_statistics() -> Dict[str, Any]:
    """エラー統計を取得"""
    if not redis_client:
        return {"error": "Redis接続なし"}
    
    try:
        # エラー種別ごとの統計
        error_keys = redis_client.keys("error_stats:*")
        stats = {}
        for key in error_keys:
            error_type = key.replace("error_stats:", "")
            count = redis_client.get(key)
            stats[error_type] = int(count) if count else 0
        
        # 最新エラー詳細（上位10件）
        recent_errors = redis_client.lrange("error_details", 0, 9)
        recent_details = []
        for error_json in recent_errors:
            try:
                error_data = json.loads(error_json)
                # 機密情報を除去
                safe_error = {
                    "timestamp": error_data.get("timestamp"),
                    "error_type": error_data.get("error_type"),
                    "error_message": error_data.get("error_message"),
                    "context": error_data.get("context", {})
                }
                recent_details.append(safe_error)
            except:
                continue
        
        return {
            "error_counts": stats,
            "recent_errors": recent_details,
            "total_errors": sum(stats.values())
        }
    except Exception as e:
        logger.warning(f"エラー統計取得失敗: {e}")
        return {"error": f"統計取得エラー: {str(e)}"}

class CircuitBreaker:
    """サーキットブレーカーパターン実装"""
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def can_execute(self) -> bool:
        """実行可能かチェック"""
        if self.state == "CLOSED":
            return True
        
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
                return True
            return False
        
        if self.state == "HALF_OPEN":
            return True
        
        return False
    
    def on_success(self):
        """成功時の処理"""
        self.failure_count = 0
        self.state = "CLOSED"
    
    def on_failure(self):
        """失敗時の処理"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"

# サービス別サーキットブレーカー
github_circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=300)
openai_circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)
twitter_circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=180)
