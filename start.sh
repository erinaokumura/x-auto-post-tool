#!/bin/bash
# Railway起動スクリプト

# デバッグ情報を出力
echo "=== Railway Startup Debug ==="
echo "PORT environment variable: '$PORT'"
echo "All environment variables:"
env | grep -E "(PORT|RAILWAY)" || echo "No PORT/RAILWAY variables found"

# PORT環境変数が設定されていない場合は8000をデフォルトに
if [ -z "$PORT" ]; then
    echo "PORT not set, using default 8000"
    PORT=8000
else
    echo "Using PORT: $PORT"
fi

echo "Starting uvicorn on port $PORT"
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT
