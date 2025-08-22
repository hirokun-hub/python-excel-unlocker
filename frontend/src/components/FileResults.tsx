"use client"
import { useSession } from "next-auth/react"
import { uploadToDriveUsingAccessToken } from "@/utils/googleDrive"
import DriveFolderPicker from "@/components/DriveFolderPicker"
import { useEffect, useState } from "react"
import { toast } from "sonner"
import { Button } from "@/components/ui/button"

const LS_KEY = "driveFolderSelection"

export function FileResults({ results }: { results: Array<{ fileName: string; downloadUrl?: string }> }) {
  const { data: session } = useSession()
  const [pickerOpen, setPickerOpen] = useState(false)
  const [folder, setFolder] = useState<{ id: string, name: string } | null>(null)
  useEffect(() => { const raw = localStorage.getItem(LS_KEY); if (raw) try { setFolder(JSON.parse(raw)) } catch {} }, [])
  const applyFolder = (f: { id: string, name: string }) => { setFolder(f); localStorage.setItem(LS_KEY, JSON.stringify(f)); setPickerOpen(false); toast.success("保存先を設定しました", { description: f.name }) }
  const clearFolder = () => { setFolder(null); localStorage.removeItem(LS_KEY) }

  const onSaveToDrive = async (file: { fileName: string; downloadUrl?: string }) => {
    const at = (session as any)?.accessToken
    if (!at) throw new Error("Googleに再ログインしてください（accessTokenなし）")
    const blob = await fetch(file.downloadUrl!).then(r => r.blob())
    await uploadToDriveUsingAccessToken(blob, file.fileName, at, { parentId: folder?.id })
    toast.success("Google Driveに保存しました", { description: file.fileName })
  }
  const saveAll = async () => {
    if (!folder?.id) { toast.error("先に保存先フォルダを選択してください"); setPickerOpen(true); return }
    const at = (session as any)?.accessToken
    if (!at) throw new Error("Googleに再ログインしてください（accessTokenなし）")
    for (const f of results) {
      const blob = await fetch(f.downloadUrl!).then(r => r.blob())
      await uploadToDriveUsingAccessToken(blob, f.fileName, at, { parentId: folder.id })
    }
    toast.success("全ファイルを保存しました", { description: `保存先: ${folder.name}` })
  }

  return (
    <>
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <Button variant="secondary" onClick={()=>setPickerOpen(true)}>保存先を選ぶ</Button>
        {folder ? (
          <>
            <span className="text-sm">保存先: <span className="font-medium">{folder.name}</span></span>
            <Button variant="outline" size="sm" onClick={clearFolder}>クリア</Button>
            <Button onClick={saveAll}>すべてDriveに保存</Button>
          </>
        ) : (
          <span className="text-sm text-muted-foreground">未設定（マイドライブ直下に保存）</span>
        )}
      </div>
      {results.map(file => (
        <div key={file.fileName} className="flex items-center justify-between rounded bg-green-50 p-3 mb-2">
          <span>{file.fileName}</span>
          <div className="flex gap-2">
            <Button onClick={() => onSaveToDrive(file)}>
              Google Driveに保存{folder ? "（設定先）" : ""}
            </Button>
            <Button variant="secondary" onClick={() => window.open(file.downloadUrl!, "_blank")}>ダウンロード</Button>
          </div>
        </div>
      ))}
      <DriveFolderPicker open={pickerOpen} onClose={()=>setPickerOpen(false)} onPick={applyFolder} initialFolderId={folder?.id ?? undefined}/>
    </>
  )
}


