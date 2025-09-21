# Vercel設定詳細ガイド - GitHub Actions連携

## 📋 概要

このガイドでは、GitHub ActionsからVercelにデプロイするための設定方法を詳しく説明します。特に**Vercel Hobbyアカウント + チーム構成**での運用を前提とした、確実で分かりやすい手順を提供します。

## 🎯 前提条件

### Vercelアカウント構成（推奨）

```
Vercel Hobbyアカウント（無料プラン）
└── My Account
    └── Teams
        └── excel-unlocker-team（作成したチーム）
            └── excel-unlocker（プロジェクト）
```

**なぜこの構成が推奨か**:
- **組織管理**: 複数プロジェクトの一元管理
- **権限分離**: 個人アカウントとプロジェクトの分離
- **将来性**: チームメンバー追加時の拡張性
- **明確性**: 組織ID（Team ID）の識別が容易

## 🔑 GitHub Actions用必須シークレット3点

GitHub ActionsでVercelにデプロイするために、以下の**3つのシークレット**が必要です：

### 1. VERCEL_TOKEN（個人のAccess Token）

**取得場所**: https://vercel.com/account/tokens

**手順**:
1. Vercelにログイン
2. Account Settings → Tokens
3. 「Create Token」をクリック
4. 設定:
   ```
   Token Name: excel-unlocker-deploy-token
   Scope: Full Account
   Expiration: No expiration（または適切な期限）
   ```
5. 生成されたトークンをコピー

**形式**: `vercel_1234567890abcdef...`

### 2. VERCEL_ORG_ID（組織ID）

**今回はチーム配下のプロジェクトなので、Team IDを使用します。**

#### 方法1: Vercelダッシュボードから取得

**取得場所**: https://vercel.com/teams/[your-team-slug]/settings

**手順**:
1. チームのSettings画面にアクセス
2. 「General」タブを選択
3. 「Team ID」をコピー

**形式**: `team_abc123def456789`

#### 方法2: .vercel/project.jsonから取得（推奨）

```bash
# frontendディレクトリで実行
cd frontend
vercel link
cat .vercel/project.json
```

**出力例**:
```json
{
  "orgId": "team_abc123def456789",
  "projectId": "prj_xyz789abc123def"
}
```

### 3. VERCEL_PROJECT_ID（プロジェクトID）

#### 方法1: Vercelダッシュボードから取得

**取得場所**: https://vercel.com/[team-slug]/excel-unlocker/settings

**手順**:
1. プロジェクトのSettings画面にアクセス
2. 「General」タブを選択
3. 「Project ID」をコピー

**形式**: `prj_abc123def456789`

#### 方法2: .vercel/project.jsonから取得（推奨）

上記の方法2と同じファイルから取得できます。

## 🚨 よくある間違いと対処法

### ❌ 間違い1: User IDとTeam IDの取り違え

**問題**: 個人配下のプロジェクトにTeam IDを設定、またはその逆
**症状**: 403 Forbidden または 404 Not Found エラー
**解決**: **プロジェクトが属する側のID**を使用する

| プロジェクトの配置 | 使用するID | 形式 |
|------------------|-----------|------|
| チーム配下 | Team ID | `team_abc123def456` |
| 個人配下 | Your ID | `QmVyY2VsVGVhbQ`（ランダム文字列） |

### ❌ 間違い2: 二重デプロイ

**問題**: Vercel GitHub連携とGitHub Actionsが両方動作
**症状**: 同時に2つのデプロイが実行される
**解決**: GitHub連携を無効化

#### 解決方法1: Vercelダッシュボードで無効化
1. プロジェクトSettings → Git
2. 「Disconnect」をクリック

#### 解決方法2: vercel.jsonで無効化
```json
{
  "github": {
    "enabled": false
  }
}
```

### ❌ 間違い3: 古いワークフロー構文

**問題**: 古いVercel GitHub Actionsを使用
**症状**: デプロイが失敗する
**解決**: 公式推奨の`vercel pull → build → deploy`を使用

## ✅ 推奨GitHub Actionsワークフロー

### 最小ワークフロー例

```yaml
name: Vercel Deploy
on:
  push:
    branches: [ main ]
  pull_request:

env:
  VERCEL_ORG_ID: ${{ secrets.VERCEL_ORG_ID }}
  VERCEL_PROJECT_ID: ${{ secrets.VERCEL_PROJECT_ID }}

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm i -g vercel@latest
      
      # PRやブランチは preview、main は production で引く
      - run: vercel pull --yes --environment=${{ github.ref == 'refs/heads/main' && 'production' || 'preview' }} --token=${{ secrets.VERCEL_TOKEN }}
      
      - run: vercel build ${{ github.ref == 'refs/heads/main' && '--prod' || '' }} --token=${{ secrets.VERCEL_TOKEN }}
      
      - run: vercel deploy --prebuilt ${{ github.ref == 'refs/heads/main' && '--prod' || '' }} --token=${{ secrets.VERCEL_TOKEN }}
```

### ワークフローのポイント

1. **3段階の処理**: `pull → build → deploy --prebuilt`
2. **環境分岐**: mainブランチは本番、それ以外はプレビュー
3. **必要なシークレット**: 上記3点のみ
4. **公式推奨**: Vercel公式ガイドに準拠

## 🔧 設定確認方法

### 1. .vercel/project.jsonの確認

```bash
cd frontend
cat .vercel/project.json
```

**期待する出力**:
```json
{
  "orgId": "team_abc123def456789",
  "projectId": "prj_xyz789abc123def"
}
```

### 2. GitHub Secretsの確認

GitHub リポジトリ → Settings → Secrets and variables → Actions

**必要なシークレット**:
- ✅ `VERCEL_TOKEN`
- ✅ `VERCEL_ORG_ID`
- ✅ `VERCEL_PROJECT_ID`

### 3. Vercel Git連携の確認

Vercel プロジェクト → Settings → Git

**期待する状態**: 「No Git Integration」または「Disconnected」

## 🚀 デプロイテスト

### 手動テスト

```bash
# ローカルでテスト
cd frontend
vercel --prod --token YOUR_VERCEL_TOKEN
```

### GitHub Actionsテスト

1. 軽微な変更をコミット
2. mainブランチにプッシュ
3. GitHub Actions → Workflowsで実行状況確認
4. Vercel Dashboardでデプロイ確認

## 📚 参考リンク

- [Vercel CLI Documentation](https://vercel.com/docs/cli)
- [GitHub Actions with Vercel](https://vercel.com/guides/how-can-i-use-github-actions-with-vercel)
- [Vercel Environment Variables](https://vercel.com/docs/concepts/projects/environment-variables)

## 🆘 トラブルシューティング

### エラー: "Project not found"

**原因**: VERCEL_PROJECT_IDが間違っている
**解決**: `.vercel/project.json`から正しいprojectIdを確認

### エラー: "Forbidden"

**原因**: VERCEL_ORG_IDが間違っている
**解決**: プロジェクトが属する組織のIDを確認（チーム配下ならTeam ID）

### エラー: "Token invalid"

**原因**: VERCEL_TOKENが無効または期限切れ
**解決**: 新しいトークンを生成して更新

### デプロイが2回実行される

**原因**: Vercel GitHub連携が有効
**解決**: Git連携を無効化（上記参照）

## 📝 チェックリスト

設定完了前に以下を確認してください：

- [ ] Vercel Hobbyアカウント作成済み
- [ ] チーム作成済み
- [ ] プロジェクトをチーム配下に配置済み
- [ ] VERCEL_TOKEN取得済み
- [ ] VERCEL_ORG_ID（Team ID）取得済み
- [ ] VERCEL_PROJECT_ID取得済み
- [ ] GitHub Secretsに3点設定済み
- [ ] Vercel Git連携無効化済み
- [ ] GitHub Actionsワークフロー更新済み
- [ ] デプロイテスト成功