#!/bin/bash
# Railway起動スクリプト

# PORT環境変数が設定されていない場合は8000をデフォルトに
PORT=${PORT:-8000}

echo "Starting uvicorn on port $PORT"
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT
