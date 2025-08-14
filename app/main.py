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

# CORS設定
cors_origins = settings.CORS_ORIGINS.split(",") if settings.CORS_ORIGINS else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# APIルーター登録
app.include_router(twitter.router, prefix="/api")
app.include_router(openai.router, prefix="/api")
app.include_router(auth.router, prefix="/api")

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
    
    # フロントエンドのコールバックページにリダイレクト
    frontend_callback_url = f"http://localhost:3000/callback?{query_params}"
    
    return RedirectResponse(url=frontend_callback_url)