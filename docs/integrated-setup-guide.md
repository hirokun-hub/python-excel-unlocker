# 統合セットアップガイド

## 概要

Excel Unlocker 社内展開用統合セットアップスクリプトは、初心者向けの対話式セットアップ、進捗表示、エラー時サポート機能を提供する包括的な環境構築ツールです。

## 主な機能

### 🎯 初心者向け機能
- **対話式セットアップ**: 技術知識不要の質問形式設定
- **リアルタイム進捗表示**: プログレスバーによる視覚的進捗確認
- **詳細エラーサポート**: 問題発生時の具体的解決方法提示
- **自動リカバリガイド**: エラー種別に応じた復旧手順

### 🚀 自動化機能
- **設定ファイル管理**: JSON設定の自動生成・検証
- **環境変数生成**: 環境別の自動環境変数設定
- **AWS リソース作成**: S3バケット・Lambda・API Gateway自動構築
- **フロントエンド構築**: Next.js依存関係・ビルド自動実行
- **Vercelデプロイ**: オプションでのVercel自動デプロイ

### 🔧 診断・サポート機能
- **前提条件チェック**: 必要ツールの自動検出・案内
- **設定検証**: 設定ファイルの構文・内容検証
- **動作確認テスト**: デプロイ後の自動動作確認
- **包括的ログ**: 詳細な実行ログとトラブルシューティング情報

## 前提条件

### 🔐 AWS IAMユーザー設定（重要）

統合セットアップスクリプトを実行する前に、**プロジェクト専用のIAMユーザー**を作成することを強く推奨します。

#### **なぜ専用IAMユーザーが必要か**
- **セキュリティ**: 最小権限の原則に従った安全な運用
- **管理性**: Excel Unlocker専用の独立した権限管理
- **監査性**: 明確な操作ログと追跡
- **将来性**: プロジェクト終了時の簡単な清理

#### **IAMユーザー作成手順**
1. **AWSマネジメントコンソール**にルートアカウント（または管理者権限ユーザー）でログイン
2. **IAM** → **Users** → **Create user**
3. ユーザー名: `excel-unlocker-deploy-user`（推奨）
4. **Programmatic access**を選択（コンソールアクセスは不要）
5. **Attach policies directly** → **Create policy**
6. 以下の**修正版最小権限ポリシー**を使用

#### **修正版最小権限ポリシー（セキュリティ警告対応済み）**
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "ExcelUnlockerS3Access",
            "Effect": "Allow",
            "Action": [
                "s3:CreateBucket",
                "s3:DeleteBucket",
                "s3:GetBucketLocation",
                "s3:ListBucket",
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject",
                "s3:PutBucketCORS",
                "s3:PutBucketPublicAccessBlock",
                "s3:GetBucketCORS",
                "s3:GetBucketPublicAccessBlock"
            ],
            "Resource": [
                "arn:aws:s3:::excel-unlock-*",
                "arn:aws:s3:::excel-unlock-*/*"
            ]
        },
        {
            "Sid": "ExcelUnlockerLambdaAccess",
            "Effect": "Allow",
            "Action": [
                "lambda:CreateFunction",
                "lambda:UpdateFunctionCode",
                "lambda:UpdateFunctionConfiguration",
                "lambda:DeleteFunction",
                "lambda:GetFunction",
                "lambda:ListFunctions",
                "lambda:InvokeFunction",
                "lambda:AddPermission",
                "lambda:RemovePermission",
                "lambda:TagResource",
                "lambda:UntagResource"
            ],
            "Resource": "arn:aws:lambda:*:*:function:excel-unlocker-*"
        },
        {
            "Sid": "ExcelUnlockerAPIGatewayAccess",
            "Effect": "Allow",
            "Action": [
                "apigateway:GET",
                "apigateway:POST",
                "apigateway:PUT",
                "apigateway:DELETE",
                "apigateway:PATCH"
            ],
            "Resource": [
                "arn:aws:apigateway:*::/restapis",
                "arn:aws:apigateway:*::/restapis/*"
            ]
        },
        {
            "Sid": "ExcelUnlockerCloudFormationAccess",
            "Effect": "Allow",
            "Action": [
                "cloudformation:CreateStack",
                "cloudformation:UpdateStack",
                "cloudformation:DeleteStack",
                "cloudformation:DescribeStacks",
                "cloudformation:DescribeStackEvents",
                "cloudformation:DescribeStackResources",
                "cloudformation:DescribeStackResource",
                "cloudformation:GetTemplate",
                "cloudformation:ValidateTemplate",
                "cloudformation:ListStackResources"
            ],
            "Resource": "arn:aws:cloudformation:*:*:stack/excel-unlocker-*/*"
        },
        {
            "Sid": "ExcelUnlockerIAMRoleAccess",
            "Effect": "Allow",
            "Action": [
                "iam:CreateRole",
                "iam:DeleteRole",
                "iam:GetRole",
                "iam:UpdateRole",
                "iam:AttachRolePolicy",
                "iam:DetachRolePolicy",
                "iam:PutRolePolicy",
                "iam:DeleteRolePolicy",
                "iam:GetRolePolicy",
                "iam:ListRolePolicies",
                "iam:ListAttachedRolePolicies",
                "iam:TagRole",
                "iam:UntagRole"
            ],
            "Resource": "arn:aws:iam::*:role/excel-unlocker-*"
        },
        {
            "Sid": "ExcelUnlockerIAMPassRole",
            "Effect": "Allow",
            "Action": "iam:PassRole",
            "Resource": "arn:aws:iam::*:role/excel-unlocker-*",
            "Condition": {
                "StringEquals": {
                    "iam:PassedToService": [
                        "lambda.amazonaws.com",
                        "apigateway.amazonaws.com"
                    ]
                }
            }
        },
        {
            "Sid": "ExcelUnlockerLogsAccess",
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents",
                "logs:DescribeLogGroups",
                "logs:DescribeLogStreams"
            ],
            "Resource": "arn:aws:logs:*:*:log-group:/aws/lambda/excel-unlocker-*"
        }
    ]
}
```

7. ポリシー名: `ExcelUnlockerDeployPolicy`
8. ユーザーを作成し、**Access Key ID**と**Secret Access Key**を安全に保存
9. AWS CLIで認証情報を設定: `aws configure`

#### **既存IAMユーザーがある場合**
既存のIAMユーザーでも使用可能ですが、**プロジェクト専用ユーザーの新規作成を推奨**します：
- セキュリティ上のメリット（最小権限、権限分離）
- 運用上のメリット（独立管理、簡単な清理）
- 監査上のメリット（明確な操作追跡）

## クイックスタート

### 1. 簡易セットアップ（推奨）

```bash
# 初心者向け・ワンクリック起動
./setup-easy.sh
```

### 2. 統合セットアップ（直接実行）

```bash
# 対話式セットアップ
./scripts/setup-integrated-deployment.sh

# 開発環境の自動セットアップ
./scripts/setup-integrated-deployment.sh --environment development

# 本番環境 + Vercelデプロイ
./scripts/setup-integrated-deployment.sh --environment production --deploy-vercel
```

### 3. 事前診断（推奨）

```bash
# セットアップ前の環境診断
python3 scripts/setup-diagnostics.py

# 診断レポート出力
python3 scripts/setup-diagnostics.py --output diagnosis-report.json
```

### 4. Vercel必須シークレット3点の取得

#### **前提条件: Vercel Hobbyアカウント + チーム構成**

このスクリプトは以下のVercelアカウント構成を前提としています：
- **Vercel Hobbyアカウント**（無料プラン）
- **My Account内でTeam作成**
- **チーム配下にプロジェクト配置**

#### **必須シークレット3点**

GitHub ActionsでVercelデプロイするために以下が必要です：

1. **VERCEL_TOKEN**: 個人のAccess Token
2. **VERCEL_ORG_ID**: チーム運用時はTeam ID（`team_...`）
3. **VERCEL_PROJECT_ID**: プロジェクトID（`prj_...`）

#### **取得方法**

**方法1: .vercel/project.jsonから取得（推奨）**

```bash
# Vercel CLIのインストール
npm install -g vercel

# ログイン
vercel login

# プロジェクトをリンク（frontendディレクトリで実行）
cd frontend
vercel link
# → チームを選択
# → 既存プロジェクトを選択

# 設定ファイルから値を確認
cat .vercel/project.json
# 出力例:
# {
#   "orgId": "team_abc123def456789",
#   "projectId": "prj_xyz789abc123def"
# }
```

**方法2: Vercelダッシュボードから取得**

```bash
# VERCEL_TOKEN: https://vercel.com/account/tokens で作成
# VERCEL_ORG_ID: https://vercel.com/teams/[team-slug]/settings の Team ID
# VERCEL_PROJECT_ID: https://vercel.com/[team-slug]/[project]/settings の Project ID
```

#### **よくある間違い**

- **User ID vs Team ID**: プロジェクトが属する側のIDを使用
  - チーム配下 → Team ID（`team_...`）
  - 個人配下 → Your ID（ランダム文字列）
- **二重デプロイ**: GitHub連携を無効化（Project Settings → Git → Disconnect）

```bash
# 診断レポート出力
python3 scripts/setup-diagnostics.py --output setup-diagnosis.json
```

## 詳細な使用方法

### コマンドオプション

```bash
./scripts/setup-integrated-deployment.sh [オプション]

オプション:
  --environment ENV    対象環境 (development|staging|production)
  --deploy-vercel      Vercelデプロイを実行
  --skip-tests         動作確認テストをスキップ
  --non-interactive    非対話モード（上級者向け）
  --help, -h           ヘルプを表示
```

### 対話式セットアップフロー

1. **環境選択**
   - development（開発環境）
   - staging（ステージング環境）
   - production（本番環境）

2. **デプロイオプション**
   - Vercelデプロイの有無
   - 動作確認テストの実行有無

3. **設定ファイル作成・編集**
   - 自動テンプレート生成
   - 必要な機密情報の入力案内

4. **自動セットアップ実行**
   - 進捗バー表示
   - リアルタイム状況更新

### 設定ファイル構造

統合セットアップスクリプトは `setup-config.json` を使用します：

```json
{
  "version": "1.0.0",
  "environments": {
    "development": {
      "aws": {
        "region": "ap-northeast-1",
        "s3": {
          "bucketName": "excel-unlock-dev-bucket",
          "corsOrigin": "http://localhost:3000"
        },
        "lambda": {
          "stackName": "excel-unlocker-api-dev"
        }
      },
      "google": {
        "clientId": "YOUR_GOOGLE_CLIENT_ID",
        "clientSecret": "YOUR_GOOGLE_CLIENT_SECRET"
      },
      "security": {
        "allowedUsers": ["user@example.com"],
        "jwtSecret": "YOUR_JWT_SECRET"
      }
    }
  }
}
```

## セットアップステップ詳細

### Step 1: 前提条件チェック
- Python 3.x の確認
- AWS CLI の確認・認証テスト
- SAM CLI の確認
- Node.js & npm の確認
- Git の確認

### Step 2: 対話式設定収集
- 環境選択（development/staging/production）
- Vercelデプロイオプション
- テスト実行オプション

### Step 3: 設定ファイル初期化・検証
- `setup-config.json` の自動生成
- JSON Schema による設定検証
- 機密情報プレースホルダーチェック

### Step 4: 環境セットアップ
- 環境変数の生成（`.env.{environment}`）
- AWS認証確認
- 設定値の環境変数読み込み

### Step 5: S3バケット作成
- 環境別S3バケットの作成
- パブリックアクセスブロック設定
- セキュリティポリシー適用

### Step 6: バックエンドデプロイ
- SAM アプリケーションビルド
- CloudFormation スタックデプロイ
- API Gateway URL取得・設定

### Step 7: フロントエンドセットアップ
- npm 依存関係インストール
- 環境変数ファイル設定
- Next.js ビルドテスト実行

### Step 8: 動作確認・バックアップ・完了
- API エンドポイント疎通確認
- 統合テスト実行（オプション）
- 設定ファイルバックアップ
- 完了サマリー表示

## エラーハンドリング・リカバリ

### 自動エラー検出

統合セットアップスクリプトは以下のエラーを自動検出し、解決方法を提示します：

- **設定ファイルエラー**: JSON形式・必須項目・プレースホルダー
- **AWS認証エラー**: 認証情報・権限・リージョン設定
- **依存関係エラー**: Python・Node.js パッケージ
- **ビルドエラー**: SAM・Next.js ビルド失敗
- **デプロイエラー**: CloudFormation・Vercel デプロイ失敗

### リカバリガイド例

#### AWS認証エラー
```
❌ AWS認証に失敗しました

🔧 解決方法:
  1. AWS設定を確認: aws configure list
  2. AWS認証情報を設定: aws configure
  3. 認証テスト: aws sts get-caller-identity
  4. 再実行: ./scripts/setup-integrated-deployment.sh
```

#### 設定ファイル検証エラー
```
❌ 設定ファイルの検証に失敗しました

🔧 解決方法:
  1. 設定ファイルを確認: cat setup-config.json
  2. 設定例を参照: docs/beginner-complete-setup-guide.md
  3. JSON形式を確認: python3 -m json.tool setup-config.json
  4. 再実行: ./scripts/setup-integrated-deployment.sh
```

## 診断ツール

### 事前診断

セットアップ前に環境診断を実行することを推奨します：

```bash
# 完全診断
python3 scripts/setup-diagnostics.py

# 基本チェックのみ
python3 scripts/setup-diagnostics.py --quiet

# 診断レポート出力
python3 scripts/setup-diagnostics.py --output diagnosis-report.json
```

### 診断項目

- **前提条件**: 必要ツールのインストール状況
- **AWS設定**: 認証情報・権限・接続確認
- **プロジェクト構造**: 必須ファイル・ディレクトリ確認
- **設定ファイル**: JSON形式・必須項目・プレースホルダー
- **依存関係**: Python・Node.js パッケージ確認
- **ネットワーク接続**: 重要エンドポイントへの接続確認

## 進捗表示・ログ

### リアルタイム進捗表示

```
[75%] [██████████████████████████████████████░░░░░░░░░░░░░░] フロントエンドセットアップ
```

### 詳細ログ

すべての実行内容は `setup-integrated-deployment.log` に記録されます：

```
=== Excel Unlocker 社内展開用統合セットアップ開始: 2025-01-19 14:30:00 ===
引数: --environment development
=== セットアップ開始 ===

[INFO] 前提条件をチェックしています...
[SUCCESS] 前提条件のチェックが完了しました
...
```

## 完了後の確認事項

### 自動生成ファイル

セットアップ完了後、以下のファイルが生成されます：

```
├── setup-config.json              # 設定ファイル
├── .env.development               # 環境変数（開発環境）
├── setup-integrated-deployment.log # 実行ログ
├── config-backup/                 # 設定バックアップ
└── frontend/.env.local            # フロントエンド環境変数
```

### 動作確認手順

1. **ローカル開発環境**
   ```bash
   cd frontend && npm run dev
   # http://localhost:3000 にアクセス
   ```

2. **API エンドポイント**
   ```bash
   curl ${API_GATEWAY_URL}/health
   ```

3. **Google OAuth**
   - テストユーザーでログイン
   - 認証フローの確認

4. **ファイル解除機能**
   - パスワード付きExcelファイルのアップロード
   - 解除・ダウンロード機能の確認

## トラブルシューティング

### よくある問題

#### 1. Python依存関係エラー
```bash
# 解決方法
pip3 install -r scripts/requirements.txt
```

#### 2. AWS権限不足
```bash
# IAMポリシー確認
aws iam list-attached-user-policies --user-name your-username
```

#### 3. Node.js バージョン不適合
```bash
# Node.js バージョン確認・更新
node --version
# 推奨: Node.js 18.x 以上
```

#### 4. S3バケット名重複
```bash
# 設定ファイルでバケット名を変更
# bucketName: "excel-unlock-dev-bucket-unique-suffix"
```

### 詳細トラブルシューティング

問題が解決しない場合は、以下のドキュメントを参照してください：

- [トラブルシューティング診断フローチャート](troubleshooting-flowchart.md)
- [よくある質問（FAQ）](beginner-faq.md)
- [トラブルシューティング診断ガイド](troubleshooting-diagnostic-guide.md)

## 高度な使用方法

### 非対話モード

上級者向けの非対話モードでの実行：

```bash
# 環境変数で設定を指定
export SETUP_ENVIRONMENT=production
export SETUP_DEPLOY_VERCEL=true
export SETUP_SKIP_TESTS=false

# 非対話モードで実行
./scripts/setup-integrated-deployment.sh --non-interactive
```

### カスタム設定

設定ファイルを事前に準備して実行：

```bash
# 1. 設定ファイルを手動作成・編集
cp setup-config.example.json setup-config.json
# setup-config.json を編集

# 2. 設定検証
python3 scripts/config_manager.py validate

# 3. 統合セットアップ実行
./scripts/setup-integrated-deployment.sh --non-interactive
```

### バッチ処理

複数環境の一括セットアップ：

```bash
#!/bin/bash
# 複数環境セットアップスクリプト例

environments=("development" "staging" "production")

for env in "${environments[@]}"; do
    echo "Setting up $env environment..."
    ./scripts/setup-integrated-deployment.sh \
        --environment "$env" \
        --non-interactive \
        --skip-tests
done
```

## セキュリティ考慮事項

### 機密情報の保護

- **設定ファイル**: `setup-config.json` は `.gitignore` で除外
- **環境変数**: `.env.*` ファイルは自動的に除外
- **ログファイル**: 機密情報はマスクして記録
- **バックアップ**: 設定バックアップのアクセス権限制限

### 推奨セキュリティ設定

```bash
# ファイル権限の設定
chmod 600 setup-config.json
chmod 600 .env.*
chmod 700 config-backup/
```

## パフォーマンス・最適化

### セットアップ時間の最適化

- **並列処理**: 可能な処理の並列実行
- **キャッシュ活用**: npm・pip キャッシュの活用
- **テストスキップ**: 開発時のテスト省略オプション
- **増分デプロイ**: 変更部分のみのデプロイ

### リソース使用量

- **メモリ使用量**: 約500MB（ピーク時）
- **ディスク使用量**: 約2GB（依存関係含む）
- **ネットワーク**: 約100MB（初回ダウンロード）
- **実行時間**: 15-30分（環境・ネットワークによる）

## まとめ

統合セットアップスクリプトにより、以下の利点が得られます：

### 🎯 初心者向け
- **技術知識不要**: 対話式で簡単セットアップ
- **詳細サポート**: エラー時の具体的解決方法
- **視覚的進捗**: プログレスバーによる安心感
- **包括的ドキュメント**: 豊富なヘルプ・ガイド

### 🚀 効率化
- **自動化**: 手作業の最小化
- **一貫性**: 環境間の設定統一
- **再現性**: 同じ手順での確実な構築
- **時短**: 従来60分→15分の大幅短縮

### 🔧 運用性
- **診断機能**: 問題の早期発見
- **ログ記録**: 詳細な実行履歴
- **バックアップ**: 設定の安全な保管
- **リカバリ**: 問題時の迅速復旧

統合セットアップスクリプトを使用することで、技術的な前提知識がない社内メンバーでも、安全かつ確実にExcel Unlockerの環境構築を行うことができます。

---

**関連ドキュメント:**
- [ドキュメント索引](index.md)
- [初心者向け完全セットアップガイド](beginner-complete-setup-guide.md)
- [設定情報管理システムガイド](config-management-guide.md)
- [よくある質問（FAQ）](beginner-faq.md)