#!/usr/bin/env bash
# ------------------------------------------------------------
# fe-snapshot.sh  (frontend diagnostics snapshot)
# ------------------------------------------------------------
# 用途:
# - フロントエンド開発環境の状態とAPI疎通を一括採取してZIP化
#
# 使い方:
#   bash scripts/fe-snapshot.sh
#
# 環境変数:
#   PORT=3000
#   BASE_URL=http://localhost:3000
#   FRONTEND_DIR=frontend
#   COOKIE="__Secure-next-auth.session-token=xxx; ..."
#   HEAVY=1    # 型チェックやlintも実行
# ------------------------------------------------------------

set -Eeuo pipefail
IFS=$'\n\t'

TS="$(date +%Y%m%d-%H%M%S)"
OUTDIR="fe-snapshot-${TS}"
mkdir -p "$OUTDIR"

log() { echo "[$(date +%H:%M:%S)] $*" | tee -a "$OUTDIR/_snapshot.log" ; }

PORT="${PORT:-3000}"
BASE_URL="${BASE_URL:-http://localhost:${PORT}}"

# FRONTEND_DIR 自動判定
if [[ -n "${FRONTEND_DIR:-}" ]]; then
  FE_DIR="$FRONTEND_DIR"
elif [[ -f "package.json" ]]; then
  FE_DIR="."
elif [[ -d "frontend" && -f "frontend/package.json" ]]; then
  FE_DIR="frontend"
else
  FE_DIR="."
fi

have_tree=0
command -v tree >/dev/null 2>&1 && have_tree=1 || true

# 秘匿情報マスク
mask_file() {
  local src="$1" dst="$2"
  [[ -f "$src" ]] || return 0
  sed -E \
    -e 's/^([A-Za-z0-9_]*(SECRET|TOKEN|PASSWORD|CLIENT_SECRET|PRIVATE_KEY|REFRESH_TOKEN|ACCESS_TOKEN|API_KEY|WEBHOOK|AUTH|PASSPHRASE)[A-Za-z0-9_]*)=.*/\1=***redacted***/g' \
    -e 's/("?(authorization|Authorization|AUTHORIZATION)"?\s*:\s*").*?(")/\1***redacted***\3/g' \
    -e 's/(Bearer )[A-Za-z0-9\.\-\_=]+/\1***redacted***/g' \
    "$src" > "$dst" || true
}

# package.json の指定フィールドを取り出す（jq なければ node で）
pkg_field() {
  local file="$1" field="$2"
  if command -v jq >/dev/null 2>&1; then
    jq -r ".$field // empty" "$file" 2>/dev/null || true
  else
    FILE="$file" FIELD="$field" node -e '
      const fs=require("fs");
      const file=process.env.FILE, path=(process.env.FIELD||"").split(".").filter(Boolean);
      try{
        let v=JSON.parse(fs.readFileSync(file,"utf8"));
        for(const k of path){ if(v==null) break; v=v[k]; }
        if(v==null) process.exit(0);
        console.log(typeof v==="object"?JSON.stringify(v,null,2):String(v));
      }catch(e){}
    ' 2>/dev/null || true
  fi
}

run_save() { local outfile="$1"; shift; ( set +e; "$@" ) >"$OUTDIR/$outfile" 2>&1 || true; }

log "=== Basic info ==="
{
  echo "Base URL   : $BASE_URL"
  echo "Frontend   : $FE_DIR"
  echo "CWD        : $(pwd)"
  echo "OS         : $(uname -a)"
  sw_vers 2>/dev/null || true
} | tee "$OUTDIR/system.txt" >/dev/null

log "=== Versions ==="
{
  command -v node >/dev/null 2>&1 && { echo -n "node: "; node -v; }
  command -v npm  >/dev/null 2>&1 && { echo -n "npm : "; npm -v; }
  command -v pnpm >/dev/null 2>&1 && { echo -n "pnpm: "; pnpm -v; }
  command -v bun  >/dev/null 2>&1 && { echo -n "bun : "; bun -v; }
  (cd "$FE_DIR" && npx -y next --version) 2>/dev/null || true
  (cd "$FE_DIR" && node -p 'require("./package.json").dependencies?.next || require("./package.json").devDependencies?.next') 2>/dev/null || true
} > "$OUTDIR/versions.txt"

log "=== Git ==="
run_save git.txt bash -lc 'git rev-parse --abbrev-ref HEAD; git log -1 --pretty=fuller; echo; git status --porcelain=v1 -uno; echo; git remote -v'

log "=== Project tree (top) ==="
if [[ $have_tree -eq 1 ]]; then
  run_save tree.txt bash -lc 'tree -a -L 3 -I node_modules .'
else
  run_save tree.txt bash -lc 'find . -maxdepth 3 -not -path "*/node_modules/*" -print'
fi

log "=== package.json summary ==="
if [[ -f "$FE_DIR/package.json" ]]; then
  cp "$FE_DIR/package.json" "$OUTDIR/package.json"
  {
    echo "name        : $(pkg_field "$FE_DIR/package.json" "name")"
    echo "scripts     :"
    pkg_field "$FE_DIR/package.json" "scripts"
    echo
    echo "dependencies:"
    pkg_field "$FE_DIR/package.json" "dependencies"
    echo
    echo "devDependencies:"
    pkg_field "$FE_DIR/package.json" "devDependencies"
  } > "$OUTDIR/package-summary.txt"
fi

log "=== .env files (masked) ==="
for f in ".env" ".env.local" ".env.development" "$FE_DIR/.env" "$FE_DIR/.env.local" "$FE_DIR/.env.development"; do
  [[ -f "$f" ]] && mask_file "$f" "$OUTDIR/$(basename "$f").masked"
done

log "=== TypeScript / Lint (optional) ==="
if [[ "${HEAVY:-0}" -eq 1 ]]; then
  if grep -q '"typecheck"' "$FE_DIR/package.json" 2>/dev/null; then
    run_save tsc.txt bash -lc 'cd "'"$FE_DIR"'" && npm run -s typecheck'
  else
    run_save tsc.txt bash -lc 'cd "'"$FE_DIR"'" && npx -y tsc --noEmit'
  fi
  if grep -q '"lint"' "$FE_DIR/package.json" 2>/dev/null; then
    run_save eslint.txt bash -lc 'cd "'"$FE_DIR"'" && npm run -s lint'
  fi
else
  echo "HEAVY=1 を指定すると型チェックとlintを実行します。" > "$OUTDIR/tsc.txt"
fi

log "=== Drive picker related greps ==="
run_save grep_ui.txt bash -lc 'grep -RIn --line-number -E "Drive|google|folders|mimeType|parents|contains|fullText|picker" "'"$FE_DIR/src"'" 2>/dev/null || true'

log "=== NextAuth / scope hints ==="
run_save auth_scopes.grep bash -lc 'grep -RIn -E "GoogleProvider|scope|scopes|next-auth|getServerSession|session|jwt|access_token" "'"$FE_DIR/src"'" 2>/dev/null || true'

log "=== API quick checks (curl) ==="
HTTP_LOG="$OUTDIR/http_checks.txt"; : >"$HTTP_LOG"
curl_save() {
  local path="$1" name="$2"; local url="${BASE_URL}${path}"
  local hdr="$OUTDIR/${name}.headers.txt"; local body="$OUTDIR/${name}.body.txt"
  if [[ -n "${COOKIE:-}" ]]; then
    curl -sk -D "$hdr" -H "Cookie: $COOKIE" -H "Accept: application/json" "$url" -o "$body" || true
  else
    curl -sk -D "$hdr" -H "Accept: application/json" "$url" -o "$body" || true
  fi
  local code; code="$(head -1 "$hdr" | sed -E 's/.* ([0-9]{3}) .*/\1/')" || code="000"
  echo "$url -> $code" | tee -a "$HTTP_LOG"
}
curl_save "/"                                   "root_index"
curl_save "/api/drive/breadcrumb?id=root"       "api_breadcrumb_root"
curl_save "/api/drive/folders?parentId=root"    "api_folders_root"
curl_save "/api/drive/folders?q=test"           "api_folders_search_test"
curl_save "/api/drive/folders?parentId=root&mode=children" "api_folders_children"
# スコープ確認のための軽いAPI
curl_save "/api/drive/about"                    "api_drive_about" || true

log "=== Accessibility warnings (Dialog etc.) hint ==="
run_save a11y_warnings.grep bash -lc 'grep -RIn -E "aria-|Dialog(Content|Description)" "'"$FE_DIR/src"'" 2>/dev/null || true'

log "=== Capture next.config.js / tsconfig.json ==="
for f in "$FE_DIR/next.config.js" "$FE_DIR/next.config.mjs" "$FE_DIR/tsconfig.json"; do
  [[ -f "$f" ]] && cp "$f" "$OUTDIR/$(basename "$f")"
done
if [[ -d "$FE_DIR/src/app" ]]; then
  if [[ $have_tree -eq 1 ]]; then
    run_save app-tree.txt bash -lc 'tree -a -L 3 "'"$FE_DIR/src/app"'"'
  else
    run_save app-tree.txt bash -lc 'find "'"$FE_DIR/src/app"'" -maxdepth 3 -print'
  fi
fi

log "=== Lockfile hash ==="
if [[ -f "$FE_DIR/package-lock.json" ]]; then
  run_save lock_hash.txt bash -lc 'cd "'"$FE_DIR"'" && (sha256sum package-lock.json 2>/dev/null || shasum -a 256 package-lock.json)'
elif [[ -f "$FE_DIR/pnpm-lock.yaml" ]]; then
  run_save lock_hash.txt bash -lc 'cd "'"$FE_DIR"'" && (sha256sum pnpm-lock.yaml 2>/dev/null || shasum -a 256 pnpm-lock.yaml)'
elif [[ -f "$FE_DIR/yarn.lock" ]]; then
  run_save lock_hash.txt bash -lc 'cd "'"$FE_DIR"'" && (sha256sum yarn.lock 2>/dev/null || shasum -a 256 yarn.lock)'
fi

log "=== Finalize ZIP ==="
ZIP="${OUTDIR}.zip"
( set +e; command -v zip >/dev/null 2>&1 && zip -r "$ZIP" "$OUTDIR" >/dev/null 2>&1 || tar -czf "${OUTDIR}.tar.gz" "$OUTDIR" )
if [[ -f "$ZIP" ]]; then
  log "Snapshot created: $ZIP"
else
  log "Snapshot created: ${OUTDIR}.tar.gz"
fi
log "Done."