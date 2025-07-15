from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    OPENAI_API_KEY: str = ""
    GITHUB_API_URL: str = "https://api.github.com/repos/{repo}/commits"
    TWITTER_CLIENT_ID: str = ""
    TWITTER_CLIENT_SECRET: str = ""
    TWITTER_ACCESS_TOKEN: str = ""
    TWITTER_ACCESS_TOKEN_SECRET: str = ""
    TWITTER_REDIRECT_URI: str = "http://127.0.0.1:8000/callback"

    class Config:
        env_file = ".env"

settings = Settings() 