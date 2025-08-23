import { NextResponse } from "next/server"
import { getServerSession } from "next-auth"
import { authOptions } from "@/auth"

const DRIVE_LIST = "https://www.googleapis.com/drive/v3/files"
const FOLDER_MIME = "application/vnd.google-apps.folder"

import { NextRequest } from "next/server";

export async function GET(req: NextRequest) {
  const parentId = req.nextUrl.searchParams.get("parentId") || "root"
  const q = req.nextUrl.searchParams.get("q")?.trim()
  const pageToken = req.nextUrl.searchParams.get("pageToken") || ""

  const session = await getServerSession(authOptions)
  const at = session?.accessToken
  if (!at) return NextResponse.json({ error: "unauthorized" }, { status: 401 })

  const parts = [`'${parentId}' in parents`, `mimeType='${FOLDER_MIME}'`, "trashed=false"]
  if (q) parts.push(`name contains '${q.replace(/'/g, "\\'")}'`)
  const driveQ = parts.join(" and ")

  const params = new URLSearchParams({
    q: driveQ,
    pageSize: "50",
    orderBy: "name_natural",
    fields: "nextPageToken, files(id,name,mimeType,modifiedTime,parents,iconLink)",
    corpora: "user",
    includeItemsFromAllDrives: "false",
    supportsAllDrives: "false",
    spaces: "drive",
  })
  if (pageToken) params.set("pageToken", pageToken)

  const res = await fetch(`${DRIVE_LIST}?${params.toString()}`, {
    headers: { Authorization: `Bearer ${at}` },
    cache: "no-store",
  })
  const body = await res.json()
  return NextResponse.json(body, { status: res.status })
}


