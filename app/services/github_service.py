import requests
from fastapi import HTTPException
from app.config import settings

def fetch_latest_commit_message(repository: str) -> str:
    url = settings.GITHUB_API_URL.format(repo=repository)
    resp = requests.get(url)
    if resp.status_code != 200:
        error_detail = f"GitHub API エラー: {resp.status_code}"
        try:
            error_data = resp.json()
            if "message" in error_data:
                error_detail += f" - {error_data['message']}"
        except:
            pass
        raise HTTPException(status_code=404, detail=error_detail)
    data = resp.json()
    if not data:
        raise HTTPException(status_code=404, detail="コミット情報が見つかりません")
    commit_message = data[0]["commit"]["message"]
    return commit_message 