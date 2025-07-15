from pydantic import BaseModel

class GenerateTweetRequest(BaseModel):
    repository: str 