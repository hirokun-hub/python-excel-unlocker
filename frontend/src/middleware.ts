import { NextResponse } from 'next/server';

export function middleware() {
  // Edge Runtime対応のnonce生成
  const nonce = generateNonce();
  
  // CSPヘッダーを設定
  const cspHeader = [
    "default-src 'self'",
    `script-src 'self' 'nonce-${nonce}' 'strict-dynamic'`,
    `style-src 'self' 'unsafe-inline'`, // Tailwind CSSのため一時的に許可
    "img-src 'self' data: https:",
    "font-src 'self' https://fonts.gstatic.com",
    "connect-src 'self' https://api.github.com https://*.execute-api.ap-northeast-1.amazonaws.com https://accounts.google.com https://www.googleapis.com",
    "frame-src 'self' https://accounts.google.com",
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "frame-ancestors 'none'",
    "upgrade-insecure-requests"
  ].join('; ');

  // レスポンスを作成
  const response = NextResponse.next();
  
  // CSPヘッダーを設定
  response.headers.set('Content-Security-Policy', cspHeader);
  
  // nonceをリクエストヘッダーに追加（レイアウトで使用するため）
  response.headers.set('x-nonce', nonce);
  
  // その他のセキュリティヘッダーも設定
  response.headers.set('X-Frame-Options', 'DENY');
  response.headers.set('X-Content-Type-Options', 'nosniff');
  response.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin');
  response.headers.set('Permissions-Policy', 'camera=(), microphone=(), geolocation=()');
  
  return response;
}

/**
 * Edge Runtime対応のnonce生成関数
 * crypto.randomBytesの代替実装
 */
function generateNonce(): string {
  const array = new Uint8Array(16);
  crypto.getRandomValues(array);
  return btoa(String.fromCharCode(...array))
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=/g, '');
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    '/((?!api|_next/static|_next/image|favicon.ico).*)',
  ],
};