import { headers } from 'next/headers';

/**
 * サーバーサイドでnonceを取得する関数
 * CSPのscript-srcで使用するnonce値を返す
 */
export async function getNonce(): Promise<string | undefined> {
  try {
    const headersList = await headers();
    return headersList.get('x-nonce') || undefined;
  } catch {
    // クライアントサイドでは使用できないため、undefinedを返す
    return undefined;
  }
}

/**
 * CSPに準拠したスクリプトタグの属性を生成する
 */
export function getScriptProps(nonce?: string) {
  return nonce ? { nonce } : {};
}

/**
 * 開発環境でのCSP設定
 * 開発時は一部制限を緩和する
 */
export function isDevelopment() {
  return process.env.NODE_ENV === 'development';
}

/**
 * CSPポリシーの生成
 */
export function generateCSPPolicy(nonce: string) {
  const policies = [
    "default-src 'self'",
    `script-src 'self' 'nonce-${nonce}' 'strict-dynamic'`,
    "style-src 'self' 'unsafe-inline'", // Tailwind CSSのため
    "img-src 'self' data: https:",
    "font-src 'self' https://fonts.gstatic.com",
    "connect-src 'self' https://api.github.com https://*.execute-api.ap-northeast-1.amazonaws.com https://accounts.google.com https://www.googleapis.com",
    "frame-src 'self' https://accounts.google.com",
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "frame-ancestors 'none'",
  ];

  // 開発環境では制限を緩和
  if (isDevelopment()) {
    policies.push("upgrade-insecure-requests");
  }

  return policies.join('; ');
}