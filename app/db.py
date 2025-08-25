from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# 直接環境変数を確認（config.pyを読み込む前）
print("=== db.py 環境変数直接確認 ===")
database_url_direct = os.getenv("DATABASE_URL")
print(f"DATABASE_URL (直接): {database_url_direct}")
print(f"ENVIRONMENT: {os.getenv('ENVIRONMENT')}")
print(f"RAILWAY_ENVIRONMENT: {os.getenv('RAILWAY_ENVIRONMENT')}")
print("利用可能な環境変数:")
for key, value in os.environ.items():
    if any(keyword in key.upper() for keyword in ['DATABASE', 'DB', 'POSTGRES', 'RAILWAY']):
        print(f"  {key}: {value}")
print("================================")

from app.config import settings

# デバッグ: DATABASE_URLの確認
print(f"DATABASE_URL (settings): {settings.DATABASE_URL}")
if not settings.DATABASE_URL and not database_url_direct:
    raise ValueError("DATABASE_URL環境変数が設定されていません")

# 直接環境変数があればそれを使用
database_url = settings.DATABASE_URL or database_url_direct
if not database_url:
    raise ValueError("DATABASE_URL環境変数が設定されていません")

engine = create_engine(database_url, echo=True, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
