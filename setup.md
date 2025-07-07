# FastAPI 最小構成セットアップ手順

## 1. Python仮想環境の作成（任意）
```
python -m venv venv
```

## 2. 仮想環境の有効化（Windowsの場合）
```
venv\Scripts\activate
```
※powershellでスクリプトの実行が無効になっている場合
```
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
```
https://qiita.com/ponsuke0531/items/4629626a3e84bcd9398f

## 3. 必要パッケージのインストール
```
pip install fastapi uvicorn
```

## 4. サーバーの起動
```
uvicorn app.main:app --reload
```

## 5. 動作確認
- ブラウザで `http://127.0.0.1:8000/` にアクセスし、`{"message": "Hello, FastAPI!"}` が表示されることを確認してください。
- 自動ドキュメント: `http://127.0.0.1:8000/docs` 

## 終了方法(venvの抜け方)
```
deactivate
```