# レート制限・WAF設定ガイド

## 概要

このドキュメントでは、Excel Unlocker APIに実装されたレート制限とWAF（Web Application Firewall）設定について説明します。これらの設定により、DDoS攻撃、総当たり攻撃、Bot攻撃からAPIを保護します。

## 実装された保護機能

### 1. API Gatewayスロットリング設定

#### 設定値
| 環境 | バーストリミット | 継続レート制限 |
|------|------------------|----------------|
| 本番環境 | 100 req/burst | 50 req/sec |
| 開発・ステージング | 200 req/burst | 100 req/sec |

#### 動作
- **バーストリミット**: 短時間に許可される最大リクエスト数
- **継続レート制限**: 1秒間に許可される平均リクエスト数
- 制限を超えたリクエストは`429 Too Many Requests`で拒否

### 2. WAFv2レートベースルール

#### 設定値
| 環境 | 5分間のリクエスト制限 |
|------|----------------------|
| 本番環境 | 1,000 requests |
| 開発・ステージング | 2,000 requests |

#### 動作
- IPアドレス単位で5分間のリクエスト数を監視
- 制限を超えたIPアドレスからのリクエストを自動ブロック
- ブロック期間は自動的に解除（通常10分程度）

### 3. 地理的制限

#### 設定
- **許可国**: 日本（JP）のみ
- **動作**: 日本以外からのアクセスを自動ブロック

### 4. AWS Managed Rules

#### 実装されたルールセット

##### Known Bad Inputs Rule Set
- 既知の悪意のあるリクエストパターンをブロック
- SQLインジェクション、XSS攻撃の基本的な防御

##### Common Rule Set
- 一般的なWeb攻撃パターンをブロック
- ファイルアップロード機能のため一部ルールを除外
  - `SizeRestrictions_BODY`: 大きなファイルアップロード許可
  - `GenericRFI_BODY`: 正当なリクエストの誤検知防止

##### Bot Control Rule Set
- 自動化されたBot攻撃を検知・ブロック
- 検査レベル: COMMON（基本的なBot検知）

### 5. カスタムIPブロック機能

#### 機能
- 手動でIPアドレスをブロックリストに追加可能
- 社内IPアドレスのホワイトリスト設定可能

## 監視・アラート設定

### CloudWatchアラーム

#### 高レート制限アラーム
- **条件**: 5分間で50回以上のレート制限ブロック
- **通知**: SNSトピック経由でメール通知

#### Bot攻撃アラーム
- **条件**: 5分間で10回以上のBot検知
- **通知**: SNSトピック経由でメール通知

### CloudWatchダッシュボード

#### 監視メトリクス
- WAF許可/ブロックリクエスト数
- レート制限イベント数
- Bot制御イベント数
- Lambda関数のパフォーマンス指標

## 運用手順

### 1. IPアドレスの手動ブロック

```bash
# AWS CLIでIPアドレスをブロックリストに追加
aws wafv2 update-ip-set \
  --scope REGIONAL \
  --id <BlockedIPSetId> \
  --addresses "192.0.2.1/32,203.0.113.0/24" \
  --region ap-northeast-1
```

### 2. 社内IPアドレスのホワイトリスト追加

```bash
# 社内IPアドレスを許可リストに追加
aws wafv2 update-ip-set \
  --scope REGIONAL \
  --id <AllowedIPSetId> \
  --addresses "203.0.113.100/32" \
  --region ap-northeast-1
```

### 3. WAFルールの一時無効化（緊急時）

```bash
# 特定のルールを一時的に無効化
aws wafv2 update-web-acl \
  --scope REGIONAL \
  --id <WebACLId> \
  --default-action Allow={} \
  --rules file://disabled-rules.json \
  --region ap-northeast-1
```

### 4. レート制限の調整

SAMテンプレートの`MethodSettings`を更新してデプロイ：

```yaml
MethodSettings:
  - ResourcePath: "/*"
    HttpMethod: "*"
    ThrottlingBurstLimit: 150  # 調整値
    ThrottlingRateLimit: 75    # 調整値
```

## トラブルシューティング

### 正当なユーザーがブロックされる場合

#### 症状
- 429エラーまたは403エラーが頻発
- 特定のIPアドレスからのアクセスが拒否される

#### 対処法
1. **CloudWatchログを確認**
   ```bash
   aws logs filter-log-events \
     --log-group-name /aws/wafv2/webacl \
     --start-time $(date -d '1 hour ago' +%s)000
   ```

2. **WAFサンプルリクエストを確認**
   - AWS Console > WAF & Shield > Web ACLs
   - サンプルリクエストタブで詳細を確認

3. **IPアドレスを許可リストに追加**
   ```bash
   aws wafv2 update-ip-set \
     --scope REGIONAL \
     --id <AllowedIPSetId> \
     --addresses "ブロックされたIP/32"
   ```

### Bot制御の誤検知

#### 症状
- 正当なブラウザアクセスがBot判定される
- モバイルアプリからのアクセスが拒否される

#### 対処法
1. **Bot制御レベルを調整**
   ```yaml
   ManagedRuleGroupConfigs:
     - AWSManagedRulesBotControlRuleSet:
         InspectionLevel: COMMON  # TARGETEDから変更
   ```

2. **特定のBot制御ルールを除外**
   ```yaml
   ExcludedRules:
     - Name: SignalNonBrowserUserAgent
     - Name: CategoryHttpLibrary
   ```

### パフォーマンスへの影響

#### 症状
- API応答時間の増加
- タイムアウトエラーの発生

#### 対処法
1. **WAFルールの最適化**
   - 不要なルールの無効化
   - ルール優先度の調整

2. **レート制限の緩和**
   - バーストリミットの増加
   - 継続レート制限の調整

## セキュリティベストプラクティス

### 1. 定期的な監視
- 週次でWAFログとメトリクスを確認
- 異常なトラフィックパターンの検知

### 2. ルールの定期更新
- AWS Managed Rulesの自動更新を有効化
- 新しい脅威に対応したカスタムルールの追加

### 3. インシデント対応
- 攻撃検知時の自動ブロック手順の整備
- エスカレーション手順の明文化

### 4. テスト環境での検証
- 本番適用前のステージング環境でのテスト
- 正当なトラフィックへの影響確認

## 関連リソース

### AWS Console URLs
- **WAF Web ACL**: `https://console.aws.amazon.com/wafv2/homev2/web-acls`
- **CloudWatch Dashboard**: 出力値の`DashboardUrl`を参照
- **API Gateway**: `https://console.aws.amazon.com/apigateway/`

### 設定ファイル
- **SAMテンプレート**: `template.yaml`
- **デプロイ設定**: `samconfig.toml`

### ログ確認
```bash
# WAFログ
aws logs describe-log-groups --log-group-name-prefix "/aws/wafv2"

# API Gatewayログ
aws logs describe-log-groups --log-group-name-prefix "/aws/apigateway"

# Lambda関数ログ
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda"
```

## 緊急時連絡先

- **システム管理者**: hironomac2025@gmail.com
- **SNSアラート**: 自動通知設定済み
- **エスカレーション**: GitHub Issues作成

---

このガイドは定期的に更新され、新しい脅威や要件に対応していきます。