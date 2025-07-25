from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models import User, OAuthToken
from app.services.token_service import TokenService
from app.auth.twitter_oauth import get_oauth2_handler, fetch_token
import tweepy
from fastapi import HTTPException

class OAuthService:
    def __init__(self, db: Session):
        self.db = db
        self.token_service = TokenService()
    
    def save_oauth_token(self, user_id: int, provider: str, token_data: Dict[str, Any]) -> OAuthToken:
        """OAuthトークンを暗号化してデータベースに保存"""
        # 既存のトークンを無効化
        self.db.query(OAuthToken).filter(
            OAuthToken.user_id == user_id,
            OAuthToken.provider == provider,
            OAuthToken.is_active == True
        ).update({"is_active": False})
        
        # 有効期限の計算
        expires_at = None
        if 'expires_in' in token_data:
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=token_data['expires_in'])
        
        # トークンを暗号化
        encrypted_access_token = self.token_service.encrypt_token(token_data.get('access_token', ''))
        encrypted_refresh_token = self.token_service.encrypt_token(token_data.get('refresh_token', ''))
        
        # 新しいトークンレコードを作成
        oauth_token = OAuthToken(
            user_id=user_id,
            provider=provider,
            access_token=encrypted_access_token,
            refresh_token=encrypted_refresh_token,
            token_type=token_data.get('token_type', 'Bearer'),
            expires_at=expires_at,
            scope=token_data.get('scope', ''),
            is_active=True
        )
        
        self.db.add(oauth_token)
        self.db.commit()
        self.db.refresh(oauth_token)
        
        return oauth_token
    
    def get_valid_token(self, user_id: int, provider: str) -> Optional[OAuthToken]:
        """有効なOAuthトークンを取得（必要に応じてリフレッシュ）"""
        oauth_token = self.db.query(OAuthToken).filter(
            OAuthToken.user_id == user_id,
            OAuthToken.provider == provider,
            OAuthToken.is_active == True
        ).first()
        
        if not oauth_token:
            return None
        
        # トークンが期限切れの場合、リフレッシュを試行
        if self.token_service.is_token_expired(oauth_token.expires_at):
            if oauth_token.refresh_token:
                refreshed_token = self.refresh_oauth_token(oauth_token)
                if refreshed_token:
                    return refreshed_token
            # リフレッシュできない場合は無効化
            oauth_token.is_active = False
            self.db.commit()
            return None
        
        return oauth_token
    
    def refresh_oauth_token(self, oauth_token: OAuthToken) -> Optional[OAuthToken]:
        """OAuthトークンをリフレッシュ"""
        try:
            # リフレッシュトークンを復号化
            refresh_token = self.token_service.decrypt_token(oauth_token.refresh_token)
            if not refresh_token:
                return None
            
            # Twitter OAuth2.0 リフレッシュ
            handler = get_oauth2_handler()
            new_token_data = handler.refresh_token(refresh_token)
            
            # 新しいトークンを保存
            return self.save_oauth_token(oauth_token.user_id, oauth_token.provider, new_token_data)
            
        except Exception as e:
            print(f"Token refresh failed: {e}")
            return None
    
    def get_decrypted_access_token(self, user_id: int, provider: str) -> Optional[str]:
        """復号化されたアクセストークンを取得"""
        oauth_token = self.get_valid_token(user_id, provider)
        if not oauth_token:
            return None
        
        return self.token_service.decrypt_token(oauth_token.access_token)
    
    def delete_oauth_token(self, user_id: int, provider: str):
        """OAuthトークンを削除（ログアウト時など）"""
        self.db.query(OAuthToken).filter(
            OAuthToken.user_id == user_id,
            OAuthToken.provider == provider
        ).update({"is_active": False})
        self.db.commit()
    
    def create_or_update_user_from_oauth(self, oauth_user_info: Dict[str, Any], provider: str) -> User:
        """OAuth認証情報からユーザーを作成または更新"""
        # Twitterの場合はusernameをemailとして使用（Twitterはemailを提供しない）
        email = oauth_user_info.get('email') or f"{oauth_user_info.get('username', 'unknown')}@{provider}.com"
        username = oauth_user_info.get('username', '')
        
        # 既存ユーザーを検索
        user = self.db.query(User).filter(User.email == email).first()
        
        if user:
            # 既存ユーザーの情報を更新
            user.username = username
            user.display_name = oauth_user_info.get('name', '')
            user.avatar_url = oauth_user_info.get('profile_image_url', '')
            user.last_login_at = datetime.now(timezone.utc)
            user.login_count += 1
        else:
            # 新規ユーザーを作成
            user = User(
                email=email,
                username=username,
                display_name=oauth_user_info.get('name', ''),
                avatar_url=oauth_user_info.get('profile_image_url', ''),
                last_login_at=datetime.now(timezone.utc),
                login_count=1
            )
            self.db.add(user)
        
        self.db.commit()
        self.db.refresh(user)
        return user 