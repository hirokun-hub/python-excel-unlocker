import { NextRequest, NextResponse } from "next/server"
import { getServerAccessToken, refreshGoogleToken, getServerRefreshToken } from "@/lib/serverAuth"
import { google, drive_v3 } from "googleapis"

export async function POST(req: NextRequest) {
  try {
    // サーバーサイドでのみアクセス可能なトークンを取得
    let accessToken = await getServerAccessToken(req)
    
    if (!accessToken) {
      // リフレッシュトークンを使用してアクセストークンを更新
      const refreshToken = await getServerRefreshToken(req)
      if (refreshToken) {
        const refreshed = await refreshGoogleToken(refreshToken)
        if (refreshed) {
          accessToken = refreshed.access_token
        }
      }
    }

    if (!accessToken) {
      return NextResponse.json(
        { error: "認証が必要です。再ログインしてください。" },
        { status: 401 }
      )
    }

    const formData = await req.formData()
    const file = formData.get("file") as File
    const filename = formData.get("filename") as string
    const parentId = formData.get("parentId") as string | null

    if (!file || !filename) {
      return NextResponse.json(
        { error: "ファイルとファイル名が必要です。" },
        { status: 400 }
      )
    }

    // Google Drive API を使用してファイルをアップロード
    const auth = new google.auth.OAuth2()
    auth.setCredentials({ access_token: accessToken })
    const drive = google.drive({ version: "v3", auth })

    const metadata: drive_v3.Schema$File = { name: filename }
    if (parentId && parentId !== "root") {
      metadata.parents = [parentId]
    }

    const media = {
      mimeType: file.type,
      body: Buffer.from(await file.arrayBuffer()),
    }

    const response = await drive.files.create({
      requestBody: metadata,
      media: media,
      fields: "id,name,webViewLink",
    })

    return NextResponse.json({
      success: true,
      file: response.data,
      message: "ファイルがGoogle Driveに保存されました。"
    })

  } catch (error) {
    console.error("Google Drive upload error:", error)
    
    // エラーの種類に応じた適切なレスポンス
    if (error instanceof Error) {
      if (error.message.includes("401") || error.message.includes("unauthorized")) {
        return NextResponse.json(
          { error: "認証が切れました。再ログインしてください。" },
          { status: 401 }
        )
      }
      if (error.message.includes("403") || error.message.includes("forbidden")) {
        return NextResponse.json(
          { error: "Google Drive APIへのアクセス権限がありません。" },
          { status: 403 }
        )
      }
    }

    return NextResponse.json(
      { error: "Google Driveへのアップロードに失敗しました。" },
      { status: 500 }
    )
  }
}