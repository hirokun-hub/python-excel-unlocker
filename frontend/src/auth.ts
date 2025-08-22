import GoogleProvider from "next-auth/providers/google"
import type { NextAuthOptions } from "next-auth"

const scopes = [
  "openid","email","profile",
  "https://www.googleapis.com/auth/drive.file",          // アップロード用（最小権限）
  "https://www.googleapis.com/auth/drive.metadata.readonly", // フォルダ一覧・検索用
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
    async jwt({ token, account }) {
      if (account) {
        // Persist access token and scope into the JWT
        ;(token as any).accessToken = account.access_token
        ;(token as any).scope = account.scope
        ;(token as any).expires_at = Math.floor(Date.now() / 1000) + (account.expires_in ?? 3600)
      }
      return token
    },
    async session({ session, token }) {
      // Expose accessToken and scope on the session object for client usage
      ;(session as any).accessToken = (token as any).accessToken
      ;(session as any).scope = (token as any).scope
      return session
    },
    // Keep redirect normalization if present elsewhere
    async redirect({ url, baseUrl }) {
      if (url.startsWith('/')) return `${baseUrl}${url}`
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


