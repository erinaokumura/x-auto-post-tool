import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from app.config import settings
from typing import Optional

class TokenService:
    def __init__(self):
        # 環境変数から暗号化キーを取得、なければ生成
        self.secret_key = os.getenv('ENCRYPTION_KEY')
        if not self.secret_key:
            # 開発環境用のデフォルトキー（本番では必ず環境変数で設定）
            self.secret_key = "dev-secret-key-for-encryption-32chars!!"
        
        # キーを32バイトに調整
        if len(self.secret_key) < 32:
            self.secret_key = self.secret_key.ljust(32, '0')
        elif len(self.secret_key) > 32:
            self.secret_key = self.secret_key[:32]
        
        # Fernetキーを生成
        salt = b'x_auto_post_tool_salt'  # 固定のソルト（本番ではランダム化を検討）
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.secret_key.encode()))
        self.fernet = Fernet(key)
    
    def encrypt_token(self, token: str) -> str:
        """トークンを暗号化"""
        if not token:
            return ""
        encrypted = self.fernet.encrypt(token.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt_token(self, encrypted_token: str) -> Optional[str]:
        """トークンを復号化"""
        if not encrypted_token:
            return None
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_token.encode())
            decrypted = self.fernet.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception as e:
            # 復号化に失敗した場合（古い形式のトークンなど）
            print(f"Token decryption failed: {e}")
            return None
    
    def is_token_expired(self, expires_at) -> bool:
        """トークンの有効期限をチェック"""
        if not expires_at:
            return True
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        return now >= expires_at 