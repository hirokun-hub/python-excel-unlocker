#!/usr/bin/env bash
# fe-debug.sh — フロントエンドのデバッグ情報を安全に一括採取
# 目的:
#  - OAuth後に localhost 接続拒否になる等の「環境/ポート不一致」を即断できるログを集める
#  - 型/ESLint/ビルド/ルーティングの要点を一式収集（秘密は出力しない）
#
# 使い方:
#   chmod +x fe-debug.sh
#   ./fe-debug.sh                # カレントが frontend でもルートでもOK
#   ./fe-debug.sh outdir-name    # 出力ディレクトリ名を指定したい場合
#
# 生成物:
#   fe-debug-YYYYmmdd-HHMMSS/ ... を zip に固めてカレントに出力

set -u                              # 未定義変数はエラー
# 失敗しても極力継続したいので -e は付けない
export LC_ALL=C

#-------------------------------
# 小物ユーティリティ
#-------------------------------
ts() { date +"%Y-%m-%d %H:%M:%S"; }
log() { printf "[%s] %s\n" "$(ts)" "$*" >&2; }
save_run() {
  # $1: 出力パス, 以降: コマンド
  local out="$1"; shift
  ( "$@" ) >"$out" 2>&1 || true
}

#-------------------------------
# ルート/対象ディレクトリ決定
#-------------------------------
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT"

# frontend ディレクトリ自動検出（src が無ければ frontend を優先）
if [ -d "src" ]; then
  TARGET_DIR="$REPO_ROOT"
elif [ -d "frontend" ]; then
  TARGET_DIR="$REPO_ROOT/frontend"
else
  TARGET_DIR="$REPO_ROOT"
fi
cd "$TARGET_DIR"

#-------------------------------
# 出力先
#-------------------------------
STAMP="$(date +%Y%m%d-%H%M%S)"
OUT_DIR="${1:-fe-debug-$STAMP}"
mkdir -p "$OUT_DIR"/{snippets,tree}

log "Collect to: $OUT_DIR"
log "Target dir : $TARGET_DIR"

#-------------------------------
# パッケージマネージャ検出
#-------------------------------
PM="npm"
if [ -f "pnpm-lock.yaml" ] && command -v pnpm >/dev/null 2>&1; then
  PM="pnpm"
elif [ -f "yarn.lock" ] && command -v yarn >/dev/null 2>&1; then
  PM="yarn"
fi
echo "$PM" > "$OUT_DIR/pkgmgr.txt"

#-------------------------------
# 環境情報
#-------------------------------
save_run "$OUT_DIR/os.txt"               uname -a
save_run "$OUT_DIR/node_version.txt"     node -v
save_run "$OUT_DIR/npm_version.txt"      npm -v
[ "$PM" != "npm" ] && save_run "$OUT_DIR/${PM}_version.txt" "$PM" -v

# Next / envinfo
save_run "$OUT_DIR/next_info.txt"   npx --yes next info
save_run "$OUT_DIR/envinfo.txt"     npx --yes envinfo --system --binaries --browsers --npmPackages next,react,react-dom,next-auth,@auth/core,typescript,eslint

# Git スナップショット（秘密なし）
if command -v git >/dev/null 2>&1; then
  save_run "$OUT_DIR/git_rev.txt"           git rev-parse --short HEAD
  save_run "$OUT_DIR/git_status.txt"        git status --porcelain=v2
  save_run "$OUT_DIR/git_branch.txt"        git rev-parse --abbrev-ref HEAD
fi

#-------------------------------
# 主要設定ファイルの抜粋
#-------------------------------
for f in package.json next.config.{js,ts,mjs,cjs} tsconfig.{json,tsbuildinfo} tailwind.config.{js,ts} postcss.config.{js,ts}; do
  for p in $f; do
    [ -f "$p" ] && cp "$p" "$OUT_DIR/snippets/$(basename "$p")"
  done
done

# 依存一覧（サイズ抑制のため prod+dev 名称のみ）
save_run "$OUT_DIR/npm_ls.txt"  node -e 'try{const pkg=require("./package.json");console.log("dependencies");console.log(Object.keys(pkg.dependencies||{}).sort().join("\n"));console.log("\ndevDependencies");console.log(Object.keys(pkg.devDependencies||{}).sort().join("\n"));}catch(e){console.log(e?.message)}'

#-------------------------------
# ソースツリーと気になる参照
#-------------------------------
save_run "$OUT_DIR/tree/src.txt"   bash -lc 'command -v tree >/dev/null && tree -a -L 3 src || find src -maxdepth 3 -print'
# "@/lib/utils" を参照しているファイルと utils.ts の実体
if [ -f "src/lib/utils.ts" ]; then
  sed -n '1,200p' src/lib/utils.ts > "$OUT_DIR/snippets/src-lib-utils.ts.txt"
else
  echo "src/lib/utils.ts not found" > "$OUT_DIR/snippets/src-lib-utils.ts.txt"
fi
grep -R -n "@/lib/utils" src 2>/dev/null | cut -d: -f1 | sort -u | while read -r f; do
  echo "---- $f ----" >> "$OUT_DIR/snippets/offending_files.txt"
  sed -n '1,160p' "$f" >> "$OUT_DIR/snippets/offending_files.txt" 2>/dev/null || true
  echo >> "$OUT_DIR/snippets/offending_files.txt"
done

#-------------------------------
# 型 / ESLint スナップショット
#-------------------------------
save_run "$OUT_DIR/tsc.txt"     npx -y tsc --noEmit
# lint スクリプト優先、無ければ eslint . を試す
if jq -e '.scripts.lint' package.json >/dev/null 2>&1; then
  save_run "$OUT_DIR/eslint.txt" npm run -s lint
else
  save_run "$OUT_DIR/eslint.txt" npx -y eslint .
fi

#-------------------------------
# dev ポート推定 & Auth ベースURL整合チェック
#-------------------------------
DEV_PORT="$(node -e "try{const s=require('./package.json').scripts?.dev||'';const m=s.match(/-p\\s*(\\d+)/);process.stdout.write(m?m[1]:'3000')}catch(e){process.stdout.write('3000')}")"
echo "$DEV_PORT" > "$OUT_DIR/dev_port.txt"

{
  echo "NEXTAUTH_URL=${NEXTAUTH_URL:+set}"
  echo "AUTH_URL=${AUTH_URL:+set}"
  BASE_URL="${NEXTAUTH_URL:-${AUTH_URL:-http://localhost:$DEV_PORT}}"
  echo "baseUrl=$BASE_URL"
  node -e "const u=process.env.NEXTAUTH_URL||process.env.AUTH_URL||'';const dev=process.argv[2];if(!u){console.log('status=NO_ENV');process.exit(0)}try{const p=new URL(u).port||'80';console.log(p===dev?'status=OK':'status=MISMATCH envPort='+p+' devPort='+dev)}catch{console.log('status=PARSE_ERROR')}" "$DEV_PORT"
  echo "expected_redirect=$BASE_URL/api/auth/callback/google"
} > "$OUT_DIR/auth_baseurl_check.txt"

# .env の「存在のみ」（値は伏せる/長さのみ）
{
  for k in NEXTAUTH_URL AUTH_URL NEXTAUTH_SECRET GOOGLE_CLIENT_ID GOOGLE_CLIENT_SECRET NODE_ENV; do
    if printenv "$k" >/dev/null 2>&1; then
      v="$(printenv "$k")"; printf "%s=set len=%d\n" "$k" "${#v}"
    else
      printf "%s=UNSET\n" "$k"
    fi
  done
} > "$OUT_DIR/env_snapshot_redacted.txt"

#-------------------------------
# ビルド & マニフェスト
#-------------------------------
# 可能ならクリーン → ビルド。失敗してもログは残す。
if jq -e '.scripts.build' package.json >/dev/null 2>&1; then
  [ -d ".next" ] && rm -rf .next
  (npm run build || true) 2>&1 | tee "$OUT_DIR/build.log" >/dev/null
  # 成果物があればルーティング/ビルドマニフェストを収集
  [ -f .next/routes-manifest.json ] && cp .next/routes-manifest.json "$OUT_DIR/" || true
  [ -f .next/build-manifest.json ]  && cp .next/build-manifest.json  "$OUT_DIR/" || true
else
  echo "no build script" > "$OUT_DIR/build.log"
fi

#-------------------------------
# 追加ヘルスチェック（起動はしない/安全なHTTPのみ）
#-------------------------------
# CSRF エンドポイントは dev サーバが起動していないと 失敗→それもログ化
save_run "$OUT_DIR/http_probe_csrf.txt" bash -lc "curl -sS -I http://localhost:${DEV_PORT}/api/auth/csrf"

#-------------------------------
# 最後に ZIP
#-------------------------------
ZIP="${OUT_DIR}.zip"
log "Zipping to: $ZIP"
# macOS の場合 ditto が速い
if command -v ditto >/dev/null 2>&1; then
  ditto -c -k --sequesterRsrc --keepParent "$OUT_DIR" "$ZIP"
else
  (command -v zip >/dev/null 2>&1 && zip -rq "$ZIP" "$OUT_DIR") || tar -czf "${OUT_DIR}.tar.gz" "$OUT_DIR"
fi

log "Done."
log "Attach: $ZIP"
