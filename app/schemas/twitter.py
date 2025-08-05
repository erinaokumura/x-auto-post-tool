from pydantic import BaseModel
from typing import Any

class PostTweetRequest(BaseModel):
    tweet_text: str

class PostTweetResponse(BaseModel):
    status: str

class TwitterAuthRequest(BaseModel):
    pass

class TwitterAuthResponse(BaseModel):
    authorization_url: str
    state: str

class TwitterTokenRequest(BaseModel):
    redirect_response: str
    tweet_text: str

class TwitterTokenResponse(BaseModel):
    status: str
    tweet_response: Any

class AutoPostTweetRequest(BaseModel):
    repository: str
    redirect_response: str
    language: str = 'ja'

class AutoPostTweetResponse(BaseModel):
    status: str
    tweet_text: str
    tweet_response: Any 