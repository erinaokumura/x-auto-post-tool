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

# 環境変数ファイルの読み込み（環境に応じて分岐）
def load_environment_config():
    """
    環境変数ENVIRONMENTに基づいて適切な.envファイルを読み込む
    """
    # ENVIRONMENT環境変数を先に取得
    environment = os.getenv("ENVIRONMENT", "development")
    
    # Railwayの場合は環境変数が直接設定されているので.envファイル読み込みをスキップ
    if os.getenv("RAILWAY_ENVIRONMENT"):
        return environment
    
    # ローカル環境では.envファイルを読み込む
    detect_and_load_dotenv(".env")
    
    # 環境固有の.envファイルを読み込み
    env_file = f".env.{environment}"
    if detect_and_load_dotenv(env_file):
        print(f"環境固有ファイル {env_file} を読み込みました")
    
    return environment

# 環境設定の読み込み
current_environment = load_environment_config()

class Settings(BaseSettings):
    OPENAI_API_KEY: str = ""
    GITHUB_API_URL: str = "https://api.github.com/repos/{repo}/commits"
    GITHUB_TOKEN: str = ""  # GitHub認証トークン（レート制限緩和用）
    TWITTER_CLIENT_ID: str = ""
    TWITTER_CLIENT_SECRET: str = ""
    TWITTER_ACCESS_TOKEN: str = ""
    TWITTER_ACCESS_TOKEN_SECRET: str = ""
    TWITTER_REDIRECT_URI: str = ""  # 環境変数で設定
    REDIS_URL: str = ""  # Railway Redis URL (本番環境で使用)
    DATABASE_URL: str = ""
    ENCRYPTION_KEY: str = ""
    
    # CORS設定
    CORS_ORIGINS: str = "http://localhost:3000,https://*.vercel.app,https://x-auto-post-tool.vercel.app,https://x-auto-post-tool-development.up.railway.app"
    ENVIRONMENT: str = "development"  # development, production
    
    # 最適化設定
    ENABLE_CACHING: bool = True  # キャッシュ機能のON/OFF
    CACHE_GITHUB_TTL: int = 300  # GitHubキャッシュ有効期限（秒）
    CACHE_OPENAI_TTL: int = 86400  # OpenAIキャッシュ有効期限（秒）
    ENABLE_CIRCUIT_BREAKER: bool = True  # サーキットブレーカーのON/OFF
    GITHUB_CIRCUIT_FAILURE_THRESHOLD: int = 3  # GitHub API障害閾値
    OPENAI_CIRCUIT_FAILURE_THRESHOLD: int = 5  # OpenAI API障害閾値
    TWITTER_CIRCUIT_FAILURE_THRESHOLD: int = 3  # Twitter API障害閾値
    
    # パフォーマンス設定
    ASYNC_TIMEOUT: int = 30  # 非同期処理タイムアウト（秒）
    MAX_CONCURRENT_REQUESTS: int = 10  # 最大同時リクエスト数
    ENABLE_PERFORMANCE_LOGGING: bool = True  # パフォーマンスログのON/OFF

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        case_sensitive = False
    
    def get_redis_url(self) -> str:
        """
        Redis接続URLを取得（環境に応じて適切なRedisを使用）
        """
        if self.REDIS_URL:
            # Railway環境（開発・本番）でREDIS_URLが設定されている場合
            return self.REDIS_URL
        else:
            # フォールバック: ローカルRedis（開発環境のみ）
            if self.is_production():
                raise ValueError("本番環境ではREDIS_URLの設定が必須です")
            return "redis://localhost:6379"  # ローカル開発環境用のデフォルト
    
    def is_production(self) -> bool:
        """
        本番環境かどうかを判定
        """
        return self.ENVIRONMENT.lower() == "production"
    
    def get_cors_origins(self) -> list[str]:
        """
        CORS設定を環境に応じて取得
        """
        origins = [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
        # ワイルドカードパターンを展開
        expanded_origins = []
        for origin in origins:
            if "*.vercel.app" in origin:
                # 具体的なVercelドメインを追加
                expanded_origins.extend([
                    "https://x-auto-post-tool.vercel.app",
                    "https://x-auto-post-tool-git-master.vercel.app",
                    "https://x-auto-post-tool-git-main.vercel.app"
                ])
            else:
                expanded_origins.append(origin)
        return expanded_origins
    
    def get_twitter_redirect_uri(self) -> str:
        """
        環境に応じてTwitter OAuth リダイレクトURIを取得
        """
        if self.TWITTER_REDIRECT_URI:
            return self.TWITTER_REDIRECT_URI
        
        # 環境変数が設定されていない場合は環境に応じて自動決定
        if self.ENVIRONMENT == "production":
            return "https://x-auto-post-tool-development.up.railway.app/callback"
        elif self.ENVIRONMENT == "development":
            return "https://x-auto-post-tool-development.up.railway.app/callback"
        else:
            return "http://127.0.0.1:8000/callback"

settings = Settings() 