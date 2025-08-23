import { NextRequest, NextResponse } from "next/server"
import { getServerSession } from "next-auth"
import { authOptions } from "@/auth"

const DRIVE_LIST_URL = "https://www.googleapis.com/drive/v3/files"
const FOLDER_MIME_TYPE = "application/vnd.google-apps.folder"

export async function GET(req: NextRequest) {
  const parentId = req.nextUrl.searchParams.get("parentId") || "root"
  const q = (req.nextUrl.searchParams.get("q") || "").trim()
  const mode = req.nextUrl.searchParams.get("mode") || "" // "children" | ""
  const pageToken = req.nextUrl.searchParams.get("pageToken") || ""

  try {
    const session = await getServerSession(authOptions)
    const accessToken = session?.accessToken
    if (!accessToken) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
    }

    const esc = (s: string) => s.replace(/['\\]/g, "\\$&")
    const baseQuery = `mimeType='${FOLDER_MIME_TYPE}' and trashed=false`
    let query: string

    if (q) {
      // When searching, remove parent constraint for global search
      query = `${baseQuery} and (name contains '${esc(q)}' or fullText contains '${esc(q)}')`
    } else if (mode === "children") {
      // Apply parent constraint only when explicitly requested
      const pid = parentId || "root"
      query = `${baseQuery} and '${esc(pid)}' in parents`
    } else {
      // Default: recent folders
      query = baseQuery
    }

    const params = new URLSearchParams({
      q: query,
      fields: "files(id,name,iconLink,parents,modifiedTime),nextPageToken",
      pageSize: "50",
      corpora: "user",
      includeItemsFromAllDrives: "false",
      supportsAllDrives: "false",
      spaces: "drive",
      orderBy: q ? "modifiedTime desc" : (mode === "children" ? "name" : "viewedByMeTime desc, modifiedTime desc"),
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
