#!/usr/bin/env bash
set -euo pipefail

# ====== 設定 ======
# プロジェクトのfrontendディレクトリ自動判定（なければカレント）
if [ -d ./frontend ] && [ -f ./frontend/package.json ]; then
  ROOT=./frontend
else
  ROOT=.
fi
PORT=${PORT:-3000}

TS=$(date +"%Y%m%d-%H%M%S")
OUT="fe-snapshot-${TS}"
mkdir -p "$OUT"

# ====== 基本情報 ======
(
  echo "PWD=$(pwd)"
  echo "ROOT=${ROOT}"
  echo -n "node: "; node -v 2>/dev/null || echo "N/A"
  echo -n "npm : "; npm -v 2>/dev/null || echo "N/A"
) > "$OUT/_meta.txt"

git -C "$ROOT" rev-parse --short HEAD > "$OUT/git_commit.txt" 2>/dev/null || echo "not-a-git-repo" > "$OUT/git_commit.txt"

# 主要ファイルをコピー（存在するものだけ）
cp "$ROOT/package.json" "$OUT/package.json" 2>/dev/null || true
cp "$ROOT/next.config."* "$OUT/" 2>/dev/null || true
cp "$ROOT/tsconfig."* "$OUT/" 2>/dev/null || true

# 環境変数（マスクして保存）
if [ -f "$ROOT/.env.local" ]; then
  sed -E 's/=.*/=***MASKED***/' "$ROOT/.env.local" > "$OUT/env.local.masked"
fi

# ツリー出力
(printf "== src tree (depth 3) ==\n"; cd "$ROOT" && find src -maxdepth 3 -print) > "$OUT/tree.txt"

# ====== 重要ファイルの存在確認 ======
CHECK=(
"src/components/DriveFolderPicker.tsx"
"src/lib/googleDrive.ts"
"src/app/api/drive/folders/route.ts"
"src/app/api/drive/breadcrumb/route.ts"
"src/auth.ts"
)

: > "$OUT/presence.txt"
for f in "${CHECK[@]}"; do
  if [ -f "$ROOT/$f" ]; then
    echo "OK   $f" >> "$OUT/presence.txt"
  else
    echo "MISS $f" >> "$OUT/presence.txt"
  fi
done

# auth.ts のスコープ痕跡
grep -nE "drive\.file|drive\.metadata\.readonly" "$ROOT/src/auth.ts" > "$OUT/auth_scopes.grep" 2>/dev/null || true

# UI テキスト/コンポーネント import/アップロード呼出の痕跡
if command -v rg >/dev/null 2>&1; then
  rg -n "保存先を選ぶ|DriveFolderPicker|uploadToDriveUsingAccessToken" "$ROOT/src" > "$OUT/grep_ui.txt" || true
else
  grep -RInE "保存先を選ぶ|DriveFolderPicker|uploadToDriveUsingAccessToken" "$ROOT/src" > "$OUT/grep_ui.txt" || true
fi

# 重要ソースのスナップショット（先頭220行）
for f in "${CHECK[@]}"; do
  [ -f "$ROOT/$f" ] || continue
  mkdir -p "$OUT/src/$(dirname "$f")"
  sed -n '1,220p' "$ROOT/$f" > "$OUT/src/$f"
done

# ====== HTTP 到達性（dev サーバーが起動しているときに有効）=====
: > "$OUT/http_checks.txt"
for path in "/" "/api/drive/folders" "/api/drive/breadcrumb"; do
  code=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:${PORT}${path}" || true)
  echo "$path -> HTTP $code" >> "$OUT/http_checks.txt"
done

# ====== 型チェック ======
( cd "$ROOT" && npx -y tsc --noEmit ) > "$OUT/tsc.txt" 2>&1 || true

# ====== 圧縮 ======
zip -rq "${OUT}.zip" "$OUT"
echo "DONE: ${OUT}.zip"
