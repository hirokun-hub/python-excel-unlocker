# プロジェクト構成

## ルートレベルの構成
```
├── frontend/           # Next.js Webアプリケーション
├── backend/            # AWS Lambda関数のソースコード
├── docs/               # プロジェクトドキュメント
├── scripts/            # ユーティリティスクリプトとレガシーコード
├── tests/              # 統合テストとパフォーマンステスト
├── template.yaml       # AWS SAMテンプレート
├── samconfig.toml      # SAMデプロイ設定
├── .aws-sam/           # SAMビルド成果物とドキュメント
└── analysis_data/      # AI分析用データ（GitHub Actions生成）
```

## フロントエンド構成 (`frontend/`)
```
├── src/
│   ├── app/            # Next.js App RouterのページとAPIルート
│   │   ├── api/        # APIルートハンドラー（auth, debug, drive）
│   │   ├── page.tsx    # メインアプリケーションページ
│   │   └── layout.tsx  # ルートレイアウトコンポーネント
│   ├── components/     # Reactコンポーネント
│   │   ├── ui/         # shadcn/uiコンポーネント
│   │   └── *.tsx       # カスタムコンポーネント（FileUpload, FileResults等）
│   ├── lib/            # ユーティリティライブラリ
│   ├── types/          # TypeScript型定義
│   └── utils/          # ヘルパー関数
├── __tests__/          # ユニットテスト
├── e2e/                # Playwright E2Eテスト
└── public/             # 静的アセット
```

## バックエンド構成 (`backend/`)
```
├── src/
│   ├── main.py         # Lambdaハンドラーとコアロジック
│   └── requirements.txt # Python依存関係
└── tests/
    ├── unit/           # ユニットテスト
    └── conftest.py     # テスト設定
```

## ドキュメント構成 (`docs/`)
```
├── dev/                # 開発リソース
├── guides/             # ユーザーと開発者ガイド
├── how-to/             # ステップバイステップ手順
├── project/            # プロジェクト計画とアーキテクチャ
├── security/           # セキュリティドキュメント
└── 企画/               # 企画書（日本語）
```

## 命名規則

### ファイル
- **コンポーネント**: PascalCase（例：`FileUpload.tsx`, `DriveFolderPicker.tsx`）
- **ページ**: lowercase（例：`page.tsx`, `layout.tsx`）
- **ユーティリティ**: camelCase（例：`googleDrive.ts`, `utils.ts`）
- **テスト**: `*.test.tsx` または `*.spec.ts`
- **ドキュメント**: ASCII の kebab-case のみ（日本語・全角記号・アンダースコア禁止）（例：`aws-deploy-prep-guide.md`）

### ディレクトリ
- **コンポーネント**: 機能またはUIライブラリ別に整理（`ui/`, `components/`）
- **APIルート**: Next.js App Routerの規則に従う（`api/auth/[...nextauth]/`）
- **テスト**: ソース構造をミラーリング（`__tests__/components/`）

## AI分析用ディレクトリ (`analysis_data/`)
```
analysis_data/
├── runtime.json           # Node/Python/OSバージョン情報
├── todo-fixme.json        # 変更箇所のTODO/FIXME抽出
└── codeframes/            # JUnit失敗時のコードフレーム（±10行）
    ├── junit-fe.txt
    └── junit-be.txt
```

## 主要設定ファイル
- `components.json`: shadcn/ui設定
- `next.config.ts`: Next.js設定
- `tailwind.config.ts`: Tailwind CSS設定
- `tsconfig.json`: TypeScript設定
- `pytest.ini`: Pythonテスト設定
- `.env.local`: ローカル環境変数（フロントエンド）
- `.gitignore`: バージョン管理から除外するファイル・ディレクトリの指定

## Git管理の注意点

### 除外すべきファイル・ディレクトリ
- **環境変数ファイル**: `.env.local`, `.env.production.local`
- **依存関係**: `node_modules/`, `__pycache__/`
- **ビルド成果物**: `.next/`, `dist/`, `.aws-sam/`
- **IDE設定**: `.vscode/`, `.idea/`
- **ログファイル**: `*.log`
- **一時ファイル**: `*.tmp`, `.DS_Store`

### 機密情報の取り扱い
- **APIキー、パスワード、トークンは絶対にコミットしない**
- **AWSクレデンシャルファイルは除外する**
- **データベース接続文字列は環境変数で管理する**