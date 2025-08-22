import { NextRequest, NextResponse } from "next/server"
import { getServerSession } from "next-auth"
import { authOptions } from "@/auth"
import type { BreadcrumbItem, DriveFolder } from "@/types/drive"

const DRIVE_GET_URL = (id: string) => `https://www.googleapis.com/drive/v3/files/${id}?fields=id,name,parents`
const ROOT_CRUMB: BreadcrumbItem = { id: "root", name: "マイドライブ" }

export async function GET(req: NextRequest) {
  const id = req.nextUrl.searchParams.get("id") || "root"

  try {
    const session = await getServerSession(authOptions)
    const accessToken = session?.accessToken
    if (!accessToken) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
    }

    if (id === "root") {
      return NextResponse.json([ROOT_CRUMB])
    }

    const crumbs: BreadcrumbItem[] = []
    let currentId = id
    for (let i = 0; i < 10; i++) { // Max 10 levels deep to prevent infinite loops
      const res = await fetch(DRIVE_GET_URL(currentId), { headers: { Authorization: `Bearer ${accessToken}` } })
      if (!res.ok) break

      const folder: DriveFolder = await res.json()
      crumbs.unshift({ id: folder.id, name: folder.name })

      const parentId = folder.parents?.[0]
      if (!parentId) break

      // Note: The API might return a root folder ID that is not literally "root"
      // but represents the root. A more robust implementation might check against
      // the user's actual root folder ID. For this app, we assume the parent
      // of a folder without further parents is the root.
      currentId = parentId
    }
    // Always add the root crumb at the beginning
    if (crumbs.length === 0 || crumbs[0].id !== "root") {
        crumbs.unshift(ROOT_CRUMB)
    }


    return NextResponse.json(crumbs)
  } catch (_e) {
    return NextResponse.json({ error: "Internal Server Error" }, { status: 500 })
  }
}


