# Content Security Policy (CSP) 実装ガイド

## 概要

このドキュメントでは、Secure Excel Unlockアプリケーションに実装されたContent Security Policy (CSP)について説明します。CSPはXSS攻撃に対する追加の防御層として機能します。

## 実装されたCSP設定

### 基本ポリシー

```
default-src 'self';
script-src 'self' 'nonce-{nonce}' 'strict-dynamic';
style-src 'self' 'unsafe-inline';
img-src 'self' data: https:;
font-src 'self' https://fonts.gstatic.com;
connect-src 'self' https://api.github.com https://*.execute-api.ap-northeast-1.amazonaws.com https://accounts.google.com https://www.googleapis.com;
frame-src 'self' https://accounts.google.com;
object-src 'none';
base-uri 'self';
form-action 'self';
frame-ancestors 'none';
```

### ポリシーの詳細説明

| ディレクティブ | 設定値 | 説明 |
|---------------|--------|------|
| `default-src` | `'self'` | デフォルトで同一オリジンのみ許可 |
| `script-src` | `'self' 'nonce-{nonce}' 'strict-dynamic'` | nonceベースのスクリプト実行制御 |
| `style-src` | `'self' 'unsafe-inline'` | Tailwind CSSのためインラインスタイル許可 |
| `img-src` | `'self' data: https:` | 画像リソースの読み込み許可 |
| `font-src` | `'self' https://fonts.gstatic.com` | Google Fontsの読み込み許可 |
| `connect-src` | 複数のHTTPS URL | 必要なAPIエンドポイントへの接続許可 |
| `frame-src` | `'self' https://accounts.google.com` | Google OAuth用のフレーム許可 |
| `object-src` | `'none'` | オブジェクト埋め込みを完全禁止 |
| `base-uri` | `'self'` | base要素のURIを同一オリジンに制限 |
| `form-action` | `'self'` | フォーム送信先を同一オリジンに制限 |
| `frame-ancestors` | `'none'` | フレーム埋め込みを完全禁止 |

## 実装ファイル

### 1. ミドルウェア (`frontend/src/middleware.ts`)

```typescript
import { NextRequest, NextResponse } from 'next/server';
import { randomBytes } from 'crypto';

export function middleware(request: NextRequest) {
  // nonceを生成
  const nonce = randomBytes(16).toString('base64');
  
  // CSPヘッダーを設定
  const cspHeader = generateCSPPolicy(nonce);
  
  const response = NextResponse.next();
  response.headers.set('Content-Security-Policy', cspHeader);
  response.headers.set('x-nonce', nonce);
  
  return response;
}
```

### 2. CSPユーティリティ (`frontend/src/lib/csp.ts`)

```typescript
export async function getNonce(): Promise<string | undefined> {
  const headersList = await headers();
  return headersList.get('x-nonce') || undefined;
}

export function generateCSPPolicy(nonce: string) {
  // CSPポリシーの生成ロジック
}
```

### 3. レイアウト更新 (`frontend/src/app/layout.tsx`)

```typescript
export default async function RootLayout({ children }: Props) {
  const nonce = await getNonce();
  
  return (
    <html lang="ja">
      <head>
        <meta httpEquiv="Content-Security-Policy" content={cspPolicy} />
      </head>
      <body>
        <AuthProvider nonce={nonce}>{children}</AuthProvider>
      </body>
    </html>
  );
}
```

## セキュリティ効果

### XSS攻撃の防止

1. **インラインスクリプト制御**: nonceなしのインラインスクリプトは実行されない
2. **外部スクリプト制限**: 許可されたオリジンからのスクリプトのみ実行可能
3. **動的スクリプト制御**: `'strict-dynamic'`により信頼されたスクリプトのみが新しいスクリプトを作成可能

### その他のセキュリティ強化

1. **フレーム埋め込み防止**: `frame-ancestors 'none'`によりクリックジャッキング攻撃を防止
2. **オブジェクト埋め込み禁止**: `object-src 'none'`により悪意のあるプラグインの実行を防止
3. **フォーム送信制限**: `form-action 'self'`により外部への意図しないデータ送信を防止

## 開発時の注意事項

### CSPテストコンポーネント

開発環境では`CSPTest`コンポーネントが表示され、CSPの動作状況を確認できます：

```typescript
// 開発環境でのみ表示されるCSPテストコンポーネント
<CSPTest />
```

### CSP違反の確認方法

1. **ブラウザコンソール**: CSP違反は自動的にコンソールに出力される
2. **ネットワークタブ**: ブロックされたリソースの読み込み失敗を確認
3. **CSPテストコンポーネント**: 開発環境での視覚的な確認

## トラブルシューティング

### よくある問題と解決方法

#### 1. インラインスクリプトが実行されない

**症状**: JavaScriptが動作しない、コンソールにCSP違反エラー

**解決方法**:
```typescript
// 悪い例: nonceなしのインラインスクリプト
<script>console.log('test')</script>

// 良い例: nonceありのインラインスクリプト
<script nonce={nonce}>console.log('test')</script>
```

#### 2. 外部リソースが読み込まれない

**症状**: 画像、フォント、APIが読み込まれない

**解決方法**: CSPポリシーに必要なドメインを追加
```typescript
// connect-srcに新しいAPIドメインを追加
"connect-src 'self' https://new-api.example.com"
```

#### 3. Google OAuth認証が失敗する

**症状**: 認証ポップアップが表示されない、認証フローが完了しない

**解決方法**: frame-srcとconnect-srcにGoogleドメインが含まれていることを確認
```typescript
"frame-src 'self' https://accounts.google.com",
"connect-src 'self' https://accounts.google.com https://www.googleapis.com"
```

## 本番環境での設定

### 環境別の設定

```typescript
// 開発環境: より緩い設定
if (isDevelopment()) {
  policies.push("upgrade-insecure-requests");
}

// 本番環境: より厳格な設定
if (isProduction()) {
  // 追加の制限を適用
}
```

### モニタリング

本番環境では以下の方法でCSPの効果を監視：

1. **CSP違反レポート**: ブラウザからの違反レポートを収集
2. **ログ監視**: サーバーログでCSP関連のエラーを監視
3. **セキュリティスキャン**: 定期的なセキュリティテストでCSPの効果を確認

## 今後の改善計画

### Phase 1: 基本実装 ✅
- nonceベースのCSP実装
- 基本的なXSS防止
- 開発環境でのテスト機能

### Phase 2: 強化 (将来実装)
- CSP違反レポートの収集
- より厳格なstyle-src設定（Tailwind CSS最適化後）
- 動的なCSPポリシー調整

### Phase 3: 監視・運用 (将来実装)
- CSP違反の自動アラート
- セキュリティメトリクスの収集
- 定期的なCSPポリシーの見直し

## 参考資料

- [MDN - Content Security Policy](https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP)
- [Google Web Fundamentals - CSP](https://developers.google.com/web/fundamentals/security/csp)
- [OWASP - Content Security Policy](https://owasp.org/www-community/controls/Content_Security_Policy)