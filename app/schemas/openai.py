from pydantic import BaseModel
 
class GenerateTweetResponse(BaseModel):
    tweet_draft: str
    commit_message: str 
    repository: str 
