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
        print(f"=== Generate Tweet API Called ===")
        print(f"Repository: {req.repository}")
        print(f"Language: {req.language}")
        
        commit_message = fetch_latest_commit_message(req.repository)
        print(f"Commit message: {commit_message}")
        
        tweet_draft = generate_tweet_with_openai(commit_message, req.repository, req.language)
        print(f"Generated tweet: {tweet_draft}")
        
        response = GenerateTweetResponse(
            tweet_text=tweet_draft,
            commit_message=commit_message,
            repository=req.repository
        )
        print(f"Response: {response}")
        
        return response
    except Exception as e:
        print(f"ERROR in generate_tweet: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        raise 