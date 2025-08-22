#!/usr/bin/env bash
# frontend/scripts/fe-debug.sh
# 収集: 環境/設定/ツリー/エイリアス参照/ビルドログ → ZIP化（秘密は含めない）
set -u  # 変数未定義をエラーに。-eは付けず、失敗しても収集継続。

# frontend直下で走っていることを想定。もしルートから呼ばれたら自動で移動。
if [ -f "package.json" ] && [ -d "src" ]; then
  : # ここがfrontend
elif [ -d "frontend" ] && [ -f "frontend/package.json" ]; then
  cd frontend
else
  echo "Error: Next.jsのfrontendが見つかりません。frontend/ か package.json のある場所で実行してください。" >&2
  exit 1
fi

STAMP=$(date +%Y%m%d-%H%M%S)
OUT="fe-debug-$STAMP"
mkdir -p "$OUT/snippets"

# パッケージマネージャ検出
if command -v pnpm >/dev/null 2>&1; then PM="pnpm"
elif command -v npm  >/dev/null 2>&1; then PM="npm"
elif command -v yarn >/dev/null 2>&1; then PM="yarn"
else PM="npm"; fi

# 1) 環境
(node -v           > "$OUT/node_version.txt"        2>&1) || true
($PM -v            > "$OUT/pkgmgr_version.txt"      2>&1) || true
(uname -a          > "$OUT/os.txt"                  2>&1) || true

# 2) Git 状態
(git rev-parse --abbrev-ref HEAD > "$OUT/git_head.txt"     2>&1) || true
(git status -sb                   > "$OUT/git_status.txt"  2>&1) || true
(git branch -vv                   > "$OUT/git_branches.txt" 2>&1) || true
(git remote -v                    > "$OUT/git_remotes.txt" 2>&1) || true
(git log --oneline -n 20          > "$OUT/git_log.txt"     2>&1) || true

# 3) 設定ファイルをコピー（存在するものだけ）
for f in package.json tsconfig.json jsconfig.json next.config.js next.config.mjs next.config.ts tailwind.config.js tailwind.config.ts postcss.config.js .gitignore; do
  [ -f "$f" ] && cp "$f" "$OUT/"
done
[ -f pnpm-lock.yaml ]      && cp pnpm-lock.yaml      "$OUT/" || true
[ -f yarn.lock ]           && cp yarn.lock           "$OUT/" || true
[ -f package-lock.json ]   && cp package-lock.json   "$OUT/" || true

# 4) プロジェクトの概観（重いディレクトリは除外）
if command -v tree >/dev/null 2>&1; then
  tree -a -I 'node_modules|.next|.git|.vercel|dist|build|coverage' -L 3 > "$OUT/tree.txt"
else
  find . -maxdepth 3 \( -path ./node_modules -o -path ./.next -o -path ./.git -o -path ./.vercel -o -path ./dist -o -path ./build -o -path ./coverage \) -prune -o -type f -print | sort > "$OUT/tree.txt"
fi

# 5) エイリアス/問題ファイルの痕跡
if command -v rg >/dev/null 2>&1; then
  rg -n --no-heading 'from\s+"@/' src || true > "$OUT/alias_usages.txt"
else
  grep -R -n 'from\W\+"@/' src 2>/dev/null || true > "$OUT/alias_usages.txt"
fi
[ -d src/lib ] && ls -la src/lib > "$OUT/src-lib-ls.txt" || echo "src/lib not found" > "$OUT/src-lib-ls.txt"
[ -f src/lib/utils.ts ] && sed -n '1,200p' src/lib/utils.ts > "$OUT/snippets/src-lib-utils.ts.txt" || echo "src/lib/utils.ts not found" > "$OUT/snippets/src-lib-utils.ts.txt"
grep -R -n "@/lib/utils" src 2>/dev/null | cut -d: -f1 | sort -u | while read -r f; do
  echo "---- $f ----" >> "$OUT/snippets/offending_files.txt"
  sed -n '1,160p' "$f" >> "$OUT/snippets/offending_files.txt" 2>/dev/null || true
  echo >> "$OUT/snippets/offending_files.txt"
done

# 6) ビルドログ（失敗しても続行）
if [ "$PM" = "pnpm" ]; then
  (pnpm build || true) 2>&1 | tee "$OUT/build.log" >/dev/null
elif [ "$PM" = "yarn" ]; then
  (yarn build || true) 2>&1 | tee "$OUT/build.log" >/dev/null
else
  (npm run build || true) 2>&1 | tee "$OUT/build.log" >/dev/null
fi

# 7) 注意書き（何を含めないか明示）
cat > "$OUT/_note_no_secrets.txt" <<'EOF'
This archive intentionally excludes secrets and heavy artifacts:
- .env* files
- *client_secret*.json, *_credentials.json
- node_modules, .next, .git, .vercel
EOF

# 8) ZIP化（zip 無ければ tar.gz）
ARCHIVE="$OUT.zip"
if command -v zip >/dev/null 2>&1; then
  zip -rq "$ARCHIVE" "$OUT"
else
  tar -czf "$OUT.tgz" "$OUT"
  ARCHIVE="$OUT.tgz"
fi

echo "Created archive: $(pwd)/$ARCHIVE"
