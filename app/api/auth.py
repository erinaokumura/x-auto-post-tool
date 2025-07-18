from fastapi import APIRouter, Request, Response, Depends, HTTPException, status, Cookie
from app.services.session_service import SessionService
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["auth"])

# 仮のユーザー認証（本番はDBやOAuthと連携）
def fake_authenticate(username: str, password: str) -> str:
    if username == "test" and password == "password":
        return "user_id_1"
    raise HTTPException(status_code=401, detail="認証失敗")

class LoginRequest(BaseModel):
    username: str
    password: str

def get_session_service():
    return SessionService

@router.post("/login")
def login(response: Response, req: LoginRequest, session_service=Depends(get_session_service)):
    user_id = fake_authenticate(req.username, req.password)
    session_id = session_service.create_session(user_id)
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        secure=False,  # 本番はTrue
        samesite="lax",
        max_age=1800
    )
    return {"message": "ログイン成功"}

@router.post("/logout")
def logout(response: Response, session_id: str = Cookie(None), session_service=Depends(get_session_service)):
    if session_id:
        session_service.delete_session(session_id)
        response.delete_cookie("session_id")
    return {"message": "ログアウトしました"}

# Dependsでセッションからユーザー取得

def get_current_user(session_id: str = Cookie(None), session_service=Depends(get_session_service)):
    if not session_id:
        raise HTTPException(status_code=401, detail="未認証")
    user_id = session_service.get_user_id(session_id)
    if not user_id:
        raise HTTPException(status_code=401, detail="セッション無効")
    return user_id

@router.get("/me")
def get_me(user_id: str = Depends(get_current_user)):
    return {"user_id": user_id} 