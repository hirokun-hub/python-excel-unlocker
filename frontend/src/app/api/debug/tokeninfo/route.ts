import { NextRequest, NextResponse } from "next/server"
import { getServerAccessToken, refreshGoogleToken, getServerRefreshToken } from "@/lib/serverAuth"

export async function GET(req: NextRequest) {
  // サーバーサイドでのみアクセス可能なトークンを取得
  let accessToken = await getServerAccessToken(req);
  
  if (!accessToken) {
    // リフレッシュトークンを使用してアクセストークンを更新
    const refreshToken = await getServerRefreshToken(req);
    if (refreshToken) {
      const refreshed = await refreshGoogleToken(refreshToken);
      if (refreshed) {
        accessToken = refreshed.access_token;
      }
    }
  }

  if (!accessToken) {
    return NextResponse.json({ error: "no-access-token" }, { status: 401 });
  }

  try {
    const info = await fetch(`https://www.googleapis.com/oauth2/v3/tokeninfo?access_token=${accessToken}`).then(r => r.json());
    const { aud, scope, expires_in } = info;
    return NextResponse.json({ aud, scope, expires_in });
  } catch (error) {
    console.error("Token info error:", error);
    return NextResponse.json({ error: "token-info-failed" }, { status: 500 });
  }
}


