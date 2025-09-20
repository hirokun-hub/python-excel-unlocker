# 統合セットアップスクリプト README

## 概要

Excel Unlocker 社内展開用統合セットアップスクリプトは、初心者向けの対話式セットアップ、進捗表示、エラー時サポート機能を提供する包括的な環境構築ツールです。

## ファイル構成

```
scripts/
├── setup-integrated-deployment.sh    # メイン統合セットアップスクリプト
├── setup-diagnostics.py             # 環境診断ツール
├── test-integrated-setup.sh         # テストスイート
├── README-integrated-setup.md       # このファイル
├── config_manager.py                # 設定管理システム
├── setup-config-manager.sh          # 設定管理ラッパー
└── setup-with-config-management.sh  # 既存統合スクリプト

プロジェクトルート/
├── setup-easy.sh                    # 簡易起動スクリプト
├── setup-config.example.json        # 設定ファイルテンプレート
├── config-schema.json               # 設定スキーマ
└── docs/
    └── integrated-setup-guide.md    # 詳細ガイド
```

## クイックスタート

### 1. 簡易セットアップ（推奨）

```bash
# プロジェクトルートで実行
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
# 環境診断
python3 scripts/setup-diagnostics.py

# テストスイート実行
./scripts/test-integrated-setup.sh
```

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

## コマンドリファレンス

### setup-integrated-deployment.sh

```bash
./scripts/setup-integrated-deployment.sh [オプション]

オプション:
  --environment ENV    対象環境 (development|staging|production)
  --deploy-vercel      Vercelデプロイを実行
  --skip-tests         動作確認テストをスキップ
  --non-interactive    非対話モード（上級者向け）
  --help, -h           ヘルプを表示

例:
  ./scripts/setup-integrated-deployment.sh                    # 対話式セットアップ
  ./scripts/setup-integrated-deployment.sh --environment development  # 開発環境
  ./scripts/setup-integrated-deployment.sh --environment production --deploy-vercel  # 本番環境
```

### setup-diagnostics.py

```bash
python3 scripts/setup-diagnostics.py [オプション]

オプション:
  --output, -o FILE    診断レポートの出力ファイル
  --quiet, -q          サマリーのみ表示

例:
  python3 scripts/setup-diagnostics.py                        # 完全診断
  python3 scripts/setup-diagnostics.py --quiet                # 基本チェックのみ
  python3 scripts/setup-diagnostics.py --output report.json   # レポート出力
```

### test-integrated-setup.sh

```bash
./scripts/test-integrated-setup.sh [オプション]

オプション:
  --verbose, -v        詳細ログを表示
  --quick, -q          クイックテスト（基本テストのみ）
  --help, -h           ヘルプを表示

例:
  ./scripts/test-integrated-setup.sh                          # 全テスト実行
  ./scripts/test-integrated-setup.sh --quick                  # クイックテスト
  ./scripts/test-integrated-setup.sh --verbose                # 詳細ログ付き
```

## セットアップフロー

### 1. 前提条件チェック
- Python 3.x の確認
- AWS CLI の確認・認証テスト
- SAM CLI の確認
- Node.js & npm の確認
- Git の確認
- **Vercel CLI の確認・ORG_ID取得**

#### Vercel組織ID取得（必須）

⚠️ **重要**: VERCEL_ORG_IDはWebダッシュボードから取得できません。

```bash
# Vercel CLIのインストール・ログイン
npm install -g vercel
vercel login

# 組織IDとプロジェクトIDの取得
vercel teams list
vercel projects list
```

### 2. 対話式設定収集
- 環境選択（development/staging/production）
- Vercelデプロイオプション
- テスト実行オプション

### 3. 設定ファイル初期化・検証
- `setup-config.json` の自動生成
- JSON Schema による設定検証
- 機密情報プレースホルダーチェック

### 4. 環境セットアップ
- 環境変数の生成（`.env.{environment}`）
- AWS認証確認
- 設定値の環境変数読み込み

### 5. AWS リソース作成
- 環境別S3バケットの作成
- パブリックアクセスブロック設定
- セキュリティポリシー適用

### 6. バックエンドデプロイ
- SAM アプリケーションビルド
- CloudFormation スタックデプロイ
- API Gateway URL取得・設定

### 7. フロントエンドセットアップ
- npm 依存関係インストール
- 環境変数ファイル設定
- Next.js ビルドテスト実行

### 8. 動作確認・バックアップ・完了
- API エンドポイント疎通確認
- 統合テスト実行（オプション）
- 設定ファイルバックアップ
- 完了サマリー表示

## エラーハンドリング

統合セットアップスクリプトは以下のエラーを自動検出し、解決方法を提示します：

### 設定ファイルエラー
- JSON形式エラー
- 必須項目不足
- プレースホルダー残存

### AWS認証エラー
- 認証情報不足
- 権限不足
- リージョン設定問題

### 依存関係エラー
- Python パッケージ不足
- Node.js パッケージ不足
- バージョン不適合

### ビルドエラー
- SAM ビルド失敗
- Next.js ビルド失敗
- 依存関係解決失敗

### デプロイエラー
- CloudFormation エラー
- Vercel デプロイ失敗
- ネットワーク接続問題

## 生成されるファイル

セットアップ完了後、以下のファイルが生成されます：

```
プロジェクトルート/
├── setup-config.json                    # 設定ファイル
├── .env.{environment}                   # 環境変数ファイル
├── setup-integrated-deployment.log     # 実行ログ
├── config-backup/                      # 設定バックアップ
│   └── YYYYMMDD_HHMMSS/
│       ├── setup-config.YYYYMMDD_HHMMSS.json
│       └── .env.{environment}
└── frontend/
    └── .env.local                      # フロントエンド環境変数
```

## トラブルシューティング

### よくある問題と解決方法

#### 1. Python依存関係エラー
```bash
# 解決方法
pip3 install -r scripts/requirements.txt
```

#### 2. AWS認証エラー
```bash
# AWS設定確認
aws configure list

# AWS認証情報設定
aws configure

# 認証テスト
aws sts get-caller-identity
```

#### 3. Node.js バージョン不適合
```bash
# Node.js バージョン確認
node --version

# 推奨: Node.js 18.x 以上
```

#### 4. S3バケット名重複
```bash
# 設定ファイルでバケット名を変更
# "bucketName": "excel-unlock-dev-bucket-unique-suffix"
```

#### 5. SAM CLI エラー
```bash
# SAM CLI バージョン確認
sam --version

# SAM CLI 更新
pip3 install --upgrade aws-sam-cli
```

### 詳細トラブルシューティング

問題が解決しない場合は、以下を確認してください：

1. **ログファイル**: `setup-integrated-deployment.log`
2. **診断実行**: `python3 scripts/setup-diagnostics.py`
3. **テスト実行**: `./scripts/test-integrated-setup.sh`
4. **ドキュメント**: `docs/integrated-setup-guide.md`

## 開発者向け情報

### スクリプト構造

```bash
setup-integrated-deployment.sh
├── show_banner()                    # バナー表示
├── check_prerequisites()           # 前提条件チェック
├── collect_interactive_settings()  # 対話式設定収集
├── initialize_and_validate_config() # 設定初期化・検証
├── setup_environment()             # 環境セットアップ
├── create_s3_bucket()              # S3バケット作成
├── deploy_backend()                # バックエンドデプロイ
├── setup_frontend()                # フロントエンドセットアップ
├── deploy_vercel()                 # Vercelデプロイ
├── run_verification_tests()        # 動作確認テスト
├── backup_configuration()          # 設定バックアップ
├── show_recovery_help()            # リカバリヘルプ
└── show_final_summary()            # 最終サマリー
```

### カスタマイズ

スクリプトをカスタマイズする場合は、以下の点に注意してください：

1. **エラーハンドリング**: `show_recovery_help()` 関数を更新
2. **進捗表示**: `show_progress_bar()` 関数を調整
3. **ログ出力**: ログレベルとフォーマットを統一
4. **設定検証**: 新しい設定項目の検証ロジック追加

### テスト追加

新しいテストを追加する場合：

```bash
# test-integrated-setup.sh に追加
test_new_feature() {
    log_step "新機能テスト"
    
    # テストロジック
    if [[ 条件 ]]; then
        log_success "新機能テスト完了"
        return 0
    else
        log_error "新機能テストに失敗"
        return 1
    fi
}

# メイン関数でテスト実行
run_test "新機能テスト" "test_new_feature" "新機能の動作確認"
```

## パフォーマンス

### 実行時間

- **診断**: 約30秒
- **設定初期化**: 約1分
- **AWS リソース作成**: 約5分
- **バックエンドデプロイ**: 約5分
- **フロントエンドセットアップ**: 約3分
- **動作確認テスト**: 約1分

**合計**: 約15-30分（環境・ネットワークによる）

### リソース使用量

- **メモリ**: 約500MB（ピーク時）
- **ディスク**: 約2GB（依存関係含む）
- **ネットワーク**: 約100MB（初回ダウンロード）

## セキュリティ

### AWS IAMユーザー設定（重要）

**プロジェクト専用のIAMユーザー作成を強く推奨します**：

#### **専用IAMユーザーのメリット**
- **セキュリティ**: 最小権限の原則に従った安全な運用
- **管理性**: Excel Unlocker専用の独立した権限管理
- **監査性**: 明確な操作ログと追跡
- **将来性**: プロジェクト終了時の簡単な清理

#### **推奨設定**
- **ユーザー名**: `excel-unlocker-deploy-user`
- **ポリシー名**: `ExcelUnlockerDeployPolicy`
- **アクセスタイプ**: Programmatic accessのみ

#### **セキュリティ警告対応済みポリシー**
統合セットアップスクリプトで使用するポリシーは、以下のセキュリティ警告を解決済みです：
- "Create SLR With Star In Action And Resource"
- "PassRole With Star In Action And Resource"

修正版ポリシーでは、PassRole権限を特定のAWSサービス（Lambda、API Gateway）のみに制限し、セキュリティを強化しています。

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

## 貢献・改善

### バグレポート

バグを発見した場合は、以下の情報を含めて報告してください：

1. **実行環境**: OS、Python、Node.js バージョン
2. **実行コマンド**: 実行したコマンドとオプション
3. **エラーメッセージ**: 完全なエラーメッセージ
4. **ログファイル**: `setup-integrated-deployment.log` の内容
5. **診断結果**: `python3 scripts/setup-diagnostics.py` の出力

### 機能改善提案

機能改善の提案は以下の観点で検討してください：

1. **初心者向け**: 技術知識のないユーザーでも使いやすいか
2. **自動化**: 手作業を減らせるか
3. **エラーハンドリング**: 問題発生時のサポートが充実しているか
4. **パフォーマンス**: 実行時間を短縮できるか
5. **セキュリティ**: 機密情報の保護が適切か

## ライセンス・著作権

このスクリプトは Excel Unlocker プロジェクトの一部として提供されます。
プロジェクトのライセンスに従って使用してください。

---

**関連ドキュメント:**
- [統合セットアップガイド](../docs/integrated-setup-guide.md)
- [設定情報管理システムガイド](../docs/config-management-guide.md)
- [初心者向け完全セットアップガイド](../docs/beginner-complete-setup-guide.md)
- [よくある質問（FAQ）](../docs/beginner-faq.md)