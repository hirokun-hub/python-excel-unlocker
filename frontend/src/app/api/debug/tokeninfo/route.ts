import { getServerSession } from "next-auth"
import { NextResponse } from "next/server"
import authOptions from "@/auth"

export async function GET() {
  const session = await getServerSession(authOptions as any)
  const at = (session as any)?.accessToken
  if (!at) return NextResponse.json({ error: "no-access-token" }, { status: 401 })
  const info = await fetch(`https://www.googleapis.com/oauth2/v3/tokeninfo?access_token=${at}`).then(r => r.json())
  const { aud, scope, expires_in } = info
  return NextResponse.json({ aud, scope, expires_in })
}


