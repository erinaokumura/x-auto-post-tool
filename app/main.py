from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from app.api import twitter, openai, auth

app = FastAPI()

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