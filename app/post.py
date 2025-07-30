import requests
import os

def post_tweet(access_token: str, tweet_text: str):
    url = "https://api.twitter.com/2/tweets"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    json_data = {
        "text": tweet_text
    }
    response = requests.post(url, headers=headers, json=json_data)
    return response