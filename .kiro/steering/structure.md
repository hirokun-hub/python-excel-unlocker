# プロジェクト構成

## ルートディレクトリ概要
```
├── backend/                    # AWS Lambda（Python）ソースとテスト
├── frontend/                   # Next.js (App Router) フロントエンド
├── docs/                       # 各種ガイド・トラブルシューティング
├── scripts/                    # セットアップ・自動化・検証スクリプト群
├── tests/                      # 統合テスト・パフォーマンステスト
├── .github/workflows/          # GitHub Actions ワークフロー定義
├── .kiro/                      # 要件・設計・タスク・ステアリング文書
├── logs/ , reports/ , events/  # 運用ログ類（コミット対象外想定）
├── samconfig.toml , template.yaml
├── setup-config*.json , secrets/  # 設定テンプレートと機密情報置き場
└── README.md ほか
```

## フロントエンド (`frontend/`)
```
├── src/
│   ├── app/                    # ページ・API Route（Next.js App Router）
│   ├── components/             # UI / 機能コンポーネント（shadcn/ui ベース）
│   ├── lib/, utils/, types/    # クライアントロジック・型定義
│   └── auth.ts                 # Auth.js (Google OAuth) 設定
├── __tests__/                  # Jest ユニットテスト
├── e2e/                        # Playwright E2E テスト
└── public/                     # 静的アセット
```

## バックエンド (`backend/`)
```
├── src/
│   ├── unlock.py, get_upload_url.py  # Lambda エントリポイント
│   ├── auth_utils.py, file_security.py などのユーティリティ
│   └── requirements.txt               # Python 依存関係
├── tests/unit/                        # pytest ユニットテスト
└── samconfig.toml に対応する設定はルートに配置
```

## ドキュメント (`docs/`)
- `github-secrets-setup-guide.md` : 必須環境変数の設定手順
- `integrated-setup-guide.md` : セットアップ全体像
- `deployment-guide.md` : デプロイ運用ガイド
- `python-environment-troubleshooting.md` / `troubleshooting-diagnostic-guide.md` : 問題解決
- `index.md` : 初心者向けトップランディング
- `runbook/` : 障害時対応手順

## スクリプト (`scripts/`)
- `setup-*.sh` : AWS / Vercel / Secrets 等のセットアップ
- `task_manager.py`, `task-aliases.sh` : タスク自動化（完了マーク・コミット）
- `normalize_vercel_project.py` : Vercel 設定補助
- `validate-env-vars.py` : 環境変数チェック
- `deploy-*.sh` : デプロイ支援

## GitHub Actions (`.github/workflows/`)
- `deploy-backend.yml` / `deploy-aws.yml` : バックエンド CI/CD
- `deploy-frontend.yml` / `deploy-vercel-reusable.yml` : フロントエンド CI/CD
- `build-frontend.yml`, `validate-frontend.yml`, `e2e-test-frontend.yml` : 再利用ワークフロー
- `deploy-full-stack.yml` : 手動フルスタックデプロイ

## 命名規則
- **TypeScript / React コンポーネント**: PascalCase (`ExcelUnlocker.tsx`)
- **ユーティリティ・フック**: camelCase (`useUpload.ts`, `api.ts`)
- **テスト**: `*.test.ts(x)` / `*.spec.ts`
- **ドキュメント**: ASCII の kebab-case (`github-secrets-setup-guide.md`)
- **シェル / Python スクリプト**: kebab-case (`setup-python-env.sh`), snake_case (`task_manager.py`)

## Git 管理上の注意
- `.gitignore` に従い `node_modules/`, `.next/`, `.aws-sam/`, `*.env*`, `secrets/` 等はコミットしない
- `setup-config.json` など機密ファイルはテンプレート (`setup-config.example.json`) 経由で共有
- タスク自動化機能を利用する場合は `task-complete-dry` で内容確認してから実行

## AI 解析関連
- `.kiro/` 配下に要件・設計・タスク・ステアリング文書を配置
- 分析系アーティファクトは `analysis_data/` が存在する場合に利用（必要時に生成）
