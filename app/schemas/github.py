from pydantic import BaseModel
 
class GenerateTweetRequest(BaseModel):
    repository: str
    language: str = 'ja'  # デフォルトは日本語 