import NextAuth, { NextAuthOptions, Session } from "next-auth"
import { JWT } from "next-auth/jwt"
import GoogleProvider from "next-auth/providers/google"

// Extend the session object to include the accessToken
interface ExtendedSession extends Session {
  accessToken?: string;
}

const authOptions: NextAuthOptions = {
  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID as string,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET as string,
      authorization: {
        params: {
          scope: "openid email profile https://www.googleapis.com/auth/drive.file",
        },
      },
    }),
  ],
  callbacks: {
    async jwt({ token, account }): Promise<JWT> {
      // Persist the OAuth access_token to the token right after signin
      if (account) {
        token.accessToken = account.access_token
      }
      return token
    },
    async session({ session, token }): Promise<ExtendedSession> {
      // Send properties to the client, like an access_token from a provider.
      const extendedSession = session as ExtendedSession;
      if (token.accessToken) {
        extendedSession.accessToken = token.accessToken as string;
      }
      return extendedSession;
    },
    // Normalize redirect URLs after sign in/sign out to use the configured baseUrl
    async redirect({ url, baseUrl }) {
      // If url is a relative path, join with baseUrl
      if (url.startsWith('/')) return `${baseUrl}${url}`
      try {
        const to = new URL(url)
        const base = new URL(baseUrl)
        // Allow same-origin redirects, otherwise fallback to baseUrl
        return to.origin === base.origin ? to.toString() : base.toString()
      } catch (e) {
        return baseUrl
      }
    },
  },
}

const handler = NextAuth(authOptions)

export { handler as GET, handler as POST }
