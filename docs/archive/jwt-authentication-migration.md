# JWT認証への移行ガイド

## 概要

このドキュメントは、X-User-Emailヘッダー認証からJWT（JSON Web Token）認証への移行について説明します。この移行により、ヘッダ偽装攻撃を防止し、認証システムのセキュリティを根本的に強化します。

## 移行の背景

### 従来の認証方式の問題点

1. **ヘッダ偽装の脆弱性**: X-User-Emailヘッダーは容易に偽装可能
2. **認証の信頼性不足**: サーバー側でトークンの検証が行われていない
3. **セキュリティリスク**: 任意のメールアドレスでAPIアクセスが可能

### JWT認証の利点

1. **暗号学的検証**: Google公開鍵による署名検証
2. **偽装防止**: トークンの改ざんが検出可能
3. **標準準拠**: OAuth 2.0 / OpenID Connectの標準仕様
4. **有効期限管理**: トークンの自動期限切れ

## 実装内容

### 1. フロントエンド変更

#### Auth.js設定の更新
```typescript
// ID Tokenの取得と保存
callbacks: {
  async jwt({ token, account }): Promise<JWT> {
    if (account?.access_token) {
      (token as any).accessToken = account.access_token
      (token as any).scope = account.scope
      // JWT認証用のID Tokenを保存
      (token as any).idToken = account.id_token
    }
    return token
  },
  async session({ session, token }): Promise<Session> {
    (session as any).accessToken = (token as any).accessToken
    (session as any).scope = (token as any).scope
    // JWT認証用のID Tokenをセッションに含める
    (session as any).idToken = (token as any).idToken
    return session
  }
}
```

#### API呼び出しの変更
```typescript
// 変更前（脆弱）
const headers = {
  'Content-Type': 'application/json',
  'X-User-Email': session.user.email, // 偽装可能
}

// 変更後（安全）
const headers = {
  'Content-Type': 'application/json',
  'Authorization': `Bearer ${idToken}`, // JWT検証必要
}
```

### 2. バックエンド変更

#### JWT検証機能の追加
```python
def verify_google_jwt(id_token: str) -> Dict[str, Any]:
    """
    Google ID TokenのJWT検証を行う
    
    - Google公開鍵の取得
    - RSA署名の検証
    - Audience/Issuerの検証
    - 有効期限の確認
    """
    # 実装詳細は auth_utils.py を参照
```

#### 認証フローの変更
```python
# 変更前（脆弱）
user_email = extract_user_from_event(event)  # X-User-Emailヘッダー
auth_result = validate_user_access(user_email)

# 変更後（安全）
user_email = extract_user_from_event(event)  # JWT検証
if not user_email:
    return create_auth_error_response("authentication_failed")
```

### 3. 環境変数の追加

#### AWS SAMテンプレート
```yaml
Environment:
  Variables:
    # JWT認証用のGoogle Client ID
    GOOGLE_CLIENT_ID: "{{resolve:ssm:/excel-unlocker/google-client-id:1}}"
```

#### AWS Systems Manager Parameter Store
```bash
# Google Client IDをParameter Storeに保存
aws ssm put-parameter \
  --name "/excel-unlocker/google-client-id" \
  --value "YOUR_GOOGLE_CLIENT_ID" \
  --type "String" \
  --description "Google OAuth Client ID for JWT verification"
```

## セキュリティ強化効果

### 1. ヘッダ偽装の防止
- **従来**: `curl -H "X-User-Email: admin@example.com"` で偽装可能
- **JWT**: 暗号学的署名により偽装が検出される

### 2. トークンの完全性保証
- **署名検証**: Google公開鍵による署名の検証
- **改ざん検出**: トークン内容の変更が検出可能
- **有効期限**: 自動的な期限切れによるセキュリティ向上

### 3. 標準準拠のセキュリティ
- **OAuth 2.0**: 業界標準の認証フロー
- **OpenID Connect**: ID Tokenによる身元確認
- **RFC 7519**: JWT標準仕様への準拠

## エラーハンドリング

### 認証エラーの種類
1. **authentication_failed**: 一般的な認証失敗
2. **token_expired**: トークンの有効期限切れ
3. **token_invalid**: 無効なトークン形式
4. **unauthorized**: アクセス権限なし

### フロントエンドでの処理
```typescript
// JWT認証エラーの特別処理
if (errorMessage.includes('認証に失敗しました')) {
  toast.error('認証エラーが発生しました。ページを更新して再ログインしてください。')
  // 必要に応じて自動ログアウト
}
```

## テスト

### ユニットテスト
- JWT検証機能のテスト
- 認証エラーレスポンスのテスト
- Google公開鍵取得のテスト

### 統合テスト
- 実際のJWTトークンによる認証テスト
- 無効なトークンでの拒否テスト
- 期限切れトークンの処理テスト

## デプロイメント手順

### 1. 事前準備
```bash
# Google Client IDをParameter Storeに保存
aws ssm put-parameter \
  --name "/excel-unlocker/google-client-id" \
  --value "YOUR_GOOGLE_CLIENT_ID" \
  --type "String"
```

### 2. バックエンドデプロイ
```bash
# 依存関係の更新（PyJWT, cryptography, requests）
cd backend
pip install -r src/requirements.txt

# SAMビルドとデプロイ
sam build
sam deploy
```

### 3. フロントエンドデプロイ
```bash
cd frontend
npm run build
# Vercelへのデプロイ
```

### 4. 動作確認
- ログイン機能の確認
- API呼び出しの成功確認
- 無効なトークンでの拒否確認

## トラブルシューティング

### よくある問題

#### 1. Google Client IDが見つからない
```
Error: GOOGLE_CLIENT_ID environment variable not set
```
**解決方法**: Parameter StoreにクライアントIDを設定

#### 2. JWT検証失敗
```
Error: JWT token validation failed
```
**解決方法**: 
- トークンの有効期限を確認
- Google公開鍵の取得状況を確認
- ネットワーク接続を確認

#### 3. CORS エラー
```
Error: CORS policy blocked
```
**解決方法**: 
- API GatewayのCORS設定を確認
- Authorizationヘッダーが許可されているか確認

## 監視とログ

### ログ出力
- JWT検証の成功/失敗
- 認証エラーの詳細
- Google公開鍵取得の状況

### メトリクス
- 認証成功率
- JWT検証エラー率
- レスポンス時間

## 今後の改善計画

### 短期的改善
1. **CORS設定の厳格化**: ワイルドカード廃止
2. **GitHub OIDC化**: 長期AWSキー廃止
3. **トークン露出対策**: フロントエンドでの適切な管理

### 長期的改善
1. **レート制限**: API呼び出し頻度の制限
2. **WAF設定**: Web Application Firewallの導入
3. **監査ログ**: 詳細なアクセスログの記録

## まとめ

JWT認証への移行により、以下のセキュリティ強化が実現されました：

1. **ヘッダ偽装の根本的防止**
2. **暗号学的検証による信頼性向上**
3. **標準準拠のセキュリティ実装**
4. **適切なエラーハンドリング**

この移行により、本番環境での安全な運用が可能になります。