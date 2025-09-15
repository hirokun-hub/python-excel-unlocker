"use client";
import { useEffect, useMemo, useState, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { toast } from "sonner";

const debounce = <T extends (...args: any[]) => void>(
  func: T,
  wait: number,
): ((...args: Parameters<T>) => void) => {
  let timeout: NodeJS.Timeout;
  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
};

const jstFormatter = new Intl.DateTimeFormat("ja-JP", {
  timeZone: "Asia/Tokyo",
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
  hour: "2-digit",
  minute: "2-digit",
});

const formatModified = (dtIso: string) =>
  `更新日: ${jstFormatter.format(new Date(dtIso))}`;

export default function DriveFolderPicker({
  open,
  onClose,
  onPick,
  initialFolderId,
}: any) {
  const [folderId, setFolderId] = useState<string>(initialFolderId || "root");
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");
  const [pageToken, setPageToken] = useState<string | null>(null);
  const [crumbs, setCrumbs] = useState<any[]>([
    { id: "root", name: "マイドライブ" },
  ]);

  const isSearching = !!debouncedQuery;
  const title = useMemo(
    () => (isSearching ? "検索結果" : crumbs.map((c) => c.name).join(" / ")),
    [crumbs, isSearching],
  );

  const debouncedSetQuery = useCallback(
    debounce((q: string) => {
      setDebouncedQuery(q);
      setItems([]); // Reset items when search query changes
      setPageToken(null);
    }, 300),
    [],
  );

  useEffect(() => {
    debouncedSetQuery(searchQuery);
  }, [searchQuery, debouncedSetQuery]);

  useEffect(() => {
    if (!open) return;
    const fetchFolders = async () => {
      setLoading(true);
      try {
        if (!isSearching) {
          const bcRes = await fetch(
            `/api/drive/breadcrumb?id=${encodeURIComponent(folderId)}`,
            { cache: "no-store" },
          );
          if (!bcRes.ok) throw new Error("Failed to fetch breadcrumbs");
          setCrumbs(await bcRes.json());
        }

        const params = new URLSearchParams();
        if (isSearching) {
          params.set("q", debouncedQuery);
        } else {
          params.set("parentId", folderId);
        }

        const folderRes = await fetch(
          `/api/drive/folders?${params.toString()}`,
          { cache: "no-store" },
        );
        if (folderRes.status === 401) {
          toast.error(
            "Google へのログインが切れました。再ログインしてください。",
          );
          return;
        }
        if (!folderRes.ok) throw new Error("Failed to fetch folders");

        const folderData = await folderRes.json();
        setItems(folderData.files ?? []);
        setPageToken(folderData.nextPageToken ?? null);
      } catch (err) {
        console.error(err);
        toast.error("フォルダの読み込みに失敗しました。");
      } finally {
        setLoading(false);
      }
    };
    fetchFolders();
  }, [open, folderId, debouncedQuery, isSearching]);

  const handleFolderClick = (folder: any) => {
    setSearchQuery("");
    setDebouncedQuery("");
    setFolderId(folder.id);
  };

  const loadMore = async () => {
    if (!pageToken) return;
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (isSearching) {
        params.set("q", debouncedQuery);
      } else {
        params.set("parentId", folderId);
      }
      params.set("pageToken", pageToken);

      const res = await fetch(`/api/drive/folders?${params.toString()}`, {
        cache: "no-store",
      });
      if (res.status === 401) {
        toast.error(
          "Google へのログインが切れました。再ログインしてください。",
        );
        return;
      }
      const data = await res.json();
      setItems((prev) => [...prev, ...(data.files ?? [])]);
      setPageToken(data.nextPageToken ?? null);
    } finally {
      setLoading(false);
    }
  };

  const currentFolder = crumbs[crumbs.length - 1];

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>保存先を選択</DialogTitle>
          <div className="text-sm text-muted-foreground truncate">{title}</div>
        </DialogHeader>
        <div className="flex gap-2">
          <Input
            placeholder="全ドライブからフォルダ名で検索"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          <Button variant="secondary" onClick={() => setSearchQuery("")}>
            クリア
          </Button>
        </div>
        <div className="mt-3 max-h-80 min-h-[20rem] overflow-auto rounded border">
          {loading && items.length === 0 ? (
            <div className="p-6 text-center text-sm text-muted-foreground">
              読み込み中…
            </div>
          ) : (
            <ul className="divide-y">
              {!isSearching && folderId !== "root" && (
                <li
                  className="p-3 hover:bg-muted cursor-pointer"
                  onClick={() =>
                    handleFolderClick(
                      crumbs[crumbs.length - 2] || { id: "root" },
                    )
                  }
                >
                  ⬆️ 上の階層へ
                </li>
              )}
              {items.map((f) => (
                <li
                  key={f.id}
                  className="p-3 flex items-center justify-between hover:bg-muted"
                >
                  <button
                    className="text-left flex-1"
                    onClick={() => handleFolderClick(f)}
                  >
                    <div className="font-medium">{f.name}</div>
                    <div className="mt-1 text-xs text-muted-foreground space-y-0.5">
                      {f.modifiedTime && (
                        <div>{formatModified(f.modifiedTime)}</div>
                      )}
                      {f.displayPath && <div>パス: {f.displayPath}</div>}
                    </div>
                  </button>
                  {!isSearching && (
                    <Button
                      size="sm"
                      onClick={() => onPick({ id: f.id, name: f.name })}
                    >
                      ここに保存
                    </Button>
                  )}
                </li>
              ))}
              {!loading && items.length === 0 && (
                <li className="p-6 text-center text-sm text-muted-foreground">
                  フォルダが見つかりません
                </li>
              )}
            </ul>
          )}
        </div>
        <div className="flex items-center justify-between pt-2">
          <div className="text-xs text-muted-foreground truncate">
            {!isSearching && `現在のフォルダ: ${currentFolder.name}`}
          </div>
          <div className="flex gap-2">
            {pageToken && (
              <Button variant="outline" onClick={loadMore} disabled={loading}>
                さらに読み込む
              </Button>
            )}
            {!isSearching && (
              <Button onClick={() => onPick(currentFolder)}>
                このフォルダを選ぶ
              </Button>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
