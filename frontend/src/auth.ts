import GoogleProvider from "next-auth/providers/google"
import type { NextAuthOptions, Session } from "next-auth"
import type { JWT } from "next-auth/jwt"

type ExtendedJWT = JWT & {
  serverAccessToken?: string
  refreshToken?: string
  scope?: string
  expiresAt?: number
  idToken?: string
}

type GoogleTokenRefreshResponse = {
  access_token: string
  expires_in: number
  refresh_token?: string
  scope?: string
  token_type?: string
}

type SessionWithLegacyTokens = Session & {
  idToken?: string
  accessToken?: unknown
  access_token?: unknown
  refreshToken?: unknown
  refresh_token?: unknown
}

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
      let extendedToken: ExtendedJWT = { ...token }

      if (account?.access_token) {
        extendedToken = {
          ...extendedToken,
          serverAccessToken: account.access_token,
          refreshToken: account.refresh_token,
          scope: account.scope,
          expiresAt: account.expires_at,
          idToken: account.id_token,
        }
      }

      if (extendedToken.expiresAt && Date.now() < extendedToken.expiresAt * 1000) {
        return extendedToken
      }

      if (extendedToken.refreshToken) {
        try {
          const response = await fetch("https://oauth2.googleapis.com/token", {
            method: "POST",
            headers: {
              "Content-Type": "application/x-www-form-urlencoded",
            },
            body: new URLSearchParams({
              client_id: process.env.GOOGLE_CLIENT_ID!,
              client_secret: process.env.GOOGLE_CLIENT_SECRET!,
              refresh_token: extendedToken.refreshToken,
              grant_type: "refresh_token",
            }),
          })

          if (response.ok) {
            const refreshedTokens: GoogleTokenRefreshResponse = await response.json()
            extendedToken = {
              ...extendedToken,
              serverAccessToken: refreshedTokens.access_token,
              expiresAt: Math.floor(Date.now() / 1000) + refreshedTokens.expires_in,
            }

            if (refreshedTokens.refresh_token) {
              extendedToken = {
                ...extendedToken,
                refreshToken: refreshedTokens.refresh_token,
              }
            }
          }
        } catch (error) {
          console.error("Token refresh failed:", error)
          extendedToken = {
            ...extendedToken,
            serverAccessToken: undefined,
            refreshToken: undefined,
          }
        }
      }

      return extendedToken
    },
    async session({ session, token }): Promise<Session> {
      const extendedToken = token as ExtendedJWT

      const sessionWithIdToken: SessionWithLegacyTokens = {
        ...session,
        idToken: extendedToken.idToken,
      }

      delete sessionWithIdToken.accessToken
      delete sessionWithIdToken.access_token
      delete sessionWithIdToken.refreshToken
      delete sessionWithIdToken.refresh_token

      return sessionWithIdToken
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
