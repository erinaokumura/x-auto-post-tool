from fastapi import FastAPI
from app.api import twitter, openai, sample
from app.api import auth

app = FastAPI()

# APIルーター登録
app.include_router(twitter.router, prefix="/api")
app.include_router(openai.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(sample.router)

@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI!"}

@app.get("/health")
def health_check():
    return {"status": "ok"} 

import redis
r = redis.Redis(host='localhost', port=6379, db=0)

@app.post('/redis/set')
def set_value(key: str, value: str):
    r.set(key, value)
    return {"result": "ok"}

@app.get('/redis/get')
def get_value(key: str):
    value = r.get(key)
    return {"value": value.decode() if value else None}