# Redisセットアップ手順

## 1. Redisの用意
### ローカルでのインストール方法
- Windowsの場合: [Memurai](https://www.memurai.com/)や[公式Redis for Windows](https://github.com/microsoftarchive/redis/releases)を利用
- Macの場合: Homebrewで `brew install redis`
- Linuxの場合: `sudo apt install redis-server` など

### Dockerでの起動例
```sh
docker run --name redis-local -p 6379:6379 -d redis
```

```sh
```

## 2. Pythonからの接続テスト
### redis-py のインストール
```sh
pip install redis
```

### サンプルコード
```python
import redis

r = redis.Redis(host='localhost', port=6379, db=0)
r.set('foo', 'bar')
print(r.get('foo'))  # b'bar'
```

## 3. FastAPIでの疎通確認
### セッションやキャッシュのset/getエンドポイント例
`app/api/redis_sample.py` などを作成:
```python
from fastapi import APIRouter
import redis

router = APIRouter()
r = redis.Redis(host='localhost', port=6379, db=0)

@router.post('/redis/set')
def set_value(key: str, value: str):
    r.set(key, value)
    return {"result": "ok"}

@router.get('/redis/get')
def get_value(key: str):
    value = r.get(key)
    return {"value": value.decode() if value else None}
```

### 動作確認方法
1. FastAPIサーバーを起動
2. `POST /redis/set?key=test&value=hello` で値をセット
```
Invoke-RestMethod -Uri "http://localhost:8000/redis/set?key=test&value=hello" -Method Post
```
3. `GET /redis/get?key=test` で値を取得し、`{"value": "hello"}` が返ることを確認
```
Invoke-RestMethod -Uri "http://localhost:8000/redis/get?key=test" -Method Get
```

## 4. トラブルシューティング
- **接続できない場合**: Redisサーバーが起動しているか確認。ポート番号やホスト名が正しいかチェック。
- **Windowsで動かない場合**: MemuraiやWSL上のRedisを利用する。
- **パーミッションエラー**: Dockerの場合は`docker ps`でコンテナが動作中か確認。
- **FastAPIでエラーが出る場合**: `redis-py`がインストールされているか、`requirements.txt`に追加されているか確認。
