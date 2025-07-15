from app.config import settings
import tweepy
from fastapi import HTTPException

CLIENT_ID = settings.TWITTER_CLIENT_ID
CLIENT_SECRET = settings.TWITTER_CLIENT_SECRET
REDIRECT_URI = settings.TWITTER_REDIRECT_URI
SCOPES = ["tweet.write", "tweet.read", "users.read", "offline.access"]

def get_oauth2_handler():
    if not CLIENT_ID or not CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="Twitter Client ID/Secretが設定されていません")
    return tweepy.OAuth2UserHandler(
        client_id=CLIENT_ID,
        redirect_uri=REDIRECT_URI,
        scope=SCOPES,
        client_secret=CLIENT_SECRET
    )

def get_authorization_url():
    handler = get_oauth2_handler()
    url = handler.get_authorization_url()
    state = handler.state()
    return url, state, handler

def fetch_token(handler, redirect_response: str):
    token = handler.fetch_token(authorization_response=redirect_response)
    return token 