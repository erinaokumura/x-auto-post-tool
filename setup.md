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
pip install -r requirements.txt
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

==============================================
## その他設定
- CursorとGithubを連携する
  - https://www.genspark.ai/spark/cursor%E3%81%A8github%E3%81%AE%E9%80%A3%E6%90%BA%E6%89%8B%E9%A0%86/612143bb-739e-417c-90fd-120cd8b76073

## 環境変数の設定

1. プロジェクトルートにある`.env.example`をコピーして`.env`を作成してください。

```sh
cp .env.example .env
```

2. `.env`ファイル内の各APIキーやシークレット値を設定してください。

- `.env`は**絶対にGit管理しないでください**（.gitignoreで除外済み）

## 新しいパッケージの追加手順（開発用パッケージの場合）

1. 仮想環境を有効化する
   ```
   venv\Scripts\activate
   ```
2. パッケージをインストールする（例: alembic）
   ```
   pip install alembic
   ```
3. requirements-dev.txtに追加する
   ```
   pip freeze | Select-String alembic >> requirements-dev.txt
   ```
   ※ `Select-String`はPowerShell用コマンドです。コマンドプロンプトの場合は`findstr`を使ってください。

---

本番用パッケージの場合は`requirements.txt`に追記してください。
