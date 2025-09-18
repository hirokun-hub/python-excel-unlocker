# CORS設定の厳格化ガイド

## 概要

このドキュメントは、CORS（Cross-Origin Resource Sharing）設定の厳格化について説明します。ワイルドカード（*）を廃止し、環境別の固定オリジン設定により、任意オリジンからのAPI呼び出しを防止します。

## 厳格化の背景

### 従来のCORS設定の問題点

1. **ワイルドカード使用**: `Access-Control-Allow-Origin: *` による全オリジン許可
2. **任意オリジン攻撃**: 悪意のあるサイトからのAPI呼び出しが可能
3. **セキュリティリスク**: CSRF攻撃やデータ漏洩の可能性
4. **本番環境での脆弱性**: 開発用設定が本番に残存するリスク

### CORS厳格化の利点

1. **オリジン制限**: 許可されたドメインからのみアクセス可能
2. **環境別設定**: 開発・ステージング・本番で異なるオリジン設定
3. **攻撃面の縮小**: 悪意のあるサイトからの攻撃を防止
4. **コンプライアンス**: セキュリティ標準への準拠

## 実装内容

### 1. AWS SAMテンプレートの変更

#### パラメータの追加
```yaml
Parameters:
  AllowedOrigins:
    Type: String
    Default: "https://localhost:3000,https://localhost:3001"
    Description: "Comma-separated list of allowed CORS origins"
    AllowedValues:
      - "https://localhost:3000,https://localhost:3001"  # development
      - "https://localhost:3000,https://localhost:3001,https://excel-unlocker-staging.vercel.app"  # staging
      - "https://excel-unlocker.vercel.app"  # production
```

#### API Gateway CORS設定
```yaml
# 変更前（脆弱）
Api:
  Cors:
    AllowOrigin: "'*'"  # 全オリジン許可

# 変更後（安全）
Api:
  Cors:
    AllowOrigin: !Sub "'${AllowedOrigins}'"  # 環境別固定オリジン
```

#### S3バケットCORS設定
```yaml
CorsConfiguration:
  CorsRules:
    - AllowedOrigins: !Split [",", !Ref AllowedOrigins]  # 環境別設定
      AllowedMethods: [GET, PUT, HEAD]
      AllowedHeaders: ["Content-Type", "Authorization"]
      MaxAge: 3600
```

### 2. Lambda関数の環境変数

```yaml
Environment:
  Variables:
    # CORS設定の厳格化：環境別許可オリジン
    ALLOWED_ORIGINS: !Ref AllowedOrigins
```

### 3. response_utils.pyの実装

#### 環境別オリジン取得
```python
def get_allowed_origin() -> str:
    """
    環境に応じた許可オリジンを取得する
    CORS設定の厳格化：ワイルドカード廃止、環境別固定オリジン
    """
    allowed_origins = os.environ.get('ALLOWED_ORIGINS', 'https://localhost:3000')
    
    # API Gatewayは単一のオリジンのみサポート
    if ',' in allowed_origins:
        return allowed_origins.split(',')[0].strip()
    
    return allowed_origins.strip()
```

#### レスポンスヘッダーの生成
```python
# 変更前（脆弱）
headers = {
    'Access-Control-Allow-Origin': '*',  # ワイルドカード
}

# 変更後（安全）
headers = {
    'Access-Control-Allow-Origin': get_allowed_origin(),  # 固定オリジン
}
```

### 4. vercel.jsonの不要設定削除

```json
// 削除された設定（不要）
{
  "headers": [
    {
      "source": "/api/(.*)",
      "headers": [
        {
          "key": "Access-Control-Allow-Origin",
          "value": "*"  // ワイルドカード削除
        }
      ]
    }
  ]
}
```

## 環境別設定

### 開発環境
```
ALLOWED_ORIGINS=https://localhost:3000,https://localhost:3001
```

### ステージング環境
```
ALLOWED_ORIGINS=https://localhost:3000,https://localhost:3001,https://excel-unlocker-staging.vercel.app
```

### 本番環境
```
ALLOWED_ORIGINS=https://excel-unlocker.vercel.app
```

## セキュリティ強化効果

### 1. 任意オリジン攻撃の防止

#### 攻撃例（従来）
```javascript
// 悪意のあるサイト（evil.com）から
fetch('https://api.excel-unlocker.com/unlock', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer stolen-token'
  },
  body: JSON.stringify({...})
})
// → 成功（ワイルドカード設定により許可）
```

#### 防御（厳格化後）
```javascript
// 同じ攻撃を試行
fetch('https://api.excel-unlocker.com/unlock', {
  method: 'POST',
  headers: {...},
  body: JSON.stringify({...})
})
// → 失敗（CORS エラー：evil.com は許可されていない）
```

### 2. 環境分離の実現

- **開発環境**: localhost のみ許可
- **ステージング環境**: localhost + ステージングドメイン
- **本番環境**: 本番ドメインのみ許可

### 3. 設定ミスの防止

- **明示的設定**: 環境ごとに明確なオリジン指定
- **デプロイ時検証**: 不正な設定でのデプロイを防止
- **監査可能性**: 設定内容の追跡が容易

## テスト

### ユニットテスト
```python
def test_cors_strict_response(self):
    """CORS厳格化レスポンスのテスト"""
    with patch.dict(os.environ, {'ALLOWED_ORIGINS': 'https://secure-app.com'}):
        response = create_response(200, {'message': 'test'})
        headers = response['headers']
        
        assert headers['Access-Control-Allow-Origin'] == 'https://secure-app.com'
        assert '*' not in headers['Access-Control-Allow-Origin']
```

### 統合テスト
```bash
# 許可されたオリジンからのテスト
curl -H "Origin: https://excel-unlocker.vercel.app" \
     -H "Authorization: Bearer valid-token" \
     https://api.excel-unlocker.com/unlock
# → 成功

# 許可されていないオリジンからのテスト
curl -H "Origin: https://evil.com" \
     -H "Authorization: Bearer valid-token" \
     https://api.excel-unlocker.com/unlock
# → CORS エラー
```

## デプロイメント手順

### 1. 環境変数の設定
```bash
# 開発環境
sam deploy --parameter-overrides \
  Environment=development \
  AllowedOrigins="https://localhost:3000,https://localhost:3001"

# 本番環境
sam deploy --parameter-overrides \
  Environment=production \
  AllowedOrigins="https://excel-unlocker.vercel.app"
```

### 2. 動作確認
```bash
# CORS プリフライトリクエストのテスト
curl -X OPTIONS \
     -H "Origin: https://excel-unlocker.vercel.app" \
     -H "Access-Control-Request-Method: POST" \
     -H "Access-Control-Request-Headers: Content-Type,Authorization" \
     https://api.excel-unlocker.com/unlock

# レスポンスヘッダーの確認
# Access-Control-Allow-Origin: https://excel-unlocker.vercel.app
```

### 3. フロントエンドの確認
- ブラウザの開発者ツールでCORSエラーがないことを確認
- 異なるドメインからのアクセスが拒否されることを確認

## トラブルシューティング

### よくある問題

#### 1. CORS エラーが発生する
```
Access to fetch at 'https://api.excel-unlocker.com/unlock' from origin 'https://new-domain.com' has been blocked by CORS policy
```
**解決方法**: 
- `AllowedOrigins` パラメータに新しいドメインを追加
- SAMテンプレートを再デプロイ

#### 2. 複数オリジンが設定されない
```
Error: API Gateway supports only single origin
```
**解決方法**: 
- API Gatewayは単一オリジンのみサポート
- 最も重要なオリジン（本番ドメイン）を設定
- 開発環境では別途設定

#### 3. S3 CORS エラー
```
CORS policy blocked S3 access
```
**解決方法**: 
- S3バケットのCORS設定を確認
- `AllowedOrigins` がS3にも適用されているか確認

## 監視とログ

### CloudWatch メトリクス
- CORS エラー率の監視
- オリジン別アクセス統計
- 拒否されたリクエストの追跡

### ログ出力
```python
logger.info(f"CORS request from origin: {origin}")
logger.warning(f"CORS blocked origin: {blocked_origin}")
```

## 今後の改善計画

### 短期的改善
1. **動的オリジン管理**: データベースベースの許可オリジン管理
2. **オリジン検証強化**: サブドメインパターンマッチング
3. **監査ログ**: 詳細なCORSアクセスログ

### 長期的改善
1. **WAF統合**: Web Application Firewallとの連携
2. **地理的制限**: 国・地域ベースのアクセス制御
3. **動的ポリシー**: 時間帯・ユーザーベースの制御

## まとめ

CORS設定の厳格化により、以下のセキュリティ強化が実現されました：

1. **ワイルドカード廃止**: 任意オリジンからの攻撃を防止
2. **環境別設定**: 適切な分離とセキュリティ境界
3. **明示的許可**: 必要最小限のオリジンのみ許可
4. **監査可能性**: 設定内容の追跡と検証

この厳格化により、本番環境でのセキュリティリスクが大幅に軽減されます。