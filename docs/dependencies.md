# 依存関係管理

## 概要

このプロジェクトでは、Pythonの依存関係を適切に管理し、再現可能な環境を構築することを目的としています。

## ファイル構成

### requirements.txt
本番環境で必要な依存関係を定義します。

```txt
# FastAPI関連
fastapi==0.115.14
uvicorn==0.35.0

# 設定管理
pydantic==2.11.7
pydantic-settings==2.10.1
typing-inspection==0.4.1

# Twitter API関連
tweepy==4.16.0

# OpenAI API関連
openai==1.93.3

# HTTP リクエスト
requests==2.32.4

# テスト関連
pytest==8.4.1
httpx==0.28.1

# 環境変数管理
python-dotenv==1.1.1
```

### requirements-dev.txt
開発環境で必要な追加の依存関係を定義します。

```txt
# 本番環境の依存関係を含む
-r requirements.txt

# 開発・テスト用追加依存関係
pytest-cov==4.1.0
pytest-asyncio==0.21.1
pytest-mock==3.12.0

# コード品質・フォーマット
black==23.11.0
flake8==6.1.0
mypy==1.7.1
isort==5.12.0
pre-commit==3.6.0

# ドキュメント生成
mkdocs==1.5.3
mkdocs-material==9.4.8

# 型チェック
types-requests==2.31.0.10
```

## 依存関係の説明

### 本番環境必須パッケージ

#### FastAPI関連
- **fastapi**: Web APIフレームワーク
- **uvicorn**: ASGIサーバー（FastAPIの実行に必要）

#### 設定管理
- **pydantic**: データバリデーションとシリアライゼーション
- **pydantic-settings**: 環境変数ベースの設定管理
- **typing-inspection**: pydanticの依存関係

#### 外部API連携
- **tweepy**: Twitter APIクライアント
- **openai**: OpenAI APIクライアント
- **requests**: HTTP リクエストライブラリ

#### テスト
- **pytest**: テストフレームワーク
- **httpx**: テスト用HTTPクライアント

#### その他
- **python-dotenv**: 環境変数ファイルの読み込み

### 開発環境追加パッケージ

#### テスト拡張
- **pytest-cov**: テストカバレッジ測定
- **pytest-asyncio**: 非同期テストサポート
- **pytest-mock**: モック機能

#### コード品質
- **black**: コードフォーマッター
- **flake8**: リンター
- **mypy**: 型チェッカー
- **isort**: import文の整理
- **pre-commit**: コミット前フック

#### ドキュメント
- **mkdocs**: ドキュメント生成
- **mkdocs-material**: Material for MkDocsテーマ

#### 型チェック
- **types-requests**: requestsの型定義

## インストール方法

### 本番環境
```bash
pip install -r requirements.txt
```

### 開発環境
```bash
pip install -r requirements-dev.txt
```

## 依存関係の更新

### 新しいパッケージの追加
1. パッケージをインストール
2. `pip freeze`でバージョンを確認
3. 適切なrequirementsファイルに追加

### バージョン更新
1. 新しいバージョンをインストール
2. テストを実行して動作確認
3. requirementsファイルを更新

### 不要なパッケージの削除
1. パッケージをアンインストール
2. テストを実行して動作確認
3. requirementsファイルから削除

## セキュリティ考慮事項

### 脆弱性スキャン
定期的に以下のコマンドで脆弱性をチェックします：

```bash
pip-audit
```

### 依存関係の最小化
- 必要最小限のパッケージのみをインストール
- 不要な依存関係は定期的に削除
- 直接使用していないパッケージは除外

## トラブルシューティング

### よくある問題

#### 1. バージョン競合
```bash
# 仮想環境を再作成
python -m venv venv_new
source venv_new/bin/activate  # Linux/Mac
venv_new\Scripts\activate     # Windows
pip install -r requirements.txt
```

#### 2. 依存関係の循環参照
```bash
# 依存関係ツリーを確認
pip install pipdeptree
pipdeptree
```

#### 3. パッケージが見つからない
```bash
# キャッシュをクリア
pip cache purge
pip install --no-cache-dir -r requirements.txt
```

## ベストプラクティス

1. **バージョン固定**: 再現可能な環境のため、バージョンを固定
2. **定期的な更新**: セキュリティアップデートのため、定期的に更新
3. **テスト実行**: 依存関係変更後は必ずテストを実行
4. **ドキュメント更新**: 依存関係変更時はドキュメントを更新
5. **最小化**: 必要最小限のパッケージのみを使用

## 今後の改善点

1. **Poetry導入**: より高度な依存関係管理のため
2. **Docker化**: 環境の完全な分離のため
3. **CI/CD連携**: 自動的な依存関係チェックのため
4. **セキュリティスキャン**: 自動的な脆弱性チェックのため 