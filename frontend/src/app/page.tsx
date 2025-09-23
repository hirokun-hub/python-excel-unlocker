'use client';

import { useState } from 'react';
import { useSession, signIn, signOut } from 'next-auth/react';
import { Toaster, toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Progress } from '@/components/ui/progress';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { AlertDialog, AlertDialogAction, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from '@/components/ui/alert-dialog';
import FileUpload from '../components/FileUpload';
import { FileResults } from '@/components/FileResults'; // Import FileResults
import CSPTest from '@/components/CSPTest'; // CSPテストコンポーネント
import { File as FileIcon, X, AlertCircle } from 'lucide-react';
import { getUploadUrl, unlockFiles, uploadFileToS3, type UnlockFilePayload } from '@/lib/api';
import type { ProcessResult } from '@/types/process-result';

const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK_API === 'true';

// --- Type Definitions ---
type UploadProgress = { [key: string]: { progress: number; }; };

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
  const { status } = useSession();
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [pass1, setPass1] = useState('');
  const [pass2, setPass2] = useState('');
  const [processingStatus, setProcessingStatus] = useState<'idle' | 'uploading' | 'processing' | 'done'>('idle');
  const [uploadProgress, setUploadProgress] = useState<UploadProgress>({});
  const [jobProgress, setJobProgress] = useState({ done: 0, total: 0 });
  const [results, setResults] = useState<ProcessResult[]>([]);
  const [error, setError] = useState<string | null>(null);

  const totalUploadProgress = selectedFiles.length > 0 ? Math.round(Object.values(uploadProgress).reduce((acc, curr) => acc + curr.progress, 0) / selectedFiles.length) : 0;
  const jobPercentage = jobProgress.total > 0 ? Math.round((jobProgress.done / jobProgress.total) * 100) : 0;

  const handleFilesAdded = (files: File[]) => setSelectedFiles(prev => [...prev, ...files]);

  const handleProcessClick = async () => {
    if (selectedFiles.length === 0) { setError('ファイルが選択されていません。'); return; }
    if (!pass1 && !pass2) { setError('少なくとも1つのパスワードを入力してください。'); return; }
    if (status !== 'authenticated') { setError('Googleアカウントでサインインしてから操作してください。'); return; }

    setError(null);
    const passwords = [pass1, pass2].filter(Boolean);
    setProcessingStatus('uploading');
    toast.info('アップロード処理を開始します...');

    try {
      if (USE_MOCK) {
        const uploadPromises = selectedFiles.map(async (file) => {
          for (let p = 0; p <= 100; p += 20) {
            await sleep(120);
            setUploadProgress(prev => ({ ...prev, [file.name]: { progress: p } }));
          }
        });
        await Promise.all(uploadPromises);
        toast.success('（デモ）全ファイルのアップロードが完了しました。');
        setProcessingStatus('processing');
        setJobProgress({ done: 0, total: selectedFiles.length });
        const mockResults: ProcessResult[] = [];
        for (const f of selectedFiles) {
          await sleep(250);
          const buf = await f.arrayBuffer();
          const blob = new Blob([buf], { type: f.type || 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
          const url = URL.createObjectURL(blob);
          mockResults.push({ fileName: f.name.replace(/\.xlsx?$/i, '_unlocked.xlsx'), status: 'success', downloadUrl: url });
          setJobProgress(prev => ({ done: prev.done + 1, total: prev.total }));
        }
        setResults(mockResults);
        setProcessingStatus('done');
        toast.success('（デモ）処理が完了しました。');
        return;
      }

      const uploadedFiles: UnlockFilePayload[] = [];
      for (const file of selectedFiles) {
        setUploadProgress(prev => ({ ...prev, [file.name]: { progress: 0 } }));
        const uploadInfo = await getUploadUrl(
          file.name,
          file.size,
          file.type || 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        );
        setUploadProgress(prev => ({ ...prev, [file.name]: { progress: 10 } }));
        await uploadFileToS3(uploadInfo.uploadUrl, file, uploadInfo.uploadFields);
        setUploadProgress(prev => ({ ...prev, [file.name]: { progress: 100 } }));
        uploadedFiles.push({
          s3_key: uploadInfo.fileKey,
          original_name: file.name,
        });
      }

      toast.success('全ファイルのアップロードが完了しました。');

      setProcessingStatus('processing');
      const totalFiles = uploadedFiles.length;
      setJobProgress({ done: 0, total: totalFiles });

      const unlockResults: ProcessResult[] = [];
      for (const fileInfo of uploadedFiles) {
        const response = await unlockFiles([fileInfo], passwords);
        const fileResult = response.results?.[0];
        if (!fileResult) {
          throw new Error(`${fileInfo.original_name}の処理結果を取得できませんでした。`);
        }
        unlockResults.push(fileResult);
        setJobProgress(prev => ({ done: prev.done + 1, total: totalFiles }));
      }

      setResults(unlockResults);
      setProcessingStatus('done');
      toast.success('ファイルの処理が完了しました。');
    } catch (err: unknown) {
      console.error(err);
      let errorMessage = '処理中に不明なエラーが発生しました。';
      if (err instanceof Error) {
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
                  <FileResults results={results} />
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
        
        {/* CSPテストコンポーネント（開発環境のみ） */}
        <CSPTest />
      </main>
    </>
  );
}
