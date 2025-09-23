"use client";
import { useEffect, useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { toast } from "sonner";

const debounce = <Args extends unknown[]>(func: (...args: Args) => void, wait: number): ((...args: Args) => void) => {
  let timeout: ReturnType<typeof setTimeout>;
  return (...args: Args) => {
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

const formatModified = (dtIso: string) => `更新日: ${jstFormatter.format(new Date(dtIso))}`;

interface DriveFolder {
  id: string;
  name: string;
  modifiedTime?: string;
  displayPath?: string;
}

type Breadcrumb = {
  id: string;
  name: string;
};

interface DriveFolderListResponse {
  files?: DriveFolder[];
  nextPageToken?: string;
}

interface DriveFolderPickerProps {
  open: boolean;
  onClose: () => void;
  onPick: (folder: { id: string; name: string }) => void;
  initialFolderId?: string;
}

const ROOT_CRUMB: Breadcrumb = { id: "root", name: "マイドライブ" };

function parseBreadcrumbs(value: unknown): Breadcrumb[] {
  if (!Array.isArray(value)) {
    return [ROOT_CRUMB];
  }

  const parsed = value.filter((item): item is Breadcrumb => {
    if (!item || typeof item !== "object") {
      return false;
    }
    const record = item as Record<string, unknown>;
    return typeof record.id === "string" && typeof record.name === "string";
  });

  return parsed.length > 0 ? parsed : [ROOT_CRUMB];
}

function parseDriveFoldersResponse(value: unknown): DriveFolderListResponse {
  if (!value || typeof value !== "object") {
    return {};
  }

  const record = value as Record<string, unknown>;
  const files = Array.isArray(record.files)
    ? record.files.reduce<DriveFolder[]>((acc, item) => {
        if (!item || typeof item !== "object") {
          return acc;
        }
        const fileRecord = item as Record<string, unknown>;
        const id = typeof fileRecord.id === "string" ? fileRecord.id : null;
        const name = typeof fileRecord.name === "string" ? fileRecord.name : null;

        if (!id || !name) {
          return acc;
        }

        acc.push({
          id,
          name,
          modifiedTime: typeof fileRecord.modifiedTime === "string" ? fileRecord.modifiedTime : undefined,
          displayPath: typeof fileRecord.displayPath === "string" ? fileRecord.displayPath : undefined,
        });

        return acc;
      }, [])
    : undefined;

  const nextPageToken = typeof record.nextPageToken === "string" ? record.nextPageToken : undefined;

  return {
    files,
    nextPageToken,
  };
}

export default function DriveFolderPicker({ open, onClose, onPick, initialFolderId }: DriveFolderPickerProps) {
  const [folderId, setFolderId] = useState<string>(initialFolderId || "root");
  const [items, setItems] = useState<DriveFolder[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");
  const [pageToken, setPageToken] = useState<string | null>(null);
  const [crumbs, setCrumbs] = useState<Breadcrumb[]>([ROOT_CRUMB]);

  const isSearching = !!debouncedQuery;
  const title = useMemo(
    () => (isSearching ? "検索結果" : crumbs.map((c) => c.name).join(" / ")),
    [crumbs, isSearching]
  );

  const debouncedSetQuery = useMemo(
    () =>
      debounce((q: string) => {
        setDebouncedQuery(q);
        setItems([]); // Reset items when search query changes
        setPageToken(null);
      }, 300),
    [setDebouncedQuery, setItems, setPageToken]
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
          const bcRes = await fetch(`/api/drive/breadcrumb?id=${encodeURIComponent(folderId)}`, { cache: "no-store" });
          if (!bcRes.ok) throw new Error("Failed to fetch breadcrumbs");
          const breadcrumbJson: unknown = await bcRes.json();
          setCrumbs(parseBreadcrumbs(breadcrumbJson));
        }

        const params = new URLSearchParams();
        if (isSearching) {
          params.set("q", debouncedQuery);
        } else {
          params.set("parentId", folderId);
        }

        const folderRes = await fetch(`/api/drive/folders?${params.toString()}`, { cache: "no-store" });
        if (folderRes.status === 401) {
          toast.error("Google へのログインが切れました。再ログインしてください。");
          return;
        }
        if (!folderRes.ok) throw new Error("Failed to fetch folders");

        const folderJson: unknown = await folderRes.json();
        const folderData = parseDriveFoldersResponse(folderJson);
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

  const handleFolderClick = (folder: { id: string; name: string }) => {
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

      const res = await fetch(`/api/drive/folders?${params.toString()}`, { cache: "no-store" });
      if (res.status === 401) {
        toast.error("Google へのログインが切れました。再ログインしてください。");
        return;
      }
      const dataJson: unknown = await res.json();
      const data = parseDriveFoldersResponse(dataJson);
      setItems((prev) => [...prev, ...(data.files ?? [])]);
      setPageToken(data.nextPageToken ?? null);
    } catch (error) {
      console.error(error);
      toast.error("フォルダの読み込みに失敗しました。");
    } finally {
      setLoading(false);
    }
  };

  const currentFolder = crumbs[crumbs.length - 1] ?? ROOT_CRUMB;

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
          <Button variant="secondary" onClick={() => setSearchQuery("")}>クリア</Button>
        </div>
        <div className="mt-3 max-h-80 min-h-[20rem] overflow-auto rounded border">
          {loading && items.length === 0 ? (
            <div className="p-6 text-center text-sm text-muted-foreground">読み込み中…</div>
          ) : (
            <ul className="divide-y">
              {!isSearching && folderId !== "root" && (
                <li
                  className="p-3 hover:bg-muted cursor-pointer"
                  onClick={() => handleFolderClick(crumbs[crumbs.length - 2] ?? ROOT_CRUMB)}
                >
                  ⬆️ 上の階層へ
                </li>
              )}
              {items.map((f) => (
                <li key={f.id} className="p-3 flex items-center justify-between hover:bg-muted">
                  <button className="text-left flex-1" onClick={() => handleFolderClick(f)}>
                    <div className="font-medium">{f.name}</div>
                    <div className="mt-1 text-xs text-muted-foreground space-y-0.5">
                      {f.modifiedTime && <div>{formatModified(f.modifiedTime)}</div>}
                      {f.displayPath && <div>パス: {f.displayPath}</div>}
                    </div>
                  </button>
                  {!isSearching && (
                    <Button size="sm" onClick={() => onPick({ id: f.id, name: f.name })}>
                      ここに保存
                    </Button>
                  )}
                </li>
              ))}
              {!loading && items.length === 0 && (
                <li className="p-6 text-center text-sm text-muted-foreground">フォルダが見つかりません</li>
              )}
            </ul>
          )}
        </div>
        <div className="flex items-center justify-between pt-2">
          <div className="text-xs text-muted-foreground truncate">
            {!isSearching && `現在のフォルダ: ${currentFolder.name}`}
          </div>
          <div className="flex gap-2">
            {pageToken && <Button variant="outline" onClick={loadMore} disabled={loading}>さらに読み込む</Button>}
            {!isSearching && <Button onClick={() => onPick(currentFolder)}>このフォルダを選ぶ</Button>}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
