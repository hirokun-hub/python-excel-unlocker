import { getToken } from "next-auth/jwt"
import { NextRequest } from "next/server"
import type { JWT } from "next-auth/jwt"

type TokenWithServerFields = JWT & {
  serverAccessToken?: string
  refreshToken?: string
  expiresAt?: number
}

/**
 * サーバーサイドでのみアクセス可能なトークン取得
 * フロントエンドには一切露出されない
 */
export async function getServerAccessToken(req?: NextRequest): Promise<string | null> {
  try {
    if (req) {
      // API ルートでの使用
      const token = await getToken({
        req,
        secret: process.env.NEXTAUTH_SECRET
      })

      const extendedToken = token as TokenWithServerFields | null

      // トークンの有効性を確認
      const accessToken = extendedToken?.serverAccessToken
      const expiresAt = extendedToken?.expiresAt
      
      if (!accessToken) {
        return null
      }
      
      // トークンが期限切れかチェック
      if (expiresAt && Date.now() >= expiresAt * 1000) {
        // 期限切れの場合はnullを返す（呼び出し側でリフレッシュを試行）
        return null
      }
      
      return accessToken
    } else {
      // Server Component での使用
      // セキュリティ上、Server Componentでは直接トークンアクセス不可
      return null
    }
  } catch (error) {
    console.error("Failed to get server access token:", error)
    return null
  }
}

/**
 * サーバーサイドでのリフレッシュトークン取得
 */
export async function getServerRefreshToken(req: NextRequest): Promise<string | null> {
  try {
    const token = await getToken({
      req,
      secret: process.env.NEXTAUTH_SECRET
    })
    const extendedToken = token as TokenWithServerFields | null
    return extendedToken?.refreshToken ?? null
  } catch (error) {
    console.error("Failed to get server refresh token:", error)
    return null
  }
}

/**
 * Google OAuth トークンのリフレッシュ
 */
export async function refreshGoogleToken(refreshToken: string): Promise<{
  access_token: string
  expires_in: number
} | null> {
  try {
    const response = await fetch("https://oauth2.googleapis.com/token", {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: new URLSearchParams({
        client_id: process.env.GOOGLE_CLIENT_ID!,
        client_secret: process.env.GOOGLE_CLIENT_SECRET!,
        refresh_token: refreshToken,
        grant_type: "refresh_token",
      }),
    })

    if (!response.ok) {
      throw new Error(`Token refresh failed: ${response.status}`)
    }

    return await response.json()
  } catch (error) {
    console.error("Failed to refresh Google token:", error)
    return null
  }
}