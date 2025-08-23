import { NextRequest, NextResponse } from "next/server"
import { getServerSession } from "next-auth"
import { authOptions } from "@/auth"

const DRIVE_LIST_URL = "https://www.googleapis.com/drive/v3/files"
const FOLDER_MIME_TYPE = "application/vnd.google-apps.folder"

const esc = (s: string) => s.replace(/['\\]/g, "\\$&")

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url)
  const parentId = searchParams.get("parentId") || "root"
  const q = (searchParams.get("q") || "").trim()
  const pageToken = searchParams.get("pageToken") || undefined

  try {
    const session = await getServerSession(authOptions)
    const accessToken = session?.accessToken
    if (!accessToken) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
    }

    const base = `mimeType='${FOLDER_MIME_TYPE}' and trashed=false`
    const query = q
      ? `${base} and name contains '${esc(q)}'`
      : `${base} and '${esc(parentId)}' in parents`

    const params = new URLSearchParams({
      q: query,
      orderBy: q ? "modifiedTime desc" : "viewedByMeTime desc, modifiedTime desc",
      fields: "files(id,name,iconLink,parents,modifiedTime),nextPageToken",
      pageSize: "50",
      corpora: "user",
      includeItemsFromAllDrives: "false",
      supportsAllDrives: "false",
      spaces: "drive",
    })
    if (pageToken) params.set("pageToken", pageToken)


    const response = await fetch(`${DRIVE_LIST_URL}?${params.toString()}`, {
      headers: { Authorization: `Bearer ${accessToken}` },
      cache: "no-store",
    })

    if (!response.ok) {
      const errorBody = await response.json()
      return NextResponse.json({ error: errorBody.error }, { status: response.status })
    }

    const body = await response.json()
    return NextResponse.json(body)
  } catch (_e) {
    return NextResponse.json({ error: "Internal Server Error" }, { status: 500 })
  }
}
