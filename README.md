# x-auto-post-tool

## ディレクトリ構成

```
x-auto-post-tool/
├── app/
│   ├── main.py              # FastAPI本体
│   ├── config.py            # 設定管理
│   ├── api/                 # APIルーター
│   ├── services/            # ビジネスロジック
│   ├── auth/                # 認証関連
│   ├── schemas/             # データモデル
│   └── utils/               # ユーティリティ
├── tests/                   # テストコード
├── docs/                    # ドキュメント
│   ├── todo_list/           # TODOリスト
│   └── dependencies.md      # 依存関係管理
├── requirements.txt         # 本番環境依存関係
├── requirements-dev.txt     # 開発環境依存関係
├── setup.md                 # セットアップ手順
├── README.md                # 全体説明・構成
└── venv/                    # 仮想環境
```

## セットアップ

### 1. 環境設定ファイルの準備

環境ごとに適切な設定ファイルを作成してください：

```bash
# 開発環境用
cp env.development.template .env.development
# 実際の値を設定して編集

# 本番環境用
cp env.production.template .env.production  
# 実際の値を設定して編集
```

詳細は [docs/environment_setup.md](docs/environment_setup.md) を参照してください。

## Railway + Vercel デプロイ構成

### アーキテクチャ
- **フロントエンド**: Vercel (Next.js)
- **バックエンド**: Railway (FastAPI)
- **データベース**: Railway (PostgreSQL + Redis)

### Railway デプロイ手順
1. GitHubリポジトリをRailwayに接続
2. 環境変数を設定（本番環境）
3. 自動デプロイが実行される

### 2. 仮想環境の作成・有効化（Windows PowerShellの場合）
```
python -m venv venv
.\venv\Scripts\Activate.ps1
```

2. 必要パッケージのインストール
```
pip install -r requirements.txt
```

開発環境の場合（テスト・コード品質ツールを含む）:
```
pip install -r requirements-dev.txt
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