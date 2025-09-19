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
        // フロントエンドには露出しない
        ;(token as any).serverAccessToken = account.access_token
        ;(token as any).refreshToken = account.refresh_token
        ;(token as any).scope = account.scope
        // JWT認証用のID Tokenを保存
        ;(token as any).idToken = account.id_token
      }
      return token
    },
    async session({ session, token }): Promise<Session> {
      // フロントエンドにはアクセストークンを露出しない
      // JWT認証用のID Tokenのみをセッションに含める
      ;(session as any).idToken = (token as any).idToken
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
