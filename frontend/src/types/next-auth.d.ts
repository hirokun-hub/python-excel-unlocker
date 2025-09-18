import "next-auth"
import "next-auth/jwt"

declare module "next-auth" {
  interface Session {
    accessToken?: string
    scope?: string
    expires_at?: number
    idToken?: string  // JWT認証用のID Token
  }
}
declare module "next-auth/jwt" {
  interface JWT {
    accessToken?: string
    scope?: string
    expires_at?: number
    idToken?: string  // JWT認証用のID Token
  }
}
