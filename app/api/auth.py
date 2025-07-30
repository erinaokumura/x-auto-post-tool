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
import json
import redis

from app.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])

# Redisクライアント（OAuth状態管理用）
oauth_redis = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=1, decode_responses=True)
OAUTH_STATE_PREFIX = "oauth_state:"
OAUTH_STATE_TTL = 600  # 10分

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
    try:
        # Redisの接続テスト
        print("Testing Redis connection...")
        try:
            oauth_redis.ping()
            print("Redis connection successful")
        except Exception as redis_error:
            print(f"Redis connection failed: {redis_error}")
            raise HTTPException(status_code=500, detail=f"Redis接続エラー: {str(redis_error)}")
        
        print("Getting OAuth2 handler...")
        handler = get_oauth2_handler()
        print(f"Handler created: {handler}")
        
        print("Getting authorization URL...")
        url = handler.get_authorization_url()
        print(f"Authorization URL: {url}")
        
        print("Getting state...")
        state = handler.state  # プロパティとして取得
        print(f"State: {state}")
        print(f"State type: {type(state)}")
        
        # stateが関数の場合は呼び出す
        if callable(state):
            print("State is callable, calling it...")
            state = state()
            print(f"State after calling: {state}")
        
        # URLからstateパラメータを抽出（これが実際にTwitterに送信される値）
        import urllib.parse
        parsed_url = urllib.parse.urlparse(url)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        actual_state = query_params.get('state', [None])[0]
        print(f"State from URL: {actual_state}")
        
        if actual_state and actual_state != state:
            print(f"State mismatch detected! Using URL state: {actual_state}")
            state = actual_state
        
        # URLからcode_challengeも抽出して確認
        code_challenge = query_params.get('code_challenge', [None])[0]
        print(f"Code challenge from URL: {code_challenge}")
        
        # handlerの全属性を確認
        print("Handler attributes:")
        for attr in dir(handler):
            if not attr.startswith('_'):
                try:
                    value = getattr(handler, attr)
                    if not callable(value):
                        print(f"  {attr}: {value}")
                except:
                    pass
        
        # プライベート属性も確認（code_verifierがここにある可能性）
        print("Handler private attributes:")
        for attr in dir(handler):
            if attr.startswith('_'):
                try:
                    value = getattr(handler, attr)
                    if not callable(value) and value:
                        print(f"  {attr}: {value}")
                except:
                    pass
        
        # code_verifierの候補を確認
        code_verifier = None
        for attr_name in ['code_verifier', '_code_verifier', 'challenge', '_challenge', 'verifier', '_verifier', '_code_challenge_verifier']:
            if hasattr(handler, attr_name):
                code_verifier = getattr(handler, attr_name)
                print(f"Found code_verifier as '{attr_name}': {code_verifier}")
                break
        
        # 内部のOAuth2Sessionオブジェクトからも確認
        if hasattr(handler, '_session') or hasattr(handler, 'session'):
            session_obj = getattr(handler, '_session', None) or getattr(handler, 'session', None)
            if session_obj:
                print("Checking OAuth2Session attributes:")
                for attr in dir(session_obj):
                    if not attr.startswith('__'):
                        try:
                            value = getattr(session_obj, attr)
                            if not callable(value) and value:
                                print(f"  session.{attr}: {value}")
                                if ('code' in attr.lower() and 'verifier' in attr.lower()) or attr == 'code_verifier':
                                    if code_verifier is None:
                                        code_verifier = value
                                        print(f"Using session.{attr} as code_verifier: {value}")
                        except:
                            pass
        
        # 最後の手段: OAuth2UserHandler内部のPKCE実装を確認
        if hasattr(handler, '_client'):
            client_obj = getattr(handler, '_client')
            if client_obj:
                print("Checking OAuth2UserHandler._client attributes:")
                for attr in dir(client_obj):
                    if not attr.startswith('__'):
                        try:
                            value = getattr(client_obj, attr)
                            if not callable(value) and value:
                                print(f"  _client.{attr}: {value}")
                                # code_verifierを特定
                                if attr == 'code_verifier' and code_verifier is None:
                                    code_verifier = value
                                    print(f"Found code_verifier in _client: {value}")
                        except:
                            pass
        
        if code_verifier is None:
            print("Warning: code_verifier not found, using empty string")
            code_verifier = ""
        else:
            print(f"Using code_verifier: {code_verifier}")
        
        # OAuth2ハンドラーの状態をRedisに保存
        oauth_data = {
            "client_id": handler.client_id,
            "client_secret": settings.TWITTER_CLIENT_SECRET,
            "redirect_uri": handler.redirect_uri,
            "scope": handler.scope,
            "code_verifier": code_verifier,
            "state": state
        }
        print(f"Saving OAuth data to Redis: {oauth_data}")
        
        oauth_redis.setex(f"{OAUTH_STATE_PREFIX}{state}", OAUTH_STATE_TTL, json.dumps(oauth_data))
        print("OAuth data saved successfully")
        
        return {
            "authorization_url": url,
            "state": state
        }
    except Exception as e:
        print(f"Error in twitter_login: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Twitter認証エラー: {str(e)}")

@router.post("/twitter/callback")
def twitter_callback(
    req: OAuthCallbackRequest,
    response: Response,
    session_service=Depends(get_session_service),
    oauth_service: OAuthService = Depends(get_oauth_service)
):
    """Twitter OAuth2.0 PKCE認証コールバック"""
    
    try:
        print("=== Twitter Callback Started ===")
        print(f"Received code: {req.code}")
        print(f"Received state: {req.state}")
        
        # Redisから認証状態を取得
        print(f"Looking for OAuth data with key: {OAUTH_STATE_PREFIX}{req.state}")
        oauth_data_json = oauth_redis.get(f"{OAUTH_STATE_PREFIX}{req.state}")
        print(f"Retrieved OAuth data: {oauth_data_json}")
        
        if not oauth_data_json:
            print("ERROR: OAuth data not found in Redis")
            raise HTTPException(status_code=400, detail="認証セッションが期限切れまたは見つかりません")
        
        oauth_data = json.loads(oauth_data_json)
        print(f"Parsed OAuth data: {oauth_data}")
        
        # OAuth2ハンドラーを再構築
        print("Reconstructing OAuth2 handler...")
        handler = tweepy.OAuth2UserHandler(
            client_id=oauth_data["client_id"],
            redirect_uri=oauth_data["redirect_uri"],
            scope=oauth_data["scope"],
            client_secret=oauth_data["client_secret"]
        )
        print(f"Handler reconstructed: {handler}")
        
        # code_verifierとstateを復元
        print("Restoring code_verifier and state...")
        print(f"Setting code_verifier to: {oauth_data['code_verifier']}")
        print(f"Setting state to: {oauth_data['state']}")
        
        # code_verifierが空の場合はエラー
        if not oauth_data["code_verifier"]:
            print("ERROR: code_verifier is empty!")
            raise HTTPException(status_code=400, detail="PKCE認証に必要なcode_verifierが見つかりません")
        
        # OAuth2UserHandlerの内部_clientにcode_verifierを設定
        if hasattr(handler, '_client'):
            handler._client.code_verifier = oauth_data["code_verifier"]
            print(f"Set handler._client.code_verifier: {oauth_data['code_verifier']}")
        
        handler.state = oauth_data["state"]
        
        print("Restored handler - CLIENT_ID:", oauth_data["client_id"])
        print("Restored handler - state:", oauth_data["state"])
        print("Restored handler - code_verifier:", oauth_data["code_verifier"])
        
        # トークンを取得
        print("Attempting to fetch token...")
        redirect_url = f"http://localhost:8000/callback?code={req.code}&state={req.state}"
        print(f"Using redirect URL: {redirect_url}")
        
        token_data = fetch_token(handler, redirect_url)
        print(f"Token fetched successfully: {token_data}")
        
        # Twitter APIクライアントを作成してユーザー情報を取得（OAuth 2.0用）
        print("Creating Twitter client and fetching user info...")
        client = tweepy.Client(bearer_token=token_data['access_token'])
        user_info = client.get_me(user_fields=['username', 'name', 'profile_image_url'], user_auth=False)
        
        if not user_info.data:
            print("ERROR: Failed to get user info")
            raise HTTPException(status_code=400, detail="ユーザー情報の取得に失敗しました")
        
        twitter_user = user_info.data
        print(f"User info retrieved: {twitter_user}")
        
        # ユーザーを作成または更新
        print("Creating/updating user...")
        user = oauth_service.create_or_update_user_from_oauth({
            'username': twitter_user.username,
            'name': twitter_user.name,
            'profile_image_url': twitter_user.profile_image_url,
            'id': twitter_user.id
        }, "twitter")
        print(f"User created/updated: {user}")
        
        # OAuthトークンを保存
        print("Saving OAuth token...")
        oauth_service.save_oauth_token(user.id, "twitter", token_data)
        print("OAuth token saved")
        
        # セッションを作成
        print("Creating session...")
        session_id = session_service.create_session(str(user.id))
        response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=True,
            secure=False,  # 本番はTrue
            samesite="lax",
            max_age=1800
        )
        print(f"Session created: {session_id}")
        
        # Redis から認証状態を削除
        print("Cleaning up OAuth data from Redis...")
        oauth_redis.delete(f"{OAUTH_STATE_PREFIX}{req.state}")
        print("OAuth data deleted")
        
        print("=== Twitter Callback Completed Successfully ===")
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
        print(f"=== Twitter Callback Error ===")
        print(f"Error in twitter_callback: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        
        # エラー時も認証状態をクリア
        print("Cleaning up OAuth data due to error...")
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