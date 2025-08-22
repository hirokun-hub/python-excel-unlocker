'use client';

import { useState } from 'react';
import { useSession, signIn, signOut } from 'next-auth/react';
import axios, { AxiosResponse } from 'axios';
import { Toaster, toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Progress } from '@/components/ui/progress';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { AlertDialog, AlertDialogAction, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from '@/components/ui/alert-dialog';
import FileUpload from '../components/FileUpload';
import { File as FileIcon, X, Download, AlertCircle, Loader2 } from 'lucide-react';

// --- API Client Logic (moved from lib/api.ts) ---

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
});
const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK_API === 'true';

// --- Type Definitions ---

type FileInfo = { filename: string; size: number; contentType: string; };
type PresignedUrlResponseItem = { filename: string; s3_key: string; upload_url: string; };
type UnlockFile = { s3_key: string; original_name: string; };
type UnlockSyncResponse = { results: ProcessResult[]; };
type UnlockAsyncResponse = { job_id: string; };
type JobStatusResponse = { job_id: string; state: string; progress: { done: number; total: number; }; results: ProcessResult[]; };
type ProcessResult = { fileName: string; status: 'success' | 'error'; message?: string; downloadUrl?: string; };
type UploadProgress = { [key: string]: { progress: number; }; };

// --- API Functions ---

const getPresignedUrls = async (files: FileInfo[]): Promise<{ items: PresignedUrlResponseItem[] }> => {
  if (USE_MOCK) {
    // 署名URLを擬似返却（アップロード処理は別でモック）
    return { items: files.map(f => ({ filename: f.filename, s3_key: `mock/${f.filename}`, upload_url: 'mock://put' })) };
  }
  const response = await api.post('/presigned-urls', { files });
  return response.data;
};

const unlock = async (files: UnlockFile[], passwords: string[]): Promise<AxiosResponse<UnlockSyncResponse | UnlockAsyncResponse>> => {
  if (USE_MOCK) {
    // 同期完了の 200 を返し、results を組み立てるモック
    const results: ProcessResult[] = files.map(f => ({
      fileName: f.original_name.replace(/\.xlsx?$/i, '_unlocked.xlsx'),
      status: 'success',
    }));
    return { status: 200, data: { results } } as unknown as AxiosResponse<UnlockSyncResponse>;
  }
  return api.post('/unlock', { files, passwords });
};

const getProcessingStatus = async (jobId: string): Promise<JobStatusResponse> => {
  if (USE_MOCK) {
    // すぐ完了状態を返す
    return { job_id: jobId, state: 'completed', progress: { done: 1, total: 1 }, results: [] };
  }
  const response = await api.get(`/status?job_id=${jobId}`);
  return response.data;
};

// --- Page Components ---

const Header = () => {
  const { data: session } = useSession();
  return (
    <header className="flex justify-between items-center">
      <div className="flex-grow"><CardTitle>Excel パスワード解除</CardTitle><CardDescription>パスワード付きExcelファイルを一括で解除します</CardDescription></div>
      {session && (
        <div className="flex items-center gap-4"><p className="text-sm text-muted-foreground">{session.user?.name || session.user?.email}</p><Button variant="outline" onClick={() => signOut()}>サインアウト</Button></div>
      )}
    </header>
  );
};

const LoginOverlay = () => (
  <div className="absolute inset-0 bg-background/80 backdrop-blur-sm flex flex-col justify-center items-center z-10 rounded-lg">
    <div className="text-center p-6"><h2 className="text-2xl font-bold text-foreground mb-4">ようこそ</h2><p className="text-muted-foreground mb-8">アプリケーションの利用には、Googleアカウントでのサインインが必要です。</p><Button size="lg" onClick={() => signIn('google')}>Googleでサインイン</Button></div>
  </div>
);

const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

// --- Main Home Component ---

export default function Home() {
  const { data: session, status } = useSession();
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [pass1, setPass1] = useState('');
  const [pass2, setPass2] = useState('');
  const [processingStatus, setProcessingStatus] = useState<'idle' | 'uploading' | 'processing' | 'done'>('idle');
  const [uploadProgress, setUploadProgress] = useState<UploadProgress>({});
  const [jobProgress, setJobProgress] = useState({ done: 0, total: 0 });
  const [results, setResults] = useState<ProcessResult[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [savingToDrive, setSavingToDrive] = useState<string[]>([]);

  const totalUploadProgress = selectedFiles.length > 0 ? Math.round(Object.values(uploadProgress).reduce((acc, curr) => acc + curr.progress, 0) / selectedFiles.length) : 0;
  const jobPercentage = jobProgress.total > 0 ? Math.round((jobProgress.done / jobProgress.total) * 100) : 0;

  const handleFilesAdded = (files: File[]) => setSelectedFiles(prev => [...prev, ...files]);

  const handleProcessClick = async () => {
    if (selectedFiles.length === 0) { setError("ファイルが選択されていません。"); return; }
    if (!pass1 && !pass2) { setError("少なくとも1つのパスワードを入力してください。"); return; }
    setError(null);
    setProcessingStatus('uploading');
    toast.info("アップロード処理を開始します...");

    try {
      // --------------------
      // モック経路
      // --------------------
      if (USE_MOCK) {
        // 1) 疑似アップロード（進捗バー反映）
        const uploadPromises = selectedFiles.map(async (file) => {
          for (let p = 0; p <= 100; p += 20) {
            await sleep(120);
            setUploadProgress(prev => ({ ...prev, [file.name]: { progress: p } }));
          }
        });
        await Promise.all(uploadPromises);
        toast.success("（デモ）全ファイルのアップロードが完了しました。");

        // 2) 疑似アンロック
        setProcessingStatus('processing');
        const passwords = [pass1, pass2].filter(Boolean);
        if (passwords.length === 0) { throw new Error("少なくとも1つのパスワードを入力してください。"); }

        // 疑似処理のプログレス
        setJobProgress({ done: 0, total: selectedFiles.length });
        const results: ProcessResult[] = [];
        for (const f of selectedFiles) {
          await sleep(250);
          // 元ファイルのバイト列で Blob を作りダウンロード可能に
          const buf = await f.arrayBuffer();
          const blob = new Blob([buf], { type: f.type || 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
          const url = URL.createObjectURL(blob);
          results.push({ fileName: f.name.replace(/\.xlsx?$/i, '_unlocked.xlsx'), status: 'success', downloadUrl: url });
          setJobProgress(prev => ({ done: prev.done + 1, total: prev.total }));
        }
        setResults(results);
        setProcessingStatus('done');
        toast.success("（デモ）処理が完了しました。");
        return; // モック経路で完結
      }
      // 1. Get presigned URLs
      const fileInfos = selectedFiles.map(f => ({ filename: f.name, size: f.size, contentType: f.type }));
      const { items: presignedItems } = await getPresignedUrls(fileInfos);

      // 2. Upload files to S3
      const uploadPromises = selectedFiles.map(file => {
        const presignedData = presignedItems.find(p => p.filename === file.name);
        if (!presignedData) throw new Error(`${file.name}の署名付きURLが取得できませんでした。`);
        return axios.put(presignedData.upload_url, file, {
          headers: { 'Content-Type': file.type },
          onUploadProgress: (e) => setUploadProgress(prev => ({ ...prev, [file.name]: { progress: e.total ? Math.round((e.loaded * 100) / e.total) : 0 } })),
        });
      });
      await Promise.all(uploadPromises);
      toast.success("全ファイルのアップロードが完了しました。");

      // 3. Call unlock endpoint
      setProcessingStatus('processing');
      const unlockFiles = selectedFiles.map(f => ({ s3_key: presignedItems.find(p => p.filename === f.name)!.s3_key, original_name: f.name }));
      const passwords = [pass1, pass2].filter(Boolean);
      const unlockResponse = await unlock(unlockFiles, passwords);

      // 4. Handle sync or async response
      if (unlockResponse.status === 200) { // Sync
        const data = unlockResponse.data as UnlockSyncResponse;
        setResults(data.results);
        setProcessingStatus('done');
        toast.success("ファイルの処理が完了しました。");
      } else if (unlockResponse.status === 202) { // Async
        const data = unlockResponse.data as UnlockAsyncResponse;
        let jobStatus: JobStatusResponse | null = null;
        toast.info(`処理を開始しました (Job ID: ${data.job_id})。完了までお待ちください...`);
        while (!jobStatus || ['queued', 'running'].includes(jobStatus.state)) {
          await sleep(2000);
          jobStatus = await getProcessingStatus(data.job_id);
          setJobProgress(jobStatus.progress);
        }
        setResults(jobStatus.results);
        setProcessingStatus('done');
        toast.success("ファイルの処理が完了しました。");
      } else {
        throw new Error(`予期しないレスポンスコード: ${unlockResponse.status}`);
      }
    } catch (err: unknown) {
      console.error(err);
      let errorMessage = '処理中に不明なエラーが発生しました。';
      if (axios.isAxiosError(err) && err.response) {
        errorMessage = err.response.data?.error || err.message;
      } else if (err instanceof Error) {
        errorMessage = err.message;
      }
      setError(errorMessage);
      toast.error(errorMessage);
      setProcessingStatus('idle');
    }
  };

  const handleClearClick = () => {
    setSelectedFiles([]);
    setResults([]);
    setProcessingStatus('idle');
    setError(null);
    setPass1('');
    setPass2('');
    setUploadProgress({});
    setJobProgress({ done: 0, total: 0 });
  };

  const removeFile = (index: number) => {
    const fileToRemove = selectedFiles[index];
    setSelectedFiles(files => files.filter((_, i) => i !== index));
    const newProgress = { ...uploadProgress };
    delete newProgress[fileToRemove.name];
    setUploadProgress(newProgress);
  };

  const handleSaveToDrive = async (fileName: string, downloadUrl: string) => {
    if (!session?.accessToken) { toast.error('Google Driveに保存するには、再度サインインしてください。'); return; }
    setSavingToDrive(prev => [...prev, fileName]);
    const toastId = toast.loading(`${fileName} をGoogle Driveに保存しています...`);
    try {
      const fileResponse = await fetch(downloadUrl);
      if (!fileResponse.ok) throw new Error('ファイルのダウンロードに失敗しました。');
      const fileBlob = await fileResponse.blob();
      // Use access token from NextAuth session and upload via our util
      const at = (session as any).accessToken as string | undefined
      if (!at) throw new Error('accessToken がセッションに含まれていません。再ログインしてください。')
      const res = await fetch('/api/debug/tokeninfo'); // optional: verify token
      // Call helper to upload directly to Drive
      const { uploadToDriveUsingAccessToken } = await import('@/lib/googleDrive')
      await uploadToDriveUsingAccessToken(fileBlob, fileName, at)
      toast.success(`${fileName} をGoogle Driveに正常に保存しました。`, { id: toastId });
    } catch (err: unknown) {
      console.error(err);
      let errorMessage = 'Google Driveへの保存中に不明なエラーが発生しました。';
      if (err instanceof Error) {
        errorMessage = err.message;
      }
      toast.error(errorMessage, { id: toastId });
    } finally {
      setSavingToDrive(prev => prev.filter(f => f !== fileName));
    }
  };

  const isAuthenticated = status === 'authenticated';
  const progressValue = processingStatus === 'uploading' ? totalUploadProgress : jobPercentage;
  const progressText = processingStatus === 'uploading' ? `ファイルをアップロード中... (${totalUploadProgress}%)` : `サーバーでファイルを処理中... (${jobPercentage}%)`;

  return (
    <>
      <Toaster position="top-center" richColors />
      <main className="flex min-h-screen flex-col items-center justify-center p-4 md:p-12 bg-muted/40">
        <Card className="w-full max-w-4xl relative">
          {!isAuthenticated && status !== 'loading' && <LoginOverlay />}
          <div className={!isAuthenticated ? 'blur-sm' : ''}>
            <CardHeader><Header /></CardHeader>
            <CardContent>
              {processingStatus === 'idle' && (
                <div className="space-y-6">
                  <FileUpload onFilesAdded={handleFilesAdded} />
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4"><Input type="password" placeholder="パスワード候補1" value={pass1} onChange={e => setPass1(e.target.value)} /><Input type="password" placeholder="パスワード候補2（任意）" value={pass2} onChange={e => setPass2(e.target.value)} /></div>
                  {selectedFiles.length > 0 && (
                     <div className="space-y-2">
                       <h3 className="font-semibold">選択中のファイル ({selectedFiles.length}件)</h3>
                       <div className="max-h-60 overflow-y-auto space-y-2 p-2 bg-muted rounded-md">
                        {selectedFiles.map((file, index) => (
                          <div key={index} className="flex items-center justify-between p-2 bg-background rounded-md text-sm">
                            <div className="flex items-center gap-2"><FileIcon className="w-4 h-4 text-muted-foreground" /><span className="font-mono">{file.name}</span></div>
                            <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => removeFile(index)}><X className="w-4 h-4" /></Button>
                          </div>
                        ))}
                       </div>
                     </div>
                  )}
                </div>
              )}
              {(processingStatus === 'uploading' || processingStatus === 'processing') && (
                <div className="text-center p-12 space-y-4"><p className="text-lg text-muted-foreground">{progressText}</p><Progress value={progressValue} className="w-full" /></div>
              )}
              {processingStatus === 'done' && (
                <div className="space-y-4">
                  <h2 className="text-2xl font-semibold text-center">処理結果</h2>
                  <div className="space-y-3">
                    {results.map((result, index) => (
                      <div key={index} className={`flex justify-between items-center p-3 rounded-lg ${result.status === 'success' ? 'bg-green-100 dark:bg-green-900/20' : 'bg-red-100 dark:bg-red-900/20'}`}>
                        <span className={`font-medium ${result.status === 'success' ? 'text-green-800 dark:text-green-300' : 'text-red-800 dark:text-red-300'}`}>{result.fileName}</span>
                        {result.status === 'success' ? (
                          <div className="flex gap-2">
                            <Button variant="outline" size="sm" onClick={() => handleSaveToDrive(result.fileName, result.downloadUrl!)} disabled={savingToDrive.includes(result.fileName)}>
                              {savingToDrive.includes(result.fileName) ? (<><Loader2 className="mr-2 h-4 w-4 animate-spin" />保存中</>) : ('Google Driveに保存')}
                            </Button>
                            <Button asChild size="sm"><a href={result.downloadUrl} download><Download className="w-4 h-4 mr-2" />ダウンロード</a></Button>
                          </div>
                        ) : (<p className="text-sm text-red-700 dark:text-red-400">{result.message}</p>)}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
            <CardFooter className="flex justify-center gap-4 pt-6">
              {processingStatus === 'idle' && (<><Button size="lg" onClick={handleProcessClick} disabled={selectedFiles.length === 0}>解除開始</Button><Button size="lg" variant="outline" onClick={handleClearClick}>クリア</Button></>)}
              {(processingStatus === 'done') && (<Button size="lg" onClick={handleClearClick}>もう一度試す</Button>)}
            </CardFooter>
          </div>
        </Card>
        <AlertDialog open={!!error} onOpenChange={() => setError(null)}>
          <AlertDialogContent>
            <AlertDialogHeader><AlertDialogTitle className="flex items-center gap-2"><AlertCircle className="text-destructive"/>入力エラー</AlertDialogTitle><AlertDialogDescription>{error}</AlertDialogDescription></AlertDialogHeader>
            <AlertDialogFooter><AlertDialogAction onClick={() => setError(null)}>OK</AlertDialogAction></AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </main>
    </>
  );
}
