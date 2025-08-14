from fastapi import Request, Response
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.config import settings

class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    """本番環境でHTTPS強制リダイレクトを行うミドルウェア"""
    
    async def dispatch(self, request: Request, call_next):
        # 本番環境かつHTTPの場合のみリダイレクト
        if (settings.ENVIRONMENT == "production" and 
            request.url.scheme == "http" and 
            request.headers.get("x-forwarded-proto") != "https"):
            
            # HTTPSにリダイレクト
            https_url = request.url.replace(scheme="https")
            return RedirectResponse(url=str(https_url), status_code=301)
        
        response = await call_next(request)
        return response
