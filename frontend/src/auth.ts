import GoogleProvider from "next-auth/providers/google"
import type { NextAuthOptions, Session } from "next-auth"
import type { JWT } from "next-auth/jwt"

// OAuth スコープの最小化 - drive.fileのみに限定
const scopes = [
  "openid",
  "email", 
  "profile",
  "https://www.googleapis.com/auth/drive.file", // ファイル作成・編集のみ
].join(" ")

export const authOptions: NextAuthOptions = {
  secret: process.env.NEXTAUTH_SECRET,
  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
      authorization: {
        params: {
          scope: scopes,
          access_type: "offline",
          prompt: "consent",
        },
      },
    }),
  ],
  session: { strategy: "jwt" },
  callbacks: {
    async jwt({ token, account }): Promise<JWT> {
      if (account?.access_token) {
        // サーバーサイドでのみアクセストークンを保持
        // フロントエンドには一切露出しない
        ;(token as any).serverAccessToken = account.access_token
        ;(token as any).refreshToken = account.refresh_token
        ;(token as any).scope = account.scope
        ;(token as any).expiresAt = account.expires_at
        // JWT認証用のID Tokenを保存
        ;(token as any).idToken = account.id_token
      }
      
      // トークンの有効期限チェックとリフレッシュ
      if ((token as any).expiresAt && Date.now() < (token as any).expiresAt * 1000) {
        return token
      }
      
      // トークンが期限切れの場合、リフレッシュを試行
      if ((token as any).refreshToken) {
        try {
          const response = await fetch("https://oauth2.googleapis.com/token", {
            method: "POST",
            headers: {
              "Content-Type": "application/x-www-form-urlencoded",
            },
            body: new URLSearchParams({
              client_id: process.env.GOOGLE_CLIENT_ID!,
              client_secret: process.env.GOOGLE_CLIENT_SECRET!,
              refresh_token: (token as any).refreshToken,
              grant_type: "refresh_token",
            }),
          })
          
          if (response.ok) {
            const refreshedTokens = await response.json()
            ;(token as any).serverAccessToken = refreshedTokens.access_token
            ;(token as any).expiresAt = Math.floor(Date.now() / 1000) + refreshedTokens.expires_in
            // リフレッシュトークンが更新された場合は保存
            if (refreshedTokens.refresh_token) {
              ;(token as any).refreshToken = refreshedTokens.refresh_token
            }
          }
        } catch (error) {
          console.error("Token refresh failed:", error)
          // リフレッシュに失敗した場合、トークンをクリア
          delete (token as any).serverAccessToken
          delete (token as any).refreshToken
        }
      }
      
      return token
    },
    async session({ session, token }): Promise<Session> {
      // フロントエンドにはアクセストークンを一切露出しない
      // JWT認証用のID Tokenのみをセッションに含める
      ;(session as any).idToken = (token as any).idToken
      
      // セッションにアクセストークンが含まれていないことを明示的に確認
      delete (session as any).accessToken
      delete (session as any).access_token
      delete (session as any).refreshToken
      delete (session as any).refresh_token
      
      return session
    },
    async redirect({ url, baseUrl }) {
      if (url.startsWith("/")) return `${baseUrl}${url}`
      try {
        const to = new URL(url)
        const base = new URL(baseUrl)
        return to.origin === base.origin ? to.toString() : base.toString()
      } catch {
        return baseUrl
      }
    },
  },
}

export default authOptions
