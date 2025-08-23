"use client"
import { useEffect, useMemo, useState, useCallback } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { toast } from "sonner"

// A simple debounce function
function debounce<T extends (...args: any[]) => void>(func: T, wait: number): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout;
  return function(...args: Parameters<T>) {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
}

export default function DriveFolderPicker({ open, onClose, onPick, initialFolderId }: any) {
  const [folderId, setFolderId] = useState<string>(initialFolderId || "root")
  const [items, setItems] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [searchQuery, setSearchQuery] = useState("")
  const [debouncedQuery, setDebouncedQuery] = useState("")
  const [pageToken, setPageToken] = useState<string | null>(null)
  const [crumbs, setCrumbs] = useState<any[]>([{ id: "root", name: "マイドライブ" }])

  const title = useMemo(() => crumbs.map(c => c.name).join(" / "), [crumbs])

  // Debounce the search query
  const debouncedSetQuery = useCallback(debounce(setDebouncedQuery, 300), []);
  useEffect(() => {
    debouncedSetQuery(searchQuery);
  }, [searchQuery, debouncedSetQuery]);


  useEffect(() => {
    if (!open) return
    ;(async () => {
      setLoading(true)
      try {
        // Fetch breadcrumbs
        const bcRes = await fetch(`/api/drive/breadcrumb?id=${encodeURIComponent(folderId)}`, { cache: "no-store" })
        if (bcRes.status === 401) {
          toast.error("Google へのログインが切れました。再ログインしてください。")
          return
        }
        const bc = await bcRes.json()
        setCrumbs(bc)

        // Fetch folders
        const params = new URLSearchParams({
          parentId: folderId,
          q: debouncedQuery,
        })
        const folderRes = await fetch(`/api/drive/folders?${params.toString()}`, { cache: "no-store" })
        if (folderRes.status === 401) {
          toast.error("Google へのログインが切れました。再ログインしてください。")
          return
        }
        const folderData = await folderRes.json()
        setItems(folderData.files ?? [])
        setPageToken(folderData.nextPageToken ?? null)
      } finally {
        setLoading(false)
      }
    })()
  }, [open, folderId, debouncedQuery])

  const handleFolderClick = (folder: any) => {
    setSearchQuery(""); // Reset search when navigating
    setDebouncedQuery("");
    setFolderId(folder.id);
  }

  const loadMore = async () => {
    if (!pageToken) return
    setLoading(true)
    try {
      const params = new URLSearchParams({
        parentId: folderId,
        q: debouncedQuery,
        mode: debouncedQuery ? "" : "children",
        pageToken: pageToken,
      })
      const res = await fetch(`/api/drive/folders?${params.toString()}`, { cache: "no-store" })
      if (res.status === 401) {
        toast.error("Google へのログインが切れました。再ログインしてください。")
        return
      }
      const data = await res.json()
      setItems(prev => [...prev, ...(data.files ?? [])])
      setPageToken(data.nextPageToken ?? null)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>保存先を選択</DialogTitle>
          <div className="text-sm text-muted-foreground truncate">{title}</div>
        </DialogHeader>
        <div className="flex gap-2">
          <Input
            placeholder="フォルダ名で検索（My Drive全体）"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          <Button variant="secondary" onClick={() => setSearchQuery("")}>クリア</Button>
        </div>
        <div className="mt-3 max-h-80 overflow-auto rounded border">
          {loading && items.length === 0 ? (
            <div className="p-6 text-center text-sm text-muted-foreground">読み込み中…</div>
          ) : (
            <ul className="divide-y">
              {folderId !== "root" && !searchQuery && (
                <li className="p-3 hover:bg-muted cursor-pointer" onClick={() => handleFolderClick(crumbs[crumbs.length - 2] || { id: "root" })}>⬆️ 上の階層へ</li>
              )}
              {items.map(f => (
                <li key={f.id} className="p-3 flex items-center justify-between hover:bg-muted">
                  <button className="text-left flex-1" onClick={() => handleFolderClick(f)}>
                    <div className="font-medium">{f.name}</div>
                    <div className="text-xs text-muted-foreground">{f.modifiedTime ? new Date(f.modifiedTime).toLocaleString() : ""}</div>
                  </button>
                  <Button size="sm" onClick={() => onPick({ id: f.id, name: f.name })}>ここに保存</Button>
                </li>
              ))}
              {(!loading && items.length === 0) && <li className="p-6 text-center text-sm text-muted-foreground">フォルダが見つかりません</li>}
            </ul>
          )}
        </div>
        <div className="flex items-center justify-between">
          <div className="text-xs text-muted-foreground">現在: {title}</div>
          <div className="flex gap-2">
            {pageToken && <Button variant="outline" onClick={loadMore} disabled={loading}>さらに読み込む</Button>}
            <Button onClick={() => onPick(crumbs[crumbs.length - 1])}>このフォルダを選ぶ</Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
