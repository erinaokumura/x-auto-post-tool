from pydantic import BaseModel
 
class GenerateTweetResponse(BaseModel):
    tweet_text: str
    commit_message: str
    repository: str 