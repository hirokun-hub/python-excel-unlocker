"use client"

import { useSession } from "next-auth/react"
import { uploadToDriveUsingAccessToken } from "@/utils/googleDrive"
import DriveFolderPicker from "@/components/DriveFolderPicker"
import { useEffect, useState } from "react"
import { toast } from "sonner"
import { Button } from "@/components/ui/button"
import { Download, Loader2 } from "lucide-react"
import type { ProcessResult } from "@/app/page"
import type { BreadcrumbItem } from "@/types/drive"

const LS_KEY = "driveFolderSelection"

export function FileResults({ results }: { results: ProcessResult[] }) {
  const { data: session } = useSession()
  const [pickerOpen, setPickerOpen] = useState(false)
  const [folder, setFolder] = useState<BreadcrumbItem | null>(null)
  const [savingToDrive, setSavingToDrive] = useState<string[]>([])

  useEffect(() => {
    const raw = localStorage.getItem(LS_KEY)
    if (raw) try { setFolder(JSON.parse(raw)) } catch { /* ignore */ }
  }, [])

  const handleFolderPick = (pickedFolder: BreadcrumbItem) => {
    setFolder(pickedFolder)
    localStorage.setItem(LS_KEY, JSON.stringify(pickedFolder))
    setPickerOpen(false)
    toast.success(`保存先を「${pickedFolder.name}」に設定しました。`)
  }

  const clearFolderSelection = () => {
    setFolder(null)
    localStorage.removeItem(LS_KEY)
    toast.info("保存先をクリアしました。マイドライブの直下に保存されます。")
  }

  const handleSaveToDrive = async (result: ProcessResult) => {
    if (!session?.accessToken) {
      toast.error("Googleに再ログインしてください。")
      return
    }
    if (!result.downloadUrl) return

    setSavingToDrive(prev => [...prev, result.fileName])
    const toastId = toast.loading(`${result.fileName} をGoogle Driveに保存しています...`)
    try {
      const fileResponse = await fetch(result.downloadUrl)
      if (!fileResponse.ok) throw new Error('ファイルのダウンロードに失敗しました。')
      const fileBlob = await fileResponse.blob()
      await uploadToDriveUsingAccessToken(fileBlob, result.fileName, session.accessToken, { parentId: folder?.id })
      toast.success(`${result.fileName} をGoogle Driveに正常に保存しました。`, { id: toastId })
    } catch (err) {
      console.error(err)
      let errorMessage = 'Google Driveへの保存中に不明なエラーが発生しました。'
      if (err instanceof Error) {
        if (err.message.includes("401")) {
          errorMessage = "Googleアカウントの認証情報が無効です。再ログインしてください。";
        } else if (err.message.includes("403")) {
          errorMessage = "Google Drive APIが未有効か、スコープが不足しています。";
        } else {
          errorMessage = err.message
        }
      }
      toast.error(errorMessage, { id: toastId })
    } finally {
      setSavingToDrive(prev => prev.filter(f => f !== result.fileName))
    }
  }

  const saveAllToDrive = async () => {
    if (!session?.accessToken) {
      toast.error("Googleに再ログインしてください。");
      return;
    }
    if (!folder?.id) {
      toast.error("先に保存先フォルダを選択してください");
      setPickerOpen(true);
      return;
    }

    const filesToSave = results.filter(r => r.status === 'success' && r.downloadUrl);
    if (filesToSave.length === 0) {
      toast.info("保存対象のファイルがありません。");
      return;
    }

    setSavingToDrive(filesToSave.map(r => r.fileName));
    const toastId = toast.loading(`全 ${filesToSave.length} ファイルを保存中...`);

    try {
      const promises = filesToSave.map(async (r) => {
        const blob = await fetch(r.downloadUrl!).then(res => res.blob());
        await uploadToDriveUsingAccessToken(blob, r.fileName, session.accessToken!, { parentId: folder.id });
      });
      await Promise.all(promises);
      toast.success('全ファイルを保存しました', { id: toastId });
    } catch (err) {
      console.error(err);
      let errorMessage = '一括保存中にエラーが発生しました。';
      if (err instanceof Error) {
        if (err.message.includes("401")) {
          errorMessage = "Googleアカウントの認証情報が無効です。再ログインしてください。";
        } else if (err.message.includes("403")) {
          errorMessage = "Google Drive APIが未有効か、スコープが不足しています。";
        } else {
          errorMessage = err.message;
        }
      }
      toast.error(errorMessage, { id: toastId });
    } finally {
      setSavingToDrive([]);
    }
  }

  return (
    <>
      {/* --- Google Drive Destination Bar --- */}
      <div className="p-4 mb-4 border rounded-lg bg-slate-50 dark:bg-slate-800 space-y-3">
        <h3 className="font-semibold">Google Drive 保存先</h3>
        <div className="flex items-center flex-wrap gap-4">
          <Button variant="outline" onClick={() => setPickerOpen(true)}>保存先を選ぶ</Button>
          <div className="text-sm">
            <span className="text-muted-foreground">現在の保存先: </span>
            <span className="font-semibold">{folder?.name ?? "マイドライブ"}</span>
            {folder && <Button variant="ghost" size="sm" className="ml-2" onClick={clearFolderSelection}>クリア</Button>}
          </div>
        </div>
        {results.filter(r => r.status === 'success').length > 0 && (
          <div className="mt-2">
            <Button onClick={saveAllToDrive} disabled={savingToDrive.length > 0}>
              すべてDriveに保存
            </Button>
          </div>
        )}
      </div>
      {/* --- End Google Drive Destination Bar --- */}

      <div className="space-y-3">
        {results.map((result, index) => (
          <div key={index} className={`flex justify-between items-center p-3 rounded-lg ${result.status === 'success' ? 'bg-green-100 dark:bg-green-900/20' : 'bg-red-100 dark:bg-red-900/20'}`}>
            <span className={`font-medium ${result.status === 'success' ? 'text-green-800 dark:text-green-300' : 'text-red-800 dark:text-red-300'}`}>{result.fileName}</span>
            {result.status === 'success' ? (
              <div className="flex gap-2">
                <Button variant="outline" size="sm" onClick={() => handleSaveToDrive(result)} disabled={savingToDrive.includes(result.fileName)}>
                  {savingToDrive.includes(result.fileName) ? (<><Loader2 className="mr-2 h-4 w-4 animate-spin" />保存中</>) : ('Google Driveに保存')}
                </Button>
                <Button asChild size="sm"><a href={result.downloadUrl} download><Download className="w-4 h-4 mr-2" />ダウンロード</a></Button>
              </div>
            ) : (<p className="text-sm text-red-700 dark:text-red-400">{result.message}</p>)}
          </div>
        ))}
      </div>

      <DriveFolderPicker
        open={pickerOpen}
        onClose={() => setPickerOpen(false)}
        onPick={handleFolderPick}
        initialFolderId={folder?.id}
      />
    </>
  )
}
