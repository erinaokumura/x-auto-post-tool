# x-auto-post-tool

## ディレクトリ構成

```
x-auto-post-tool/
├── app/
│   └── main.py              # FastAPI本体
├── tests/
│   ├── test_main.py         # テストコード
│   └── test_setup.md        # テスト実行手順
├── docs/
│   ├── api_design.md        # API設計
│   ├── idea_summary.md      # アイデアまとめ
│   └── todo.md              # TODOリスト
├── setup.md                 # セットアップ手順
├── README.md                # 全体説明・構成
├── venv/                    # 仮想環境
```

## セットアップ

1. 仮想環境の作成・有効化（Windows PowerShellの場合）
```
python -m venv venv
.\venv\Scripts\Activate.ps1
```

2. 必要パッケージのインストール
```
pip install fastapi uvicorn pytest httpx
```

## 環境変数の設定

1. プロジェクトルートにある`.env.example`をコピーして`.env`を作成してください。

```sh
cp .env.example .env
```

2. `.env`ファイル内の各APIキーやシークレット値を設定してください。

- `.env`は**絶対にGit管理しないでください**（.gitignoreで除外済み）

## サーバーの起動

```
uvicorn app.main:app --reload
```

- ブラウザで [http://127.0.0.1:8000/](http://127.0.0.1:8000/) にアクセス
- 自動ドキュメント: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## テストの実行

```
python -m pytest tests/test_main.py
```

---

詳細なセットアップ手順は `setup.md`、テスト手順は `tests/test_setup.md` を参照してください。 