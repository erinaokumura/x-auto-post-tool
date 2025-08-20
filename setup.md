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

### Python 3.13使用時の注意事項
Python 3.13を使用する場合、一部のバイナリパッケージで互換性の問題が発生する可能性があります。
以下の手順で解決できます：

1. **依存関係エラーが発生した場合：**
   ```
   # 問題のあるパッケージを個別に再インストール
   pip uninstall pydantic pydantic-core cryptography psycopg2-binary cffi -y
   pip install --upgrade pip setuptools wheel
   pip install pydantic==2.11.7 pydantic-core==2.33.2
   pip install cryptography==44.0.0 cffi==1.17.1
   pip install --only-binary=all psycopg2-binary==2.9.10
   ```

2. **バイナリパッケージの優先インストール（推奨）：**
   ```
   pip install --only-binary=all psycopg2-binary
   ```

## 4. サーバーの起動
```
uvicorn app.main:app --reload
```

※開発時の動作確認時はhttpを許可する
```
$env:OAUTHLIB_INSECURE_TRANSPORT="1"
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
3. 【※Binary filesになってしまうためやらない方がよさそう】requirements-dev.txtに追加する
   ```
   pip freeze | Select-String alembic >> requirements-dev.txt
   ```
   ※ `Select-String`はPowerShell用コマンドです。コマンドプロンプトの場合は`findstr`を使ってください。

---

本番用パッケージの場合は`requirements.txt`に追記してください。

## トラブルシューティング

### 起動時のModuleNotFoundErrorについて

#### 1. `ModuleNotFoundError: No module named 'pydantic_core._pydantic_core'`
**原因:** PydanticとPydantic-coreのバージョン不整合
**解決方法:**
```
pip uninstall pydantic pydantic-core -y
pip install pydantic==2.11.7 pydantic-core==2.33.2
```

#### 2. `ModuleNotFoundError: No module named '_cffi_backend'`
**原因:** cryptographyの依存関係（cffi）の問題
**解決方法:**
```
pip uninstall cryptography cffi -y
pip install cryptography==44.0.0 cffi==1.17.1
```

#### 3. `ModuleNotFoundError: No module named 'psycopg2._psycopg'`
**原因:** psycopg2-binaryのPython 3.13互換性問題
**解決方法:**
```
pip uninstall psycopg2-binary -y
pip install --only-binary=all psycopg2-binary==2.9.10
```

### 一括解決手順
上記のエラーが複数発生する場合は、以下を順次実行：
```
# 1. 仮想環境をactivate
.\venv\Scripts\Activate.ps1

# 2. 問題のあるパッケージをすべてアンインストール
pip uninstall pydantic pydantic-core cryptography psycopg2-binary cffi -y

# 3. pipを最新版に更新
python -m pip install --upgrade pip setuptools wheel

# 4. パッケージを正しい順序で再インストール
pip install pydantic==2.11.7 pydantic-core==2.33.2
pip install cryptography==44.0.0 cffi==1.17.1
pip install --only-binary=all psycopg2-binary==2.9.10

# 5. FastAPIを再インストール（依存関係を確実にする）
pip install --force-reinstall fastapi==0.115.14
```
