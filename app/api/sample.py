from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import User  # 既存のSQLAlchemyモデル

router = APIRouter()

@router.post("/sample/users")
def create_user(email: str, db: Session = Depends(get_db)):
    user = User(email=email)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.get("/sample/users")
def list_users(db: Session = Depends(get_db)):
    return db.query(User).all()