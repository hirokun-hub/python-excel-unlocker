---
layout: default
title: AWSコンソールで行う GitHub OIDC + 最小権限ロール設定ガイド
description: AWSマネジメントコンソールでGitHub Actions用OIDCと最小権限のIAMロールを設定する手順
permalink: manual-aws-console-oidc-setup
date: 2025-10-04
last_modified_at: 2025-10-04
published: true
Tags:
  - github_actions
  - aws_oidc
  - iam
  - セキュリティ
  - デプロイ
---

> 本ガイドはAWSコンソール操作での手順です。既存のCLI手順（`docs/setup/github-oidc-aws.md`）と内容を揃え、Lambda実行ロールをCloudFormationで管理するために必要な「最小権限」の付与も含みます（2025-10-04 追記）。

## ゴール
- GitHub ActionsがOIDCでAssumeできるIAMロールを作成
- そのロールに、CloudFormationがLambda実行ロールを作成/更新/削除できる「最小権限」を付与

## 前提
- AWS管理者権限でコンソールにサインインできる
- 対象GitHubリポジトリ/ブランチが決まっている（例: `hirokun-hub/python-excel-unlocker`, `main`）

## 1. OIDCプロバイダーの作成（コンソール）
1. コンソールで「IAM」→「IDプロバイダー」→「プロバイダーを追加」
2. 種別: OpenID Connect
3. プロバイダーURL: `https://token.actions.githubusercontent.com`
4. クライアントID（オーディエンス）: `sts.amazonaws.com`
5. 追加を完了

参考: GitHub公式「Configuring OpenID Connect in AWS」（最新UIに準拠）

## 2. GitHub Actions用IAMロールの作成（信頼ポリシー）
1. 「IAM」→「ロール」→「ロールを作成」
2. 信頼されたエンティティの種類: 「カスタム信頼ポリシー」
3. 以下を貼り付け、`<ACCOUNT_ID>`, `<ORG>`, `<REPO>`, `<BRANCH>`を置換

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::<ACCOUNT_ID>:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:<ORG>/<REPO>:ref:refs/heads/<BRANCH>"
        }
      }
    }
  ]
}
```

> ブランチ制限を付けることで権限の露出を抑えます（例: `main`）。必要に応じて環境ごとにロールを分けてください。

## 3. 最小権限ポリシーの作成とアタッチ
CloudFormationがLambda実行ロールを管理できるよう、対象ロール名パターンを厳密に絞って付与します。

1. 「IAM」→「ポリシー」→「ポリシーを作成」→「JSON」タブ
2. 以下を貼り付け、`<ACCOUNT_ID>`を置換（ロール名は`template.yaml`の命名規約に合わせる）

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ManageLambdaExecutionRoles",
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
        "iam:TagRole",
        "iam:UntagRole"
      ],
      "Resource": [
        "arn:aws:iam::<ACCOUNT_ID>:role/excel-unlocker-api-*-GetUploadUrlFunctionRole-*",
        "arn:aws:iam::<ACCOUNT_ID>:role/excel-unlocker-api-*-UnlockFunctionRole-*"
      ]
    },
    {
      "Sid": "PassLambdaExecutionRoles",
      "Effect": "Allow",
      "Action": "iam:PassRole",
      "Resource": [
        "arn:aws:iam::<ACCOUNT_ID>:role/excel-unlocker-api-*-GetUploadUrlFunctionRole-*",
        "arn:aws:iam::<ACCOUNT_ID>:role/excel-unlocker-api-*-UnlockFunctionRole-*"
      ],
      "Condition": {
        "StringEquals": { "iam:PassedToService": "lambda.amazonaws.com" }
      }
    }
  ]
}
```

3. ポリシーに名称を付けて作成（例: `GitHubActions-ExcelUnlocker-ManageLambdaExecRoles`）
4. 作成したポリシーを、手順2で作成したGitHub Actions用ロールにアタッチ

> 推奨: Permissions Boundaryを導入し、作成される実行ロールの上限権限を制限する運用にすると安全です。

## 4. GitHub側設定
- リポジトリ `Settings` → `Secrets and variables` → `Actions` に `AWS_GITHUB_ACTIONS_ROLE_ARN` を登録
- ワークフローで `permissions: { id-token: write, contents: read }` を設定し、`aws-actions/configure-aws-credentials@v4` でAssume

## 5. 検証
- GitHub Actionsの実行で `aws sts get-caller-identity` をStep Summaryに出力
- デプロイ後、CloudFormationスタックに実行ロールが作成されていることを確認

## 6. トラブルシューティング要点
- OIDCトラストの`sub`がリポジトリ/ブランチに一致しているか
- `iam:PassRole`の条件が`lambda.amazonaws.com`に限定されているか
- スタック状態（`ROLLBACK_*`）時は更新不可。削除→再作成または事前ヘルスチェック

## 参考
- GitHub: Configuring OpenID Connect in AWS（最新）
- aws-actions/configure-aws-credentials v4 ドキュメント
- AWS IAM ベストプラクティス（最小権限、Permissions Boundary）
