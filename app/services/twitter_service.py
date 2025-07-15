from app.config import settings
import tweepy
import requests
from fastapi import HTTPException

def get_tweepy_client():
    consumer_key = settings.TWITTER_CLIENT_ID
    consumer_secret = settings.TWITTER_CLIENT_SECRET
    access_token = settings.TWITTER_ACCESS_TOKEN
    access_token_secret = settings.TWITTER_ACCESS_TOKEN_SECRET
    if not all([consumer_key, consumer_secret, access_token, access_token_secret]):
        raise HTTPException(status_code=500, detail="Twitter API認証情報が不足しています")
    auth = tweepy.OAuth1UserHandler(
        consumer_key, consumer_secret, access_token, access_token_secret
    )
    api = tweepy.API(auth)
    return api

def post_tweet_with_tweepy(tweet: str):
    try:
        api = get_tweepy_client()
        api.update_status(status=tweet)
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Twitter APIエラー: {str(e)}")

def post_tweet_v2(access_token: str, tweet_text: str):
    url = "https://api.twitter.com/2/tweets"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    json_data = {
        "text": tweet_text
    }
    response = requests.post(url, headers=headers, json=json_data)
    if response.status_code != 201:
        raise HTTPException(status_code=response.status_code, detail=f"Twitter API v2エラー: {response.text}")
    return response.json() 