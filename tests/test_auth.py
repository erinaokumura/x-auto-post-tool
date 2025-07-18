import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app
from app.api import auth

class DummySessionService:
    sessions = set()

    @staticmethod
    def create_session(user_id):
        DummySessionService.sessions.add("dummy_session_id")
        return "dummy_session_id"

    @staticmethod
    def get_user_id(session_id):
        if session_id in DummySessionService.sessions:
            return "user_id_1"
        return None

    @staticmethod
    def delete_session(session_id):
        DummySessionService.sessions.discard(session_id)

def override_session_service():
    return DummySessionService

app.dependency_overrides[auth.get_session_service] = override_session_service

def test_login_logout_me():
    with TestClient(app) as client:
        res = client.post("/api/auth/login", json={"username": "test", "password": "password"})
        assert res.status_code == 200
        assert "session_id" in res.cookies
        # /meでユーザー取得
        res2 = client.get("/api/auth/me")
        assert res2.status_code == 200
        assert res2.json()["user_id"] == "user_id_1"
        # ログアウト
        res3 = client.post("/api/auth/logout")
        assert res3.status_code == 200
        # ログアウト後は/meで401
        res4 = client.get("/api/auth/me")
        assert res4.status_code == 401 