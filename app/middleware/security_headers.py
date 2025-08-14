from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.config import settings

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """セキュリティヘッダーを追加するミドルウェア"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Content Security Policy
        # 開発環境と本番環境で異なる設定
        if settings.ENVIRONMENT == "development":
            csp_value = (
                "default-src 'self' 'unsafe-inline' 'unsafe-eval' "
                "http://localhost:3000 http://localhost:8000; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' "
                "http://localhost:3000 http://localhost:8000; "
                "style-src 'self' 'unsafe-inline' "
                "http://localhost:3000 http://localhost:8000; "
                "img-src 'self' data: https: http://localhost:3000; "
                "connect-src 'self' http://localhost:3000 http://localhost:8000 "
                "https://api.openai.com https://api.twitter.com https://upload.twitter.com; "
                "font-src 'self' data:; "
                "object-src 'none'; "
                "media-src 'self'; "
                "frame-src 'none'; "
                "worker-src 'self'; "
                "child-src 'none'; "
                "form-action 'self'; "
                "base-uri 'self';"
            )
        else:
            # 本番環境用のより厳しいCSP
            csp_value = (
                "default-src 'self'; "
                "script-src 'self'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "connect-src 'self' https://api.openai.com https://api.twitter.com https://upload.twitter.com; "
                "font-src 'self' data:; "
                "object-src 'none'; "
                "media-src 'self'; "
                "frame-src 'none'; "
                "worker-src 'self'; "
                "child-src 'none'; "
                "form-action 'self'; "
                "base-uri 'self'; "
                "upgrade-insecure-requests;"
            )
        
        response.headers["Content-Security-Policy"] = csp_value
        
        # Strict Transport Security (HTTPS強制)
        if settings.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        
        # X-Frame-Options (クリックジャッキング対策)
        response.headers["X-Frame-Options"] = "DENY"
        
        # X-Content-Type-Options (MIMEタイプスニッフィング対策)
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # X-XSS-Protection (XSS攻撃対策)
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions Policy
        response.headers["Permissions-Policy"] = (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "magnetometer=(), "
            "gyroscope=(), "
            "fullscreen=(self), "
            "payment=(), "
            "usb=()"
        )
        
        # Cache Control for sensitive pages
        if "/api/auth" in str(request.url) or "/api/twitter" in str(request.url):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, proxy-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        
        return response
