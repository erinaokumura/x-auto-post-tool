from fastapi import APIRouter, Depends
from app.schemas.github import GenerateTweetRequest
from app.schemas.openai import GenerateTweetResponse

def get_fetch_latest_commit_message():
    from app.services.github_service import fetch_latest_commit_message
    return fetch_latest_commit_message

def get_generate_tweet_with_openai():
    from app.services.openai_service import generate_tweet_with_openai
    return generate_tweet_with_openai

router = APIRouter()

@router.post("/generate_tweet", response_model=GenerateTweetResponse)
def generate_tweet(
    req: GenerateTweetRequest,
    fetch_latest_commit_message=Depends(get_fetch_latest_commit_message),
    generate_tweet_with_openai=Depends(get_generate_tweet_with_openai)
):
    try:
        # 安全にlanguageにアクセス
        language = getattr(req, 'language', 'ja')
        commit_message = fetch_latest_commit_message(req.repository)
        tweet_draft = generate_tweet_with_openai(commit_message, req.repository, language)
        response = GenerateTweetResponse(
            tweet_draft=tweet_draft,
            commit_message=commit_message
        )
        return response
    except Exception as e:
        import traceback
        raise 