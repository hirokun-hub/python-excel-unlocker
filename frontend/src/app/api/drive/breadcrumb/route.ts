import { NextResponse } from "next/server"
import { getServerSession } from "next-auth"
import { authOptions } from "@/auth"

const DRIVE_GET = (id: string) => `https://www.googleapis.com/drive/v3/files/${id}?fields=id,name,parents`

import { NextRequest } from "next/server";

export async function GET(req: NextRequest) {
  const id = req.nextUrl.searchParams.get("id") || "root"
  const session = await getServerSession(authOptions)
  const at = session?.accessToken
  if (!at) return NextResponse.json({ error: "unauthorized" }, { status: 401 })

  if (id === "root") {
    return NextResponse.json([{ id: "root", name: "マイドライブ" }])
  }
  const crumbs: Array<{ id: string; name: string }> = []
  let cur = id
  for (let i = 0; i < 10; i++) {
    const r = await fetch(DRIVE_GET(cur), { headers: { Authorization: `Bearer ${at}` } })
    if (!r.ok) break
    const f = await r.json()
    crumbs.unshift({ id: f.id, name: f.name })
    const parent = Array.isArray(f.parents) && f.parents[0]
    if (!parent) break
    if (parent === "root") {
      crumbs.unshift({ id: "root", name: "マイドライブ" })
      break
    }
    cur = parent
  }
  return NextResponse.json(crumbs)
}


