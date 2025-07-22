from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, index=True)
    display_name = Column(String(100))
    avatar_url = Column(Text)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_login_at = Column(DateTime(timezone=True))
    login_count = Column(Integer, default=0)
    oauth_tokens = relationship('OAuthToken', back_populates='user', cascade="all, delete-orphan")
    post_history = relationship('PostHistory', back_populates='user', cascade="all, delete-orphan")
    user_settings = relationship('UserSetting', back_populates='user', cascade="all, delete-orphan")

class OAuthToken(Base):
    __tablename__ = 'oauth_tokens'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    provider = Column(String(50), nullable=False)
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text)
    token_type = Column(String(50), default='Bearer')
    expires_at = Column(DateTime(timezone=True))
    scope = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    user = relationship('User', back_populates='oauth_tokens')

class PostHistory(Base):
    __tablename__ = 'post_history'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    repository = Column(String(255), nullable=False)
    commit_message = Column(Text, nullable=False)
    tweet_text = Column(Text, nullable=False)
    tweet_id = Column(String(255))
    language = Column(String(10), default='ja')
    status = Column(String(50), default='pending', nullable=False)
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    posted_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    user = relationship('User', back_populates='post_history')

class UserSetting(Base):
    __tablename__ = 'user_settings'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    setting_key = Column(String(100), nullable=False)
    setting_value = Column(Text)
    setting_type = Column(String(50), default='string')
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    user = relationship('User', back_populates='user_settings') 