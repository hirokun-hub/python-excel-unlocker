// Utility to upload a Blob to Google Drive using a direct access token (multipart upload)
export async function uploadToDriveUsingAccessToken(
  file: Blob,
  filename: string,
  accessToken: string,
  opts?: { parentId?: string }
) {
  const metadata: any = { name: filename }
  if (opts?.parentId) metadata.parents = [opts.parentId]
  const form = new FormData()
  form.append("metadata", new Blob([JSON.stringify(metadata)], { type: "application/json" }))
  form.append("file", file, filename)
  const res = await fetch("https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart", {
    method: "POST",
    headers: { Authorization: `Bearer ${accessToken}` },
    body: form,
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`Drive upload failed ${res.status}: ${text}`)
  }
  return res.json()
}
export type DriveFolder = { id: string; name: string; modifiedTime?: string; iconLink?: string; parents?: string[] }


