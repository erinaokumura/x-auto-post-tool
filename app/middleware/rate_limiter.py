from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from app.config import settings
import redis

# Redisクライアント（レート制限用）
rate_limit_redis = redis.Redis(
    host=settings.REDIS_HOST, 
    port=settings.REDIS_PORT, 
    db=2,  # レート制限専用DB
    decode_responses=True
)

# Limiterの設定
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/2"
)

def get_client_ip(request: Request):
    """クライアントIPアドレスを取得"""
    # プロキシ経由の場合のX-Forwarded-Forヘッダーもチェック
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    return request.client.host if request.client else "unknown"

# IP + ユーザーIDでのレート制限
def get_user_id_key(request: Request):
    """認証済みユーザーの場合はユーザーIDを、未認証の場合はIPアドレスを使用"""
    # セッションからユーザーIDを取得
    session_id = request.cookies.get("session_id")
    if session_id:
        # SessionServiceからユーザーIDを取得（簡易版）
        try:
            from app.services.session_service import SessionService
            user_id = SessionService.get_user_id(session_id)
            if user_id:
                return f"user:{user_id}"
        except:
            pass
    
    # 未認証の場合はIPアドレスを使用
    return f"ip:{get_client_ip(request)}"

# カスタムキー関数
def rate_limit_key_func(request: Request):
    """レート制限のキー関数"""
    return get_user_id_key(request)

# ユーザー用Limiter
user_limiter = Limiter(
    key_func=rate_limit_key_func,
    storage_uri=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/2"
)
