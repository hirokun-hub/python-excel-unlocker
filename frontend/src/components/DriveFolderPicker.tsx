"use client"
import { useEffect, useMemo, useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import type { DriveFolder } from "@/utils/googleDrive"

type Props = {
  open: boolean
  onClose: () => void
  onPick: (folder: { id: string; name: string }) => void
  initialFolderId?: string | null
}

export default function DriveFolderPicker({ open, onClose, onPick, initialFolderId }: Props) {
  const [folderId, setFolderId] = useState<string>(initialFolderId || "root")
  const [items, setItems] = useState<DriveFolder[]>([])
  const [loading, setLoading] = useState(false)
  const [q, setQ] = useState("")
  const [pageToken, setPageToken] = useState<string | null>(null)
  const [crumbs, setCrumbs] = useState<Array<{ id: string; name: string }>>([{ id: "root", name: "マイドライブ" }])

  const title = useMemo(() => crumbs.map(c => c.name).join(" / "), [crumbs])

  useEffect(() => {
    if (!open) return
    ;(async () => {
      setLoading(true)
      try {
        const bc = await fetch(`/api/drive/breadcrumb?id=${encodeURIComponent(folderId)}`).then(r=>r.json())
        setCrumbs(bc)
        const res = await fetch(`/api/drive/folders?parentId=${encodeURIComponent(folderId)}&q=${encodeURIComponent(q)}`).then(r=>r.json())
        setItems(res.files ?? [])
        setPageToken(res.nextPageToken ?? null)
      } finally {
        setLoading(false)
      }
    })()
  }, [open, folderId, q])

  const loadMore = async () => {
    if (!pageToken) return
    setLoading(true)
    try {
      const res = await fetch(`/api/drive/folders?parentId=${encodeURIComponent(folderId)}&q=${encodeURIComponent(q)}&pageToken=${pageToken}`).then(r=>r.json())
      setItems(prev => [...prev, ...(res.files ?? [])])
      setPageToken(res.nextPageToken ?? null)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={(v)=>!v && onClose()}>
      <DialogContent className="sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>保存先を選択</DialogTitle>
          <div className="text-sm text-muted-foreground truncate">{title}</div>
        </DialogHeader>
        <div className="flex gap-2">
          <Input
            placeholder="フォルダ名で検索"
            value={q}
            onChange={(e)=>setQ(e.target.value)}
          />
          <Button variant="secondary" onClick={()=>setQ("")}>クリア</Button>
        </div>
        <div className="mt-3 max-h-80 overflow-auto rounded border">
          {loading && items.length===0 ? (
            <div className="p-6 text-center text-sm text-muted-foreground">読み込み中…</div>
          ) : (
            <ul className="divide-y">
              {folderId!=="root" && (
                <li className="p-3 hover:bg-muted cursor-pointer" onClick={()=>setFolderId(crumbs[crumbs.length-2]?.id || "root")}>⬆️ 上の階層へ</li>
              )}
              {items.map(f => (
                <li key={f.id} className="p-3 flex items-center justify-between hover:bg-muted">
                  <button className="text-left flex-1" onClick={()=>setFolderId(f.id)}>
                    <div className="font-medium">{f.name}</div>
                    <div className="text-xs text-muted-foreground">{f.modifiedTime ? new Date(f.modifiedTime).toLocaleString() : ""}</div>
                  </button>
                  <Button size="sm" onClick={()=>onPick({ id: f.id, name: f.name })}>ここに保存</Button>
                </li>
              ))}
              {(!loading && items.length===0) && <li className="p-6 text-center text-sm text-muted-foreground">フォルダが見つかりません</li>}
            </ul>
          )}
        </div>
        <div className="flex items-center justify-between">
          <div className="text-xs text-muted-foreground">現在: {title}</div>
          <div className="flex gap-2">
            {pageToken && <Button variant="outline" onClick={loadMore} disabled={loading}>さらに読み込む</Button>}
            <Button onClick={()=>onPick(crumbs[crumbs.length-1])}>このフォルダを選ぶ</Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}


