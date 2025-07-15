from fastapi import FastAPI
from app.api import twitter, openai

app = FastAPI()

# APIルーター登録
app.include_router(twitter.router, prefix="/api")
app.include_router(openai.router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI!"} 