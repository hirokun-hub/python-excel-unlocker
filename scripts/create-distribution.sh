#!/bin/bash
set -e

PACKAGE_NAME="excel-unlocker"
DIST_DIR="distribution/${PACKAGE_NAME}"
ZIP_FILE="${PACKAGE_NAME}.zip"
IMAGE_TAR_AMD64="${DIST_DIR}/images/app_linux-amd64.tar"
IMAGE_TAR_ARM64="${DIST_DIR}/images/app_linux-arm64.tar"

echo "🚀 ${PACKAGE_NAME} 配布パッケージ作成開始"

echo "📦 既存の配布物を確認中..."
if [ -d "${DIST_DIR}" ] || [ -f "${ZIP_FILE}" ]; then
    read -p "既存の配布物を上書きしますか？ (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ 中止しました"
        exit 1
    fi
fi

echo "🧹 クリーンアップ中..."
rm -rf "${DIST_DIR}" "${ZIP_FILE}"
mkdir -p "${DIST_DIR}/images"

echo "🔨 Docker イメージをビルド中 (amd64)..."
docker buildx build \
  --platform linux/amd64 \
  -t excel-unlocker:latest \
  --output type=docker,dest="${IMAGE_TAR_AMD64}" \
  .

echo "🔨 Docker イメージをビルド中 (arm64)..."
docker buildx build \
  --platform linux/arm64 \
  -t excel-unlocker:latest \
  --output type=docker,dest="${IMAGE_TAR_ARM64}" \
  .

echo "📋 配布テンプレートをコピー中..."
cp distribution-templates/docker-compose.yml "${DIST_DIR}/"
cp distribution-templates/README.txt "${DIST_DIR}/"
cp distribution-templates/setup.command "${DIST_DIR}/"
cp distribution-templates/start.command "${DIST_DIR}/"
cp distribution-templates/setup.bat "${DIST_DIR}/"
cp distribution-templates/start.bat "${DIST_DIR}/"

if [ -f ".env" ]; then
    echo "🔑 .env を server.env として同梱します"
    cp .env "${DIST_DIR}/server.env"
else
    echo "⚠️ .env が見つかりません。環境変数ファイルは同梱されません。"
fi

echo "🔐 実行権限を付与中 (Mac 用スクリプト)..."
chmod +x "${DIST_DIR}/setup.command" "${DIST_DIR}/start.command"

pushd distribution >/dev/null

echo "📦 ZIP を作成中..."
zip -r "../${ZIP_FILE}" "${PACKAGE_NAME}"

popd >/dev/null

ZIP_SIZE=$(du -m "${ZIP_FILE}" | cut -f1)
echo ""
echo "✅ 配布パッケージ作成完了 (${ZIP_SIZE}MB)"
echo "📍 出力: $(pwd)/${ZIP_FILE}"
