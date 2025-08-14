from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()
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

settings = Settings() 