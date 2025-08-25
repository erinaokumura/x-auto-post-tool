from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings

# デバッグ: DATABASE_URLの確認
print(f"DATABASE_URL: {settings.DATABASE_URL}")
if not settings.DATABASE_URL:
    raise ValueError("DATABASE_URL環境変数が設定されていません")

engine = create_engine(settings.DATABASE_URL, echo=True, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
