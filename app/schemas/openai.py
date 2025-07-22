from pydantic import BaseModel
 
class GenerateTweetResponse(BaseModel):
    commit_message: str
    tweet_draft: str 