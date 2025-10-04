---
layout: default
title: 2025-10-04 AWS連携メモ（OIDC・Lambda実行ロール・CI/CD）
description: GitHub Actions OIDCとCloudFormationでの権限設計見直し、対応内容と今後の進め方
date: 2025-10-04
last_modified_at: 2025-10-04
published: true
Tags:
  - journal
  - aws
  - github_actions
  - oidc
  - iam
  - cloudformation
---

## 今日の概要
- GitHub Actions経由のAWSデプロイで、IAM関連の失敗（`ROLLBACK_FAILED`、`iam:CreateRole/iam:DeleteRolePolicy`拒否）を再分析。
- CI用IAM（GitHub OIDCプロバイダー／GitHub Actionsロール）をアプリケーションスタックから分離し、ブートストラップ管理へ移行。
- デプロイ実行ロール（OIDCでAssumeするロール）に、Lambda実行ロール管理のための「最小権限」を付与する方針を確立。

## 実施内容（編集・変更）
- `template.yaml`:
  - CI用IAM（`GitHubOIDCProvider`, `GitHubActionsRole`）と関連パラメータ／条件／出力を完全削除。
- `.github/workflows/deploy-aws.yml`:
  - スタック事前ヘルスチェック（Pre-check）を追加。
  - 環境名を正規化（dev/staging/prod）してスタック名に反映。
  - OIDC認証後に `aws sts get-caller-identity` をStep Summaryに出力（アカウント可視化）。
  - API URL取得ロジックを堅牢化（出力名の揺れ・execute-api派生・リトライ）。
  - 本番/ステージングでAPI URL未取得時は明示的に失敗。
- ドキュメント:
  - `docs/setup/github-oidc-aws.md` を最新方針に更新（変更履歴と最小権限付与手順を追記）。
  - 新規: `docs/setup/manual-aws-console-oidc-setup.md`（AWSコンソール操作手順）。
  - 目次: `docs/README.md` に上記ガイドへのリンクを追加。

## 主要なエラーと原因
- `ROLLBACK_FAILED`（`iam:CreateRole` / `iam:DeleteRolePolicy` など）
  - 原因: ActionsがAssumeするOIDCロールに、CloudFormationがLambda実行ロールを作成・更新・削除するためのIAM権限が不足。
- API URL未取得による統合テスト失敗
  - 原因: スタック出力のキー差異や未展開時の派生失敗。

## 決定事項（ベストプラクティス）
- CI用IAMはブートストラップで管理し、アプリケーションスタックと分離。
- OIDCロールに対し、Lambda実行ロール管理に必要な権限のみを追加（対象ロールARNを厳格に限定、`iam:PassRole`は`lambda.amazonaws.com`に限定）。
- スタック事前チェック・API URL必須化（staging/prod）は継続運用。

## 今後の進め方（To-Do）
- OIDCロール（`AWS_GITHUB_ACTIONS_ROLE_ARN`）に最小権限を付与（ドキュメントのJSONを `<ACCOUNT_ID>` で置換して適用）。
- `staging` デプロイを再実行し、CloudFormationが実行ロールを自動作成できることを確認。
- API URLを取得し、統合テストの通過を確認。
- 開発環境スタックで `ROLLBACK_*` が残っている場合はクリーンアップ（事前ヘルスチェックで検知）。

## 参照
- ガイド（CLI中心・方針/履歴付き）: `docs/setup/github-oidc-aws.md`
- ガイド（AWSコンソール操作）: `docs/setup/manual-aws-console-oidc-setup.md`
- ワークフロー: `.github/workflows/deploy-aws.yml`
- スタック: `template.yaml`
