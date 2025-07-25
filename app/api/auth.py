from fastapi import APIRouter, Request, Response, Depends, HTTPException, status, Cookie, Query
from app.services.session_service import SessionService
from app.services.oauth_service import OAuthService
from app.auth.twitter_oauth import get_oauth2_handler, fetch_token
from app.db import get_db
from app.models import User
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional
import tweepy

from app.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])

# グローバル変数でOAuth2ハンドラーを保持（セッション間で共有）
oauth2_handler = None

class LoginRequest(BaseModel):
    username: str
    password: str

class OAuthCallbackRequest(BaseModel):
    code: str
    state: str

def get_session_service():
    return SessionService

def get_oauth_service(db: Session = Depends(get_db)):
    return OAuthService(db)

@router.post("/login")
def login(response: Response, req: LoginRequest, session_service=Depends(get_session_service)):
    user_id = fake_authenticate(req.username, req.password)
    session_id = session_service.create_session(user_id)
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        secure=False,  # 本番はTrue
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
def twitter_login():
    """Twitter OAuth2.0 PKCE認証開始"""
    global oauth2_handler
    try:
        handler = get_oauth2_handler()
        url = handler.get_authorization_url()
        state = handler.state  # プロパティとして取得
        oauth2_handler = handler  # グローバル変数に保存
        return {
            "authorization_url": url,
            "state": state
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Twitter認証エラー: {str(e)}")

@router.post("/twitter/callback")
def twitter_callback(
    req: OAuthCallbackRequest,
    response: Response,
    session_service=Depends(get_session_service),
    oauth_service: OAuthService = Depends(get_oauth_service)
):
    """Twitter OAuth2.0 PKCE認証コールバック"""
    global oauth2_handler
    
    if not oauth2_handler:
        raise HTTPException(status_code=400, detail="認証セッションが見つかりません")
    
    try:
        print("CLIENT_ID:", settings.TWITTER_CLIENT_ID)
        print("CLIENT_SECRET:", settings.TWITTER_CLIENT_SECRET)
        print("handler.client_id:", oauth2_handler.client_id)
        print("handler.client_secret:", getattr(oauth2_handler, 'client_secret', None))
        print("handler auth:", getattr(oauth2_handler, 'auth', None))
        print("state:", oauth2_handler.state)
        
        # トークンを取得
        token_data = fetch_token(oauth2_handler, f"http://localhost:8000/auth/twitter/callback?code={req.code}&state={req.state}")
        
        # Twitter APIクライアントを作成してユーザー情報を取得（OAuth 2.0用）
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
            secure=False,  # 本番はTrue
            samesite="lax",
            max_age=1800
        )
        
        # グローバル変数をクリア
        oauth2_handler = None
        
        return {
            "message": "Twitter認証成功",
            "user": {
                "id": user.id,
                "username": user.username,
                "display_name": user.display_name,
                "avatar_url": user.avatar_url
            }
        }
        
    except Exception as e:
        oauth2_handler = None  # エラー時もクリア
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