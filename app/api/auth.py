from fastapi import APIRouter, Request, Response, Depends, HTTPException, status, Cookie, Query
from app.services.session_service import SessionService
from app.services.oauth_service import OAuthService
from app.auth.twitter_oauth import get_oauth2_handler, fetch_token
from app.db import get_db
from app.models import User
from app.middleware.rate_limiter import user_limiter, limiter
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session
from typing import Optional
import tweepy
import json
import redis
import urllib.parse

from app.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])

# Redisクライアント（OAuth状態管理用）
# OAuth用Redis接続（本番環境対応）
def get_oauth_redis():
    redis_url = settings.get_redis_url()
    return redis.from_url(redis_url, db=1, decode_responses=True)

oauth_redis = get_oauth_redis()
OAUTH_STATE_PREFIX = "oauth_state:"
OAUTH_STATE_TTL = 600  # 10分

class LoginRequest(BaseModel):
    username: str = Field(
        ..., 
        min_length=1, 
        max_length=50, 
        pattern=r'^[a-zA-Z0-9_.-]+$',
        description="ユーザー名（英数字、アンダースコア、ドット、ハイフンのみ）"
    )
    password: str = Field(
        ..., 
        min_length=1, 
        max_length=100,
        description="パスワード"
    )

class OAuthCallbackRequest(BaseModel):
    code: str = Field(
        ..., 
        min_length=1, 
        max_length=500,
        description="OAuth認証コード"
    )
    state: str = Field(
        ..., 
        min_length=1, 
        max_length=200,
        description="OAuth状態パラメータ"
    )
    
    @field_validator('code', 'state')
    @classmethod
    def validate_oauth_params(cls, v):
        # OAuth パラメータのセキュリティチェック
        dangerous_chars = ['<', '>', '"', "'", ';', '|', '&']
        if any(char in v for char in dangerous_chars):
            raise ValueError('不正な文字が含まれています')
        return v.strip()

def get_session_service():
    return SessionService

def get_oauth_service(db: Session = Depends(get_db)):
    return OAuthService(db)

@router.post("/login")
@limiter.limit("10/minute")  # ログイン試行の制限
def login(request: Request, response: Response, req: LoginRequest, session_service=Depends(get_session_service)):
    user_id = fake_authenticate(req.username, req.password)
    session_id = session_service.create_session(user_id)
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        secure=settings.ENVIRONMENT == "production",  # 本番環境ではTrue
        samesite="lax",
        max_age=1800
    )
    return {"message": "ログイン成功"}

@router.post("/logout")
def logout(
    response: Response, 
    session_id: str = Cookie(None), 
    session_service=Depends(get_session_service),
    db: Session = Depends(get_db)
):
    if session_id:
        user_id = session_service.get_user_id(session_id)
        if user_id:
            # OAuthトークンも削除
            oauth_service = OAuthService(db)
            oauth_service.delete_oauth_token(int(user_id), "twitter")
        
        session_service.delete_session(session_id)
        response.delete_cookie("session_id")
    return {"message": "ログアウトしました"}

@router.get("/twitter/login")
@limiter.limit("20/minute")  # OAuth開始の制限
def twitter_login(request: Request):
    """Twitter OAuth2.0 PKCE認証開始"""
    try:
        # Redisの接続確認
        oauth_redis.ping()
        
        handler = get_oauth2_handler()
        url = handler.get_authorization_url()
        
        # stateを取得
        state = handler.state
        if callable(state):
            state = state()
        
        # URLからstateパラメータを抽出（実際にTwitterに送信される値）
        parsed_url = urllib.parse.urlparse(url)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        actual_state = query_params.get('state', [None])[0]
        
        if actual_state and actual_state != state:
            state = actual_state
        
        # code_verifierを取得
        code_verifier = None
        for attr_name in ['code_verifier', '_code_verifier']:
            if hasattr(handler, attr_name):
                code_verifier = getattr(handler, attr_name)
                break
        
        # OAuth2UserHandler内部の_clientからも確認
        if code_verifier is None and hasattr(handler, '_client'):
            client_obj = getattr(handler, '_client')
            if client_obj and hasattr(client_obj, 'code_verifier'):
                code_verifier = client_obj.code_verifier
        
        if code_verifier is None:
            code_verifier = ""
        
        # OAuth2ハンドラーの状態をRedisに保存
        oauth_data = {
            "client_id": handler.client_id,
            "client_secret": settings.TWITTER_CLIENT_SECRET,
            "redirect_uri": handler.redirect_uri,
            "scope": handler.scope,
            "code_verifier": code_verifier,
            "state": state
        }
        
        oauth_redis.setex(f"{OAUTH_STATE_PREFIX}{state}", OAUTH_STATE_TTL, json.dumps(oauth_data))
        
        return {
            "authorization_url": url,
            "state": state
        }
    except Exception as redis_error:
        if "Redis" in str(type(redis_error).__name__):
            raise HTTPException(status_code=500, detail=f"Redis接続エラー: {str(redis_error)}")
        raise HTTPException(status_code=500, detail=f"Twitter認証エラー: {str(redis_error)}")

@router.post("/twitter/callback")
@limiter.limit("30/minute")  # OAuth コールバックの制限
def twitter_callback(
    request: Request,
    req: OAuthCallbackRequest,
    response: Response,
    session_service=Depends(get_session_service),
    oauth_service: OAuthService = Depends(get_oauth_service)
):
    """Twitter OAuth2.0 PKCE認証コールバック"""
    
    try:
        # Redisから認証状態を取得
        oauth_data_json = oauth_redis.get(f"{OAUTH_STATE_PREFIX}{req.state}")
        
        if not oauth_data_json:
            raise HTTPException(
                status_code=400, 
                detail="認証セッションが期限切れまたは見つかりません。既に処理済みの可能性があります。"
            )
        
        oauth_data = json.loads(oauth_data_json)
        
        # OAuth2ハンドラーを再構築
        handler = tweepy.OAuth2UserHandler(
            client_id=oauth_data["client_id"],
            redirect_uri=oauth_data["redirect_uri"],
            scope=oauth_data["scope"],
            client_secret=oauth_data["client_secret"]
        )
        
        # code_verifierが空の場合はエラー
        if not oauth_data["code_verifier"]:
            raise HTTPException(status_code=400, detail="PKCE認証に必要なcode_verifierが見つかりません")
        
        # OAuth2UserHandlerの内部_clientにcode_verifierを設定
        if hasattr(handler, '_client'):
            handler._client.code_verifier = oauth_data["code_verifier"]
        
        handler.state = oauth_data["state"]
        
        # トークンを取得
        redirect_url = f"{settings.TWITTER_REDIRECT_URI}?code={req.code}&state={req.state}"
        token_data = fetch_token(handler, redirect_url)
        
        # Twitter APIクライアントを作成してユーザー情報を取得
        client = tweepy.Client(bearer_token=token_data['access_token'])
        user_info = client.get_me(user_fields=['username', 'name', 'profile_image_url'], user_auth=False)
        
        if not user_info.data:
            raise HTTPException(status_code=400, detail="ユーザー情報の取得に失敗しました")
        
        twitter_user = user_info.data
        
        # ユーザーを作成または更新
        user = oauth_service.create_or_update_user_from_oauth({
            'username': twitter_user.username,
            'name': twitter_user.name,
            'profile_image_url': twitter_user.profile_image_url,
            'id': twitter_user.id
        }, "twitter")
        
        # OAuthトークンを保存
        oauth_service.save_oauth_token(user.id, "twitter", token_data)
        
        # セッションを作成
        session_id = session_service.create_session(str(user.id))
        response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=True,
            secure=settings.ENVIRONMENT == "production",  # 本番環境ではTrue
            samesite="none" if settings.ENVIRONMENT in ("production", "development") else "lax",  # クロスオリジン対応
            max_age=1800
        )

        # Redis から認証状態を削除
        oauth_redis.delete(f"{OAUTH_STATE_PREFIX}{req.state}")
        
        return {
            "message": "Twitter認証成功",
            "user": {
                "id": user.id,
                "username": user.username,
                "display_name": user.display_name,
                "avatar_url": user.avatar_url
            }
        }
        
    except HTTPException as http_exc:
        # HTTPExceptionは再発生させる
        raise http_exc
    except Exception as e:
        # 予期しないエラー時のみ認証状態をクリア
        if oauth_redis.exists(f"{OAUTH_STATE_PREFIX}{req.state}"):
            oauth_redis.delete(f"{OAUTH_STATE_PREFIX}{req.state}")
        raise HTTPException(status_code=400, detail=f"認証処理エラー: {str(e)}")

# Dependsでセッションからユーザー取得
def get_current_user(
    session_id: str = Cookie(None),
    session_service=Depends(get_session_service),
    db: Session = Depends(get_db)
) -> User:
    if not session_id:
        raise HTTPException(status_code=401, detail="未認証")
    
    user_id = session_service.get_user_id(session_id)
    if not user_id:
        raise HTTPException(status_code=401, detail="セッション無効")
    
    # データベースからユーザー情報を取得
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=401, detail="ユーザーが見つかりません")
    
    return user

@router.get("/me")
def get_me(user: User = Depends(get_current_user)):
    return {
        "id": user.id,
        "username": user.username,
        "display_name": user.display_name,
        "avatar_url": user.avatar_url,
        "email": user.email,
        "last_login_at": user.last_login_at,
        "login_count": user.login_count
    }

@router.get("/twitter/status")
def twitter_auth_status(user: User = Depends(get_current_user), oauth_service: OAuthService = Depends(get_oauth_service)):
    """Twitter認証状態を確認"""
    oauth_token = oauth_service.get_valid_token(user.id, "twitter")
    
    return {
        "is_authenticated": oauth_token is not None,
        "expires_at": oauth_token.expires_at if oauth_token else None,
        "scope": oauth_token.scope if oauth_token else None
    }

# 仮のユーザー認証（本番はDBやOAuthと連携）
def fake_authenticate(username: str, password: str) -> str:
    if username == "test" and password == "password":
        return "user_id_1"
    raise HTTPException(status_code=401, detail="認証失敗") 