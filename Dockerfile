# Excel Unlocker Dockerfile
# Python 3.11 ベースイメージを使用
# Requirements: 4.3, Dockerfile 環境変数

FROM python:3.11-slim

# メタデータ
LABEL maintainer="Excel Unlocker Team"
LABEL description="パスワード付き Excel ファイルを解除する Web アプリケーション"
LABEL version="1.0.0"

# 環境変数の設定（Requirements: 4.3）
ENV TMP_DIR=/tmp/excel-unlocker
ENV PORT=3000
ENV HOST=0.0.0.0
ENV MAX_WORKERS=4
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 作業ディレクトリの設定
WORKDIR /app

# システム依存関係のインストール
# msoffcrypto-tool が必要とする依存関係を含む
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# 一時ディレクトリの作成
RUN mkdir -p ${TMP_DIR}

# 依存関係ファイルをコピー
COPY requirements.txt .

# Python 依存関係のインストール
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピー
COPY app/ ./app/
COPY static/ ./static/

# ポートの公開
EXPOSE ${PORT}

# ヘルスチェック（Requirements: 4.4）
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT}/health')" || exit 1

# アプリケーションの起動
# uvicorn を使用して FastAPI アプリケーションを起動
CMD ["sh", "-c", "uvicorn app.main:app --host ${HOST} --port ${PORT}"]
