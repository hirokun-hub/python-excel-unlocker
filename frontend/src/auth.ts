import GoogleProvider from "next-auth/providers/google"
import type { NextAuthOptions, Session } from "next-auth"
import type { JWT } from "next-auth/jwt"

const scopes = [
  "openid",
  "email",
  "profile",
  "https://www.googleapis.com/auth/drive.file",           // アップロード
  "https://www.googleapis.com/auth/drive.metadata.readonly"// フォルダ一覧
].join(" ")

export const authOptions: NextAuthOptions = {
  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID as string,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET as string,
      authorization: { params: { scope: scopes, access_type: "offline", prompt: "consent" } },
    }),
  ],
  callbacks: {
    async jwt({ token, account }): Promise<JWT> {
      if (account) {
        // アクセストークン/スコープをJWTへ保存
        (token as JWT).accessToken = account.access_token
        ;(token as JWT).scope = account.scope
        // expires_in は string/number/undefined の可能性 → 数値へ安全に変換
        const raw = typeof account.expires_in === "number" ? account.expires_in : Number(account.expires_in ?? 0)
        const seconds = Number.isFinite(raw) && raw > 0 ? raw : 3600
        ;(token as JWT).expires_at = Math.floor(Date.now() / 1000) + seconds
      }
      return token
    },
    async session({ session, token }): Promise<Session> {
      ;(session as any).accessToken = (token as JWT).accessToken
      ;(session as any).scope = (token as JWT).scope
      ;(session as any).expires_at = (token as JWT).expires_at
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


