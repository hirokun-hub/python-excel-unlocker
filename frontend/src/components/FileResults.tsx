"use client"
import { useSession } from "next-auth/react"
import DriveFolderPicker from "@/components/DriveFolderPicker"
import { useEffect, useState } from "react"
import { toast } from "sonner"
import { Button } from "@/components/ui/button"
import { Download, Loader2 } from "lucide-react"
import type { ProcessResult } from "@/types/process-result"

const LS_KEY = "driveFolderSelection"

export function FileResults({ results }: { results: ProcessResult[] }) {
  const { data: session } = useSession()
  const [pickerOpen, setPickerOpen] = useState(false)
  const [folder, setFolder] = useState<{ id: string, name: string } | null>(null)
  const [savingToDrive, setSavingToDrive] = useState<string[]>([])

  useEffect(() => {
    const raw = localStorage.getItem(LS_KEY);
    if (raw) try { setFolder(JSON.parse(raw)) } catch {}
  }, [])

  const applyFolder = (f: { id: string, name: string }) => {
    setFolder(f);
    localStorage.setItem(LS_KEY, JSON.stringify(f));
    setPickerOpen(false);
    toast.success("保存先を設定しました", { description: f.name })
  }

  const clearFolder = () => {
    setFolder(null);
    localStorage.removeItem(LS_KEY)
  }

  const handleSave = async (file: ProcessResult) => {
    if (!session) {
      toast.error("Googleに再ログインしてください。");
      return;
    }
    if (!file.downloadUrl) return;

    setSavingToDrive(prev => [...prev, file.fileName]);
    const toastId = toast.loading(`${file.fileName} をGoogle Driveに保存しています...`);
    
    try {
      // ファイルをダウンロード
      const blob = await fetch(file.downloadUrl).then(r => r.blob());
      
      // サーバー経由でGoogle Driveにアップロード
      const formData = new FormData();
      formData.append("file", blob);
      formData.append("filename", file.fileName);
      if (folder?.id) {
        formData.append("parentId", folder.id);
      }

      const response = await fetch("/api/drive/upload", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || "アップロードに失敗しました");
      }

      const result = await response.json();
      toast.success("Google Driveに保存しました", { 
        id: toastId, 
        description: file.fileName 
      });
    } catch (err) {
      console.error(err);
      let errorMessage = 'Google Driveへの保存中にエラーが発生しました。';
      if (err instanceof Error) {
        errorMessage = err.message;
      }
      toast.error(errorMessage, { id: toastId });
    } finally {
      setSavingToDrive(prev => prev.filter(f => f !== file.fileName));
    }
  }

  const saveAll = async () => {
    if (!session) {
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
      // 並列でサーバー経由アップロード
      const promises = filesToSave.map(async (r) => {
        const blob = await fetch(r.downloadUrl!).then(res => res.blob());
        
        const formData = new FormData();
        formData.append("file", blob);
        formData.append("filename", r.fileName);
        formData.append("parentId", folder.id);

        const response = await fetch("/api/drive/upload", {
          method: "POST",
          body: formData,
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.error || `${r.fileName}のアップロードに失敗しました`);
        }

        return response.json();
      });

      await Promise.all(promises);
      toast.success('全ファイルを保存しました', { id: toastId });
    } catch (err) {
      console.error(err);
      let errorMessage = '一括保存中にエラーが発生しました。';
      if (err instanceof Error) {
        errorMessage = err.message;
      }
      toast.error(errorMessage, { id: toastId });
    } finally {
      setSavingToDrive([]);
    }
  }

  return (
    <>
      <div className="p-4 mb-4 border rounded-lg bg-slate-50 dark:bg-slate-800 space-y-3">
        <h3 className="font-semibold">Google Drive 保存先</h3>
        <div className="flex items-center flex-wrap gap-4">
          <Button variant="outline" onClick={() => setPickerOpen(true)}>保存先を選ぶ</Button>
          <div className="text-sm">
            <span className="text-muted-foreground">現在の保存先: </span>
            <span className="font-semibold">{folder?.name ?? "マイドライブ"}</span>
            {folder && <Button variant="ghost" size="sm" className="ml-2" onClick={clearFolder}>クリア</Button>}
          </div>
        </div>
        {results.filter(r => r.status === 'success').length > 0 && (
          <div className="mt-2">
            <Button onClick={saveAll} disabled={savingToDrive.length > 0}>
              すべてDriveに保存
            </Button>
          </div>
        )}
      </div>

      <div className="space-y-3">
        {results.map((result, index) => (
          <div key={index} className={`flex justify-between items-center p-3 rounded-lg ${result.status === 'success' ? 'bg-green-100 dark:bg-green-900/20' : 'bg-red-100 dark:bg-red-900/20'}`}>
            <span className={`font-medium ${result.status === 'success' ? 'text-green-800 dark:text-green-300' : 'text-red-800 dark:text-red-300'}`}>{result.fileName}</span>
            {result.status === 'success' ? (
              <div className="flex gap-2">
                <Button variant="outline" size="sm" onClick={() => handleSave(result)} disabled={savingToDrive.includes(result.fileName)}>
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
        onPick={applyFolder}
        initialFolderId={folder?.id}
      />
    </>
  )
}
