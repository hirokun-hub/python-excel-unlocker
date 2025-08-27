export { uploadToDriveUsingAccessToken } from "../utils/googleDrive"
export type DriveFolder = { id: string; name: string; modifiedTime?: string; iconLink?: string; parents?: string[] }

// Utility to upload a Blob to Google Drive using a direct access token (multipart upload)
export async function uploadToDriveUsingAccessToken(file: Blob, filename: string, accessToken: string) {
  const meta = new Blob([JSON.stringify({ name: filename })], { type: "application/json" })
  const form = new FormData()
  form.append("metadata", meta)
  form.append("file", file, filename)
  const res = await fetch("https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart", {
    method: "POST",
    headers: { Authorization: `Bearer ${accessToken}` },
    body: form,
  })
  if (!res.ok) throw new Error(`Drive upload failed ${res.status}: ${await res.text()}`)
  return res.json()
}


