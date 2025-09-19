# GitHub OIDC移行ガイド

## 概要

このドキュメントは、GitHub ActionsでのAWS認証を長期アクセスキーからOIDC（OpenID Connect）による短期クレデンシャルに移行する手順を説明します。

## 🚨 セキュリティ上の重要性

### 従来の問題点
- **長期アクセスキー**: AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEYが漏洩すると永続的なリスク
- **権限管理の困難**: キーローテーションが手動で煩雑
- **監査の複雑さ**: どのワークフローがどのキーを使用しているか追跡困難

### OIDC移行後の利点
- **短期クレデンシャル**: 一時的なトークンで自動失効
- **細かい権限制御**: リポジトリ・ブランチ単位での権限設定
- **監査の簡素化**: CloudTrailでの追跡が容易
- **キー管理不要**: GitHub側で自動管理

## 移行手順

### Step 1: AWS側の設定

#### 1.1 自動設定スクリプトの実行

```bash
# リポジトリルートで実行
./scripts/setup-github-oidc.sh
```

このスクリプトは以下を自動実行します：
- GitHub OIDCプロバイダーの作成
- IAMポリシーの作成（最小権限）
- IAMロールの作成（信頼関係設定）
- ポリシーのロールへのアタッチ

#### 1.2 手動設定（スクリプトが使用できない場合）

**OIDCプロバイダーの作成:**
```bash
# GitHub OIDCプロバイダーの証明書フィンガープリント取得
THUMBPRINT=$(echo | openssl s_client -servername token.actions.githubusercontent.com -connect token.actions.githubusercontent.com:443 2>/dev/null | openssl x509 -fingerprint -noout -sha1 | sed 's/://g' | cut -d= -f2)

# OIDCプロバイダー作成
aws iam create-open-id-connect-provider \
    --url https://token.actions.githubusercontent.com \
    --client-id-list sts.amazonaws.com \
    --thumbprint-list $THUMBPRINT
```

**IAMロールの作成:**
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Federated": "arn:aws:iam::ACCOUNT-ID:oidc-provider/token.actions.githubusercontent.com"
            },
            "Action": "sts:AssumeRoleWithWebIdentity",
            "Condition": {
                "StringEquals": {
                    "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
                },
                "StringLike": {
                    "token.actions.githubusercontent.com:sub": "repo:hironomac2025/excel-password-remover:*"
                }
            }
        }
    ]
}
```

### Step 2: GitHub Secretsの設定

#### 2.1 新しいSecretの追加

1. GitHubリポジトリの **Settings** > **Secrets and variables** > **Actions** に移動
2. **New repository secret** をクリック
3. 以下のSecretを追加：

| Name | Value | 説明 |
|------|-------|------|
| `AWS_GITHUB_ACTIONS_ROLE_ARN` | `arn:aws:iam::ACCOUNT-ID:role/GitHubActionsRole` | OIDC用IAMロールのARN |

#### 2.2 古いSecretsの削除

⚠️ **重要**: 以下のSecretsを削除してください：
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`

### Step 3: ワークフローの確認

#### 3.1 OIDC設定の確認

既存のワークフローファイルで以下の設定が含まれていることを確認：

```yaml
# 必要な権限
permissions:
  id-token: write   # OIDC認証に必要
  contents: read    # リポジトリ内容の読み取り

jobs:
  deploy:
    steps:
      - name: Configure AWS credentials (OIDC)
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_GITHUB_ACTIONS_ROLE_ARN }}
          role-session-name: GitHubActions-Deploy-${{ github.run_id }}
          aws-region: ap-northeast-1
```

#### 3.2 対象ワークフローファイル

以下のファイルがOIDC対応済みです：
- `.github/workflows/deploy-backend.yml`
- `.github/workflows/deploy-full-stack.yml`

## 動作確認

### テスト手順

1. **開発環境でのテスト**:
   ```bash
   # GitHub Actionsでワークフローを手動実行
   # Repository > Actions > Deploy Backend to AWS > Run workflow
   # Environment: development を選択して実行
   ```

2. **ログの確認**:
   ```
   ✅ 成功例:
   Configure AWS credentials (OIDC)
   Assuming role with OIDC
   Role assumed successfully
   
   ❌ 失敗例:
   Error: Could not assume role with OIDC
   ```

3. **CloudTrailでの確認**:
   - AWS CloudTrail > Event history
   - User name: `GitHubActions-Deploy-*` で検索
   - AssumeRoleWithWebIdentity イベントの確認

## トラブルシューティング

### よくあるエラーと対処法

#### 1. "Could not assume role with OIDC"

**原因**: IAMロールの信頼関係設定が不正

**対処法**:
```bash
# 信頼ポリシーの確認
aws iam get-role --role-name GitHubActionsRole --query 'Role.AssumeRolePolicyDocument'

# リポジトリ名の確認（大文字小文字、ハイフン等）
echo "repo:hironomac2025/excel-password-remover:*"
```

#### 2. "Access denied" エラー

**原因**: IAMポリシーの権限不足

**対処法**:
```bash
# ポリシーの確認
aws iam list-attached-role-policies --role-name GitHubActionsRole

# 必要に応じてポリシーの更新
./scripts/setup-github-oidc.sh  # 再実行で更新
```

#### 3. "Invalid identity token"

**原因**: GitHub側のOIDCトークン設定問題

**対処法**:
- ワークフローファイルの `permissions` セクション確認
- `id-token: write` が設定されているか確認

### デバッグ用コマンド

```bash
# OIDCプロバイダーの確認
aws iam list-open-id-connect-providers

# ロールの詳細確認
aws iam get-role --role-name GitHubActionsRole

# ポリシーの確認
aws iam get-policy --policy-arn arn:aws:iam::ACCOUNT-ID:policy/GitHubActionsPolicy
```

## セキュリティベストプラクティス

### 1. 最小権限の原則

IAMポリシーは必要最小限の権限のみを付与：
- CloudFormation操作権限
- Lambda関数管理権限
- S3バケット操作権限（特定バケットのみ）
- API Gateway操作権限

### 2. 条件付きアクセス

信頼ポリシーで以下を制限：
- 特定リポジトリからのアクセスのみ許可
- GitHub OIDCプロバイダーからのアクセスのみ許可

### 3. 監査とモニタリング

- CloudTrailでのAPI呼び出し監視
- IAM Access Analyzerでの権限分析
- 定期的な権限レビュー

## 移行完了チェックリスト

- [ ] AWS OIDCプロバイダーの作成完了
- [ ] IAMロールとポリシーの作成完了
- [ ] GitHub Secretsの設定完了
- [ ] 古いAWSキーの削除完了
- [ ] ワークフローの動作確認完了
- [ ] CloudTrailでのOIDC認証確認完了
- [ ] 開発環境でのテスト完了
- [ ] ステージング環境でのテスト完了

## 参考資料

- [GitHub Actions: Configuring OpenID Connect in Amazon Web Services](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services)
- [AWS IAM: Creating OpenID Connect identity providers](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_create_oidc.html)
- [aws-actions/configure-aws-credentials](https://github.com/aws-actions/configure-aws-credentials)

---

**注意**: 本番環境への適用前に、必ず開発環境・ステージング環境での十分なテストを実施してください。