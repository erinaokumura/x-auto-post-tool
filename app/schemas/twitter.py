from pydantic import BaseModel, Field, field_validator
from typing import Any, Optional
import re

class PostTweetRequest(BaseModel):
    tweet_text: str = Field(
        ..., 
        min_length=1, 
        max_length=280, 
        description="ツイート内容（1-280文字）"
    )
    
    @field_validator('tweet_text')
    @classmethod
    def validate_tweet_text(cls, v):
        # 危険な文字列のチェック
        dangerous_patterns = [
            r'<script',
            r'javascript:',
            r'vbscript:',
            r'onload=',
            r'onerror=',
            r'onclick='
        ]
        
        v_lower = v.lower()
        for pattern in dangerous_patterns:
            if re.search(pattern, v_lower):
                raise ValueError('不正な文字列が含まれています')
        
        # 制御文字の除去（改行・タブは除く）
        v = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', v)
        
        return v.strip()

class PostTweetResponse(BaseModel):
    success: bool
    tweet_id: Optional[str] = None
    message: str

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
    repository: str = Field(
        ..., 
        min_length=1, 
        max_length=200, 
        description="GitHubリポジトリ名（owner/repo形式）"
    )
    language: str = Field(
        default='ja', 
        pattern=r'^(ja|en|es|fr|de|it|pt|ru|zh|ko)$',
        description="言語コード（ja, en, es, fr, de, it, pt, ru, zh, ko）"
    )
    
    @field_validator('repository')
    @classmethod
    def validate_repository(cls, v):
        # GitHubリポジトリ形式の検証
        if not re.match(r'^[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+$', v):
            raise ValueError('リポジトリ名は owner/repo 形式で入力してください')
        
        # 危険な文字のチェック
        dangerous_chars = ['<', '>', '"', "'", '&', ';', '|', '`', '$']
        if any(char in v for char in dangerous_chars):
            raise ValueError('不正な文字が含まれています')
            
        return v.strip()

class AutoPostTweetResponse(BaseModel):
    status: str
    tweet_text: str
    tweet_response: Any 