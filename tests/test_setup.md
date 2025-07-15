# テスト実行手順

## 1. 必要なパッケージのインストール

```
pip install pytest httpx
```

## 2. テストの実行

```
$env:PYTHONPATH="."
pytest tests/test_openai.py
```

または、全テストを実行する場合：
```
$env:PYTHONPATH="."
pytest
```

## 3. 補足
- テストは `x-auto-post-tool` ディレクトリで実行してください。
- すべてのテストがパスすればOKです。 