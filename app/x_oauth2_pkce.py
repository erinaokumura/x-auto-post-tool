import tweepy
import os
from post import post_tweet

CLIENT_ID = os.getenv("TWITTER_CLIENT_ID")
CLIENT_SECRET = os.getenv("TWITTER_CLIENT_SECRET")
REDIRECT_URI = os.getenv("TWITTER_REDIRECT_URI", "http://127.0.0.1:8000/callback")
SCOPES = ["tweet.write", "tweet.read", "users.read", "offline.access"]

if not CLIENT_ID or not CLIENT_SECRET:
    raise Exception("Twitter Client ID/Secretが環境変数に設定されていません")

def main():
    # 1. 認可URL生成
    auth = tweepy.OAuth2UserHandler(
        client_id=CLIENT_ID,
        redirect_uri=REDIRECT_URI,
        scope=SCOPES,
        client_secret=CLIENT_SECRET
    )
    print("[Step1] 以下のURLにアクセスして認可してください:")
    print(auth.get_authorization_url())

    # 2. 認可後、リダイレクト先URL全体を取得
    redirect_response = input("[Step2] ブラウザのリダイレクト先URL全体を貼り付けてください: ")

    # 3. アクセストークン取得
    token = auth.fetch_token(authorization_response=redirect_response)
    print("[Step3] アクセストークン取得:")
    print(token)

    # 4. ツイート投稿
    tweet_text = input("[Step4] 投稿したいツイート文を入力してください: ")
    post_tweet(token["access_token"], tweet_text)

if __name__ == "__main__":
    main() 