from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

def detect_and_load_dotenv(file_path: str) -> bool:
    """
    複数のエンコーディングを試して.envファイルを読み込む
    """
    if not os.path.exists(file_path):
        return False
    
    # 自動エンコーディング検出を試行
    try:
        import chardet
        with open(file_path, 'rb') as f:
            raw_data = f.read()
        encoding_info = chardet.detect(raw_data)
        detected_encoding = encoding_info.get('encoding', 'utf-8')
        
        try:
            load_dotenv(file_path, encoding=detected_encoding)
            print(f"環境変数ファイルを {detected_encoding} エンコーディング（自動検出）で読み込みました")
            return True
        except (UnicodeDecodeError, UnicodeError):
            pass
    except ImportError:
        # chardetがない場合は手動でエンコーディングを試行
        pass
    
    # 手動でエンコーディングを試行
    encodings_to_try = ['utf-8', 'utf-8-sig', 'cp932', 'shift_jis', 'iso-2022-jp', 'latin1']
    
    for encoding in encodings_to_try:
        try:
            load_dotenv(file_path, encoding=encoding)
            print(f"環境変数ファイルを {encoding} エンコーディングで読み込みました")
            return True
        except (UnicodeDecodeError, UnicodeError):
            continue
    
    print(f"Warning: {file_path} を読み込めませんでした。サポートされているエンコーディング: {encodings_to_try}")
    print("環境変数を手動で設定するか、ファイルをUTF-8で保存し直してください。")
    return False

# 環境変数ファイルの読み込み
detect_and_load_dotenv(".env")
class Settings(BaseSettings):
    OPENAI_API_KEY: str = ""
    GITHUB_API_URL: str = "https://api.github.com/repos/{repo}/commits"
    TWITTER_CLIENT_ID: str = ""
    TWITTER_CLIENT_SECRET: str = ""
    TWITTER_ACCESS_TOKEN: str = ""
    TWITTER_ACCESS_TOKEN_SECRET: str = ""
    TWITTER_REDIRECT_URI: str = "http://127.0.0.1:8000/callback"
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    DATABASE_URL: str = ""
    ENCRYPTION_KEY: str = ""
    
    # CORS設定
    CORS_ORIGINS: str = "http://localhost:3000,https://*.vercel.app"
    ENVIRONMENT: str = "development"  # development, production

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        # エンコーディングエラーを無視する設定
        env_ignore_empty = True

settings = Settings() 