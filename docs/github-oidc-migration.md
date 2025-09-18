# GitHub OIDC化ガイド（長期AWSキー廃止）

## 概要

このドキュメントは、GitHub ActionsでのAWS認証を長期キー（AWS_ACCESS_KEY_ID/SECRET）からOIDC（OpenID Connect）による短期クレデンシャルに移行する手順を説明します。この移行により、AWSキー漏洩リスクを根本的に解決します。

## 移行の背景

### 従来の認証方式の問題点

1. **長期キーの漏洩リスク**: GitHub Secretsに保存されたAWSキーが漏洩する可能性
2. **キーローテーションの困難**: 手動でのキー更新が必要
3. **権限管理の複雑さ**: IAMユーザーベースの権限管理
4. **監査の困難**: どのワークフローがどのキーを使用したか追跡困難

### OIDC認証の利点

1. **短期クレデンシャル**: 一時的なトークンによる認証
2. **自動ローテーション**: トークンの自動期限切れ
3. **細かい権限制御**: リポジトリ・ブランチ単位での権限設定
4. **監査可能性**: CloudTrailでの詳細なアクセスログ

## 実装内容

### 1. AWS SAMテンプレートの変更

#### IAM OIDCプロバイダーの作成
```yaml
GitHubOIDCProvider:
  Type: AWS::IAM::OIDCIdentityProvider
  Properties:
    Url: https://token.actions.githubusercontent.com
    ClientIdList:
      - sts.amazonaws.com
    ThumbprintList:
      - 6938fd4d98bab03faadb97b34396831e3780aea1  # GitHub Actions
      - 1c58a3a8518e8759bf075b76b750d4f2df264fcd  # 予備
```

#### GitHub Actions用IAMロールの作成
```yaml
GitHubActionsRole:
  Type: AWS::IAM::Role
  Properties:
    RoleName: !Sub "GitHubActions-ExcelUnlocker-${Environment}"
    AssumeRolePolicyDocument:
      Version: '2012-10-17'
      Statement:
        - Effect: Allow
          Principal:
            Federated: !Ref GitHubOIDCProvider
          Action: sts:AssumeRoleWithWebIdentity
          Condition:
            StringEquals:
              "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
            StringLike:
              "token.actions.githubusercontent.com:sub": "repo:hirokun-hub/python-excel-unlocker:*"
```

### 2. GitHub Actionsワークフローの変更

#### 権限の追加
```yaml
# GitHub OIDC化：必要な権限を追加
permissions:
  id-token: write   # OIDC認証に必要
  contents: read    # リポジトリ内容の読み取り
```

#### AWS認証の変更
```yaml
# 変更前（長期キー）
- name: Configure AWS credentials
  uses: aws-actions/configure-aws-credentials@v4
  with:
    aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
    aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
    aws-region: ${{ env.AWS_REGION }}

# 変更後（OIDC）
- name: Configure AWS credentials (OIDC)
  uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: ${{ secrets.AWS_GITHUB_ACTIONS_ROLE_ARN }}
    role-session-name: GitHubActions-Backend-Deploy-${{ github.run_id }}
    aws-region: ${{ env.AWS_REGION }}
```

### 3. GitHub Secretsの更新

#### 削除するSecrets
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`

#### 追加するSecrets
- `AWS_GITHUB_ACTIONS_ROLE_ARN`: GitHub Actions用IAMロールのARN

## セキュリティ強化効果

### 1. キー漏洩リスクの根本的解決

#### 従来の問題
```bash
# GitHub Secretsに長期キーが保存
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
# → 漏洩すると永続的にAWSアクセス可能
```

#### OIDC後の改善
```bash
# 短期トークンによる認証
# トークンは1時間で自動期限切れ
# リポジトリ・ブランチが限定される
```

### 2. 細かい権限制御

#### リポジトリ限定
```yaml
Condition:
  StringLike:
    "token.actions.githubusercontent.com:sub": "repo:hirokun-hub/python-excel-unlocker:*"
```

#### ブランチ限定（オプション）
```yaml
Condition:
  StringLike:
    "token.actions.githubusercontent.com:sub": "repo:hirokun-hub/python-excel-unlocker:ref:refs/heads/main"
```

### 3. 監査可能性の向上

#### CloudTrailログ例
```json
{
  "eventTime": "2025-01-17T10:30:00Z",
  "eventName": "AssumeRoleWithWebIdentity",
  "sourceIPAddress": "140.82.112.0",
  "userAgent": "aws-actions/configure-aws-credentials",
  "requestParameters": {
    "roleArn": "arn:aws:iam::123456789012:role/GitHubActions-ExcelUnlocker-development",
    "roleSessionName": "GitHubActions-Backend-Deploy-12345",
    "webIdentityToken": "[REDACTED]"
  },
  "responseElements": {
    "assumedRoleUser": {
      "assumedRoleId": "AROAEXAMPLE:GitHubActions-Backend-Deploy-12345",
      "arn": "arn:aws:sts::123456789012:assumed-role/GitHubActions-ExcelUnlocker-development/GitHubActions-Backend-Deploy-12345"
    }
  }
}
```

## デプロイメント手順

### 1. AWS SAMテンプレートのデプロイ

```bash
# OIDCプロバイダーとロールを作成
sam build
sam deploy --config-env development

# 出力からロールARNを取得
aws cloudformation describe-stacks \
  --stack-name excel-unlocker-api-dev \
  --query 'Stacks[0].Outputs[?OutputKey==`GitHubActionsRoleArn`].OutputValue' \
  --output text
```

### 2. GitHub Secretsの設定

```bash
# GitHub CLIを使用してSecretsを設定
gh secret set AWS_GITHUB_ACTIONS_ROLE_ARN --body "arn:aws:iam::123456789012:role/GitHubActions-ExcelUnlocker-development"

# 古いSecretsを削除
gh secret delete AWS_ACCESS_KEY_ID
gh secret delete AWS_SECRET_ACCESS_KEY
```

### 3. ワークフローの動作確認

```bash
# テストデプロイを実行
gh workflow run deploy-backend.yml --ref main

# ログを確認
gh run list --workflow=deploy-backend.yml
gh run view [RUN_ID] --log
```

## トラブルシューティング

### よくある問題

#### 1. AssumeRole失敗
```
Error: Could not assume role with OIDC: Access denied
```

**原因と解決方法**:
- OIDCプロバイダーが正しく設定されていない
- IAMロールの信頼関係が正しくない
- リポジトリ名が一致していない

```yaml
# 信頼関係の確認
Condition:
  StringLike:
    "token.actions.githubusercontent.com:sub": "repo:YOUR_USERNAME/YOUR_REPO:*"
```

#### 2. 権限不足エラー
```
Error: User is not authorized to perform: cloudformation:CreateStack
```

**解決方法**:
- IAMロールに必要な権限を追加
- PowerUserAccessポリシーの確認

#### 3. OIDCプロバイダーが見つからない
```
Error: Invalid identity token
```

**解決方法**:
- OIDCプロバイダーのThumbprintを確認
- GitHubのThumbprintが変更されていないか確認

### デバッグ方法

#### 1. OIDC トークンの確認
```yaml
- name: Debug OIDC token
  run: |
    echo "GitHub Token Claims:"
    echo "Repository: ${{ github.repository }}"
    echo "Ref: ${{ github.ref }}"
    echo "SHA: ${{ github.sha }}"
    echo "Actor: ${{ github.actor }}"
```

#### 2. AssumeRole の詳細ログ
```yaml
- name: Configure AWS credentials (OIDC)
  uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: ${{ secrets.AWS_GITHUB_ACTIONS_ROLE_ARN }}
    role-session-name: GitHubActions-Debug-${{ github.run_id }}
    aws-region: ${{ env.AWS_REGION }}
    mask-aws-account-id: false  # デバッグ用
```

## 環境別設定

### 開発環境
```bash
# 開発環境用ロールARN
AWS_GITHUB_ACTIONS_ROLE_ARN=arn:aws:iam::123456789012:role/GitHubActions-ExcelUnlocker-development
```

### ステージング環境
```bash
# ステージング環境用ロールARN
AWS_GITHUB_ACTIONS_ROLE_ARN=arn:aws:iam::123456789012:role/GitHubActions-ExcelUnlocker-staging
```

### 本番環境
```bash
# 本番環境用ロールARN（より厳格な権限）
AWS_GITHUB_ACTIONS_ROLE_ARN=arn:aws:iam::123456789012:role/GitHubActions-ExcelUnlocker-production
```

## 監視とログ

### CloudTrail監視
```bash
# OIDC認証の監視
aws logs filter-log-events \
  --log-group-name CloudTrail/ExcelUnlocker \
  --filter-pattern "AssumeRoleWithWebIdentity"
```

### CloudWatch メトリクス
- AssumeRole成功率
- セッション継続時間
- 権限エラー発生率

## 今後の改善計画

### 短期的改善
1. **ブランチ別権限**: mainブランチのみ本番デプロイ可能
2. **時間制限**: 営業時間内のみデプロイ可能
3. **IP制限**: 特定IPからのみアクセス可能

### 長期的改善
1. **マルチアカウント対応**: 環境別AWSアカウント
2. **動的権限**: デプロイ内容に応じた最小権限
3. **自動監査**: 異常なアクセスパターンの検出

## セキュリティベストプラクティス

### 1. 最小権限の原則
```yaml
# 必要最小限の権限のみ付与
Policies:
  - PolicyName: SAMDeployOnly
    PolicyDocument:
      Version: '2012-10-17'
      Statement:
        - Effect: Allow
          Action:
            - cloudformation:CreateStack
            - cloudformation:UpdateStack
            - cloudformation:DescribeStacks
          Resource: !Sub "arn:aws:cloudformation:${AWS::Region}:${AWS::AccountId}:stack/excel-unlocker-*"
```

### 2. 条件付きアクセス
```yaml
# 特定の条件下でのみアクセス許可
Condition:
  StringEquals:
    "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
  StringLike:
    "token.actions.githubusercontent.com:sub": "repo:hirokun-hub/python-excel-unlocker:*"
  DateGreaterThan:
    "aws:CurrentTime": "2025-01-01T00:00:00Z"
```

### 3. 定期的な権限レビュー
```bash
# 使用されていない権限の確認
aws iam get-role --role-name GitHubActions-ExcelUnlocker-development
aws iam list-attached-role-policies --role-name GitHubActions-ExcelUnlocker-development
```

## まとめ

GitHub OIDC化により、以下のセキュリティ強化が実現されました：

1. **長期キー廃止**: AWSキー漏洩リスクの根本的解決
2. **短期クレデンシャル**: 自動期限切れによるセキュリティ向上
3. **細かい権限制御**: リポジトリ・ブランチ単位での制御
4. **監査可能性**: 詳細なアクセスログによる追跡

この移行により、GitHub ActionsでのAWS認証が大幅に安全になり、本番環境での運用リスクが軽減されます。