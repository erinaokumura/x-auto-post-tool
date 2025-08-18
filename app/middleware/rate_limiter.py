from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from app.config import settings

# Redis接続のチェック
redis_available = False

try:
    import redis
    redis_client = redis.Redis(
        host=settings.REDIS_HOST, 
        port=settings.REDIS_PORT, 
        db=2,  # レート制限専用DB
        decode_responses=True
    )
    # 接続テスト
    redis_client.ping()
    redis_available = True
    print(f"Redis接続成功: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
except ImportError:
    print("redisモジュールが見つかりません。メモリ内でレート制限を実行します。")
except Exception as e:
    print(f"Redis接続失敗: {e}. レート制限機能はメモリ内で動作します。")

# CP932エンコーディング問題を回避するための空のUTF-8ファイル作成
import tempfile
temp_env_file = tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False, encoding='utf-8')
temp_env_file.write("# Empty config file to avoid encoding issues\n")
temp_env_file.close()

# Limiterの設定
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/2" if redis_available else "memory://",
    enabled=True,
    config_filename=temp_env_file.name  # 空のUTF-8ファイルを指定
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
    storage_uri=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/2" if redis_available else "memory://",
    enabled=True,
    config_filename=temp_env_file.name  # 同じ空のUTF-8ファイルを指定
)

# 一時ファイルのクリーンアップ（アプリケーション終了時に自動削除される）
import atexit
atexit.register(lambda: __import__('os').unlink(temp_env_file.name) if __import__('os').path.exists(temp_env_file.name) else None)
