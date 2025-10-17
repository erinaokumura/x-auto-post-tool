from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from app.api import twitter, openai, auth
from app.config import settings
from app.middleware.rate_limiter import limiter
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.middleware.https_redirect import HTTPSRedirectMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

app = FastAPI()

# HTTPS強制リダイレクト（本番環境のみ）
if settings.ENVIRONMENT == "production":
    app.add_middleware(HTTPSRedirectMiddleware)

# セキュリティヘッダーミドルウェア
app.add_middleware(SecurityHeadersMiddleware)

# レート制限の設定
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS設定（本番環境対応）
cors_origins = settings.get_cors_origins()

# デバッグ用：CORS設定を出力
print(f"CORS Origins: {cors_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins if cors_origins else ["*"],  # 緊急対応：設定が空の場合は全許可
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# APIルーター登録
app.include_router(twitter.router, prefix="/api")
app.include_router(openai.router, prefix="/api")
app.include_router(auth.router, prefix="/api")

# システム管理API
from app.api import system
app.include_router(system.router, prefix="/api/system")

# グローバル例外ハンドラー
from app.utils.error_handler import global_exception_handler
app.add_exception_handler(Exception, global_exception_handler)

@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI!"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/callback")
async def twitter_callback_redirect(request: Request):
    """Twitter OAuth コールバックを /api/auth/twitter/callback にリダイレクト"""
    # クエリパラメータを取得
    query_params = str(request.query_params)
    
    # 環境に応じてフロントエンドURLを決定
    is_railway_env = settings.ENVIRONMENT in ("production", "development")
    
    if is_railway_env:
        # Railway環境（development/production共通）
        frontend_base_url = "http://localhost:3000"
        # frontend_base_url = "https://x-auto-post-tool-development.up.railway.app"
    else:
        # ローカル開発環境
        frontend_base_url = "http://localhost:3000"
    
    # フロントエンドのコールバックページにリダイレクト
    frontend_callback_url = f"{frontend_base_url}/callback?{query_params}"
    
    return RedirectResponse(url=frontend_callback_url)