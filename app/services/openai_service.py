import os
from fastapi import HTTPException
from openai import OpenAI
from app.config import settings

def get_openai_api_key():
    api_key = settings.OPENAI_API_KEY
    if not api_key:
        raise HTTPException(status_code=500, detail="OpenAI APIキーが設定されていません")
    return api_key

def generate_tweet_with_openai(commit_message: str, repository: str, language: str = 'ja') -> str:
    client = OpenAI(api_key=get_openai_api_key())
    if language == 'en':
        prompt = f"""
You are an indie developer who is good at sharing information on X (formerly Twitter).
Based on the following GitHub commit message, generate an engaging English tweet (within 140 characters, include at least one hashtag, in the style of Pieter Levels).

Repository: {repository}
Commit message: {commit_message}
"""
    else:
        prompt = f"""
あなたはX（旧Twitter）で情報発信が得意な個人開発者です。
以下のGitHubコミットメッセージをもとに、インプレッションが伸びるような日本語のツイート文を1つ考えてください。

リポジトリ: {repository}
コミットメッセージ: {commit_message}

#ルール
- 140文字以内
- ハッシュタグを1つ以上含める
- Pieter Levels風の熱量や人間味を意識
"""
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
            temperature=0.8
        )
        content = response.choices[0].message.content if response.choices[0].message else None
        if content is None:
            raise HTTPException(status_code=500, detail="OpenAI APIからツイート案の生成に失敗しました")
        tweet = content.strip()
        return tweet
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI APIエラー: {str(e)}") 