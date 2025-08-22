import { NextRequest, NextResponse } from "next/server"
import { getServerSession } from "next-auth"
import { authOptions } from "@/auth"
import type { FoldersResponse } from "@/types/drive"

const DRIVE_LIST_URL = "https://www.googleapis.com/drive/v3/files"
const FOLDER_MIME_TYPE = "application/vnd.google-apps.folder"

export async function GET(req: NextRequest) {
  const parentId = req.nextUrl.searchParams.get("parentId") || "root"
  const q = req.nextUrl.searchParams.get("q")?.trim()
  const pageToken = req.nextUrl.searchParams.get("pageToken") || ""

  try {
    const session = await getServerSession(authOptions)
    const accessToken = session?.accessToken
    if (!accessToken) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
    }

    const queryParts = [`'${parentId}' in parents`, `mimeType='${FOLDER_MIME_TYPE}'`, "trashed=false"]
    if (q) queryParts.push(`name contains '${q.replace(/'/g, "\\'")}'`)
    const driveQuery = queryParts.join(" and ")

    const params = new URLSearchParams({
      q: driveQuery,
      pageSize: "50",
      orderBy: "name_natural",
      fields: "nextPageToken,files(id,name,mimeType,modifiedTime,parents,iconLink)",
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

    const body: FoldersResponse = await response.json()
    return NextResponse.json(body)
  } catch (_e) {
    return NextResponse.json({ error: "Internal Server Error" }, { status: 500 })
  }
}


