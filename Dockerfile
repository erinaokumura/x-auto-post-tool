# Railway デプロイ用 Dockerfile
FROM python:3.13-slim

# 作業ディレクトリを設定
WORKDIR /app

# システム依存関係のインストール（必要最小限）
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python 依存関係のインストール
COPY requirements.txt .
RUN python -m pip install --upgrade pip setuptools wheel
RUN python -m pip install --no-cache-dir -r requirements.txt

# 起動スクリプトをコピーして実行権限を付与
COPY start.sh /start.sh
RUN chmod +x /start.sh

# アプリケーションコードをコピー
COPY . .

# Railwayが自動設定するPORT環境変数を使用
EXPOSE 8000

# 起動スクリプトを実行
CMD ["/start.sh"]

