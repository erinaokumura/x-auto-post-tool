import uuid
import redis
from typing import Optional
from fastapi import Request, HTTPException
from app.config import settings

# Redisクライアント初期化
r = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0, decode_responses=True)

SESSION_PREFIX = "session:"
SESSION_TTL = 1800  # 30分

class SessionService:
    @staticmethod
    def create_session(user_id: str) -> str:
        session_id = str(uuid.uuid4())
        r.setex(f"{SESSION_PREFIX}{session_id}", SESSION_TTL, user_id)
        return session_id

    @staticmethod
    def get_user_id(session_id: str) -> Optional[str]:
        user_id = r.get(f"{SESSION_PREFIX}{session_id}")
        if user_id is None:
            return None
        if isinstance(user_id, bytes):
            return user_id.decode("utf-8")
        return str(user_id)

    @staticmethod
    def delete_session(session_id: str):
        r.delete(f"{SESSION_PREFIX}{session_id}") 