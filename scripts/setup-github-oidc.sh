#!/bin/bash

# GitHub OIDC設定スクリプト
# AWS IAM OIDCプロバイダーとロールを作成し、GitHub ActionsでのOIDC認証を設定

set -euo pipefail

# 設定値
GITHUB_REPO="${GITHUB_REPOSITORY:-hironomac2025/excel-password-remover}"
AWS_REGION="${AWS_REGION:-ap-northeast-1}"
ROLE_NAME="GitHubActionsRole"
POLICY_NAME="GitHubActionsPolicy"

echo "🚀 GitHub OIDC設定を開始します..."
echo "リポジトリ: $GITHUB_REPO"
echo "リージョン: $AWS_REGION"

# 1. OIDCプロバイダーの存在確認と作成
echo "📋 Step 1: OIDCプロバイダーの確認・作成"

OIDC_PROVIDER_ARN=$(aws iam list-open-id-connect-providers --query "OpenIDConnectProviderList[?contains(Arn, 'token.actions.githubusercontent.com')].Arn" --output text 2>/dev/null || echo "")

if [[ -z "$OIDC_PROVIDER_ARN" ]]; then
    echo "OIDCプロバイダーを作成中..."
    
    # GitHub OIDCプロバイダーの証明書取得
    THUMBPRINT=$(echo | openssl s_client -servername token.actions.githubusercontent.com -connect token.actions.githubusercontent.com:443 2>/dev/null | openssl x509 -fingerprint -noout -sha1 | sed 's/://g' | cut -d= -f2)
    
    OIDC_PROVIDER_ARN=$(aws iam create-open-id-connect-provider \
        --url https://token.actions.githubusercontent.com \
        --client-id-list sts.amazonaws.com \
        --thumbprint-list $THUMBPRINT \
        --query 'OpenIDConnectProviderArn' \
        --output text)
    
    echo "✅ OIDCプロバイダーを作成しました: $OIDC_PROVIDER_ARN"
else
    echo "✅ OIDCプロバイダーが既に存在します: $OIDC_PROVIDER_ARN"
fi

# 2. IAMポリシーの作成
echo "📋 Step 2: IAMポリシーの作成"

POLICY_DOCUMENT=$(cat <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "cloudformation:CreateStack",
                "cloudformation:UpdateStack",
                "cloudformation:DeleteStack",
                "cloudformation:DescribeStacks",
                "cloudformation:DescribeStackEvents",
                "cloudformation:DescribeStackResources",
                "cloudformation:GetTemplate",
                "cloudformation:ValidateTemplate",
                "cloudformation:CreateChangeSet",
                "cloudformation:DescribeChangeSet",
                "cloudformation:ExecuteChangeSet",
                "cloudformation:DeleteChangeSet",
                "cloudformation:ListStacks"
            ],
            "Resource": "*"
        },
        {
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
                "lambda:GetPolicy",
                "lambda:PutFunctionConcurrency",
                "lambda:DeleteFunctionConcurrency",
                "lambda:TagResource",
                "lambda:UntagResource"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "apigateway:GET",
                "apigateway:POST",
                "apigateway:PUT",
                "apigateway:DELETE",
                "apigateway:PATCH"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:CreateBucket",
                "s3:DeleteBucket",
                "s3:GetBucketLocation",
                "s3:GetBucketPolicy",
                "s3:PutBucketPolicy",
                "s3:DeleteBucketPolicy",
                "s3:GetBucketCors",
                "s3:PutBucketCors",
                "s3:GetBucketVersioning",
                "s3:PutBucketVersioning",
                "s3:GetBucketNotification",
                "s3:PutBucketNotification",
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::excel-unlocker-*",
                "arn:aws:s3:::excel-unlocker-*/*",
                "arn:aws:s3:::aws-sam-cli-managed-default-samclisourcebucket-*",
                "arn:aws:s3:::aws-sam-cli-managed-default-samclisourcebucket-*/*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "iam:CreateRole",
                "iam:DeleteRole",
                "iam:GetRole",
                "iam:PassRole",
                "iam:AttachRolePolicy",
                "iam:DetachRolePolicy",
                "iam:PutRolePolicy",
                "iam:DeleteRolePolicy",
                "iam:GetRolePolicy",
                "iam:TagRole",
                "iam:UntagRole"
            ],
            "Resource": [
                "arn:aws:iam::*:role/excel-unlocker-*",
                "arn:aws:iam::*:role/ExcelUnlocker*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:DeleteLogGroup",
                "logs:DescribeLogGroups",
                "logs:PutRetentionPolicy"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "events:PutRule",
                "events:DeleteRule",
                "events:DescribeRule",
                "events:PutTargets",
                "events:RemoveTargets",
                "events:ListTargetsByRule"
            ],
            "Resource": "*"
        }
    ]
}
EOF
)

# ポリシーの存在確認
POLICY_ARN=$(aws iam list-policies --scope Local --query "Policies[?PolicyName=='$POLICY_NAME'].Arn" --output text 2>/dev/null || echo "")

if [[ -z "$POLICY_ARN" ]]; then
    echo "IAMポリシーを作成中..."
    POLICY_ARN=$(aws iam create-policy \
        --policy-name $POLICY_NAME \
        --policy-document "$POLICY_DOCUMENT" \
        --description "GitHub Actions用のAWS操作権限" \
        --query 'Policy.Arn' \
        --output text)
    echo "✅ IAMポリシーを作成しました: $POLICY_ARN"
else
    echo "✅ IAMポリシーが既に存在します: $POLICY_ARN"
    
    # 既存ポリシーの更新
    echo "既存ポリシーを更新中..."
    aws iam create-policy-version \
        --policy-arn $POLICY_ARN \
        --policy-document "$POLICY_DOCUMENT" \
        --set-as-default > /dev/null
    echo "✅ IAMポリシーを更新しました"
fi

# 3. IAMロールの作成
echo "📋 Step 3: IAMロールの作成"

TRUST_POLICY=$(cat <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Federated": "$OIDC_PROVIDER_ARN"
            },
            "Action": "sts:AssumeRoleWithWebIdentity",
            "Condition": {
                "StringEquals": {
                    "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
                },
                "StringLike": {
                    "token.actions.githubusercontent.com:sub": "repo:$GITHUB_REPO:*"
                }
            }
        }
    ]
}
EOF
)

# ロールの存在確認
ROLE_ARN=$(aws iam get-role --role-name $ROLE_NAME --query 'Role.Arn' --output text 2>/dev/null || echo "")

if [[ -z "$ROLE_ARN" ]]; then
    echo "IAMロールを作成中..."
    ROLE_ARN=$(aws iam create-role \
        --role-name $ROLE_NAME \
        --assume-role-policy-document "$TRUST_POLICY" \
        --description "GitHub Actions用のOIDCロール" \
        --query 'Role.Arn' \
        --output text)
    echo "✅ IAMロールを作成しました: $ROLE_ARN"
else
    echo "✅ IAMロールが既に存在します: $ROLE_ARN"
    
    # 信頼ポリシーの更新
    echo "信頼ポリシーを更新中..."
    aws iam update-assume-role-policy \
        --role-name $ROLE_NAME \
        --policy-document "$TRUST_POLICY"
    echo "✅ 信頼ポリシーを更新しました"
fi

# 4. ポリシーをロールにアタッチ
echo "📋 Step 4: ポリシーのアタッチ"

aws iam attach-role-policy \
    --role-name $ROLE_NAME \
    --policy-arn $POLICY_ARN 2>/dev/null || echo "ポリシーは既にアタッチされています"

echo "✅ ポリシーをロールにアタッチしました"

# 5. 設定情報の出力
echo ""
echo "🎉 GitHub OIDC設定が完了しました！"
echo ""
echo "📋 GitHub Secretsに以下の値を設定してください："
echo ""
echo "AWS_GITHUB_ACTIONS_ROLE_ARN=$ROLE_ARN"
echo ""
echo "🔧 設定手順："
echo "1. GitHubリポジトリの Settings > Secrets and variables > Actions に移動"
echo "2. 'New repository secret' をクリック"
echo "3. Name: AWS_GITHUB_ACTIONS_ROLE_ARN"
echo "4. Secret: $ROLE_ARN"
echo "5. 'Add secret' をクリック"
echo ""
echo "⚠️  既存のAWS_ACCESS_KEY_IDとAWS_SECRET_ACCESS_KEYは削除してください"
echo ""
echo "✅ 設定完了後、GitHub Actionsワークフローが自動的にOIDC認証を使用します"

# 6. 設定ファイルの生成（オプション）
cat > github-oidc-config.json <<EOF
{
  "oidc_provider_arn": "$OIDC_PROVIDER_ARN",
  "role_arn": "$ROLE_ARN",
  "policy_arn": "$POLICY_ARN",
  "github_repository": "$GITHUB_REPO",
  "aws_region": "$AWS_REGION",
  "setup_date": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
}
EOF

echo "📄 設定情報をgithub-oidc-config.jsonに保存しました"