import "next-auth"
import "next-auth/jwt"

declare module "next-auth" {
  interface Session {
    // フロントエンドにはアクセストークンを露出しない
    // accessToken?: string  // 削除
    scope?: string
    expires_at?: number
    idToken?: string  // JWT認証用のID Token
  }
}
declare module "next-auth/jwt" {
  interface JWT {
    // サーバーサイドでのみアクセス可能
    serverAccessToken?: string
    refreshToken?: string
    scope?: string
    expires_at?: number
    idToken?: string  // JWT認証用のID Token
  }
}
