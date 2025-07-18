'use client';

import { useState } from 'react';
import axios from 'axios'; // axiosをインポート
import FileUpload from '../components/FileUpload';

// 処理結果の型定義
type ProcessResult = {
  fileName: string;
  status: 'success' | 'error';
  message?: string;
  downloadUrl?: string;
};

/**
 * アプリケーションのメインページコンポーネント
 */
export default function Home() {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [processingStatus, setProcessingStatus] = useState<'idle' | 'processing' | 'done'>('idle');
  const [results, setResults] = useState<ProcessResult[]>([]);
  const [error, setError] = useState<string | null>(null); // APIエラー用のstate

  /**
   * ファイルが追加されたときのハンドラ
   */
  const handleFilesAdded = (files: File[]) => {
    setSelectedFiles(prevFiles => [...prevFiles, ...files]);
    setProcessingStatus('idle');
    setResults([]);
    setError(null);
  };

  /**
   * 「解除開始」ボタンクリック時のハンドラ
   */
  const handleProcessClick = async () => {
    setProcessingStatus('processing');
    setResults([]);
    setError(null);

    const formData = new FormData();
    selectedFiles.forEach(file => {
      formData.append('files', file);
    });

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL;
      if (!apiUrl) {
        throw new Error('APIのURLが設定されていません。');
      }

      const response = await axios.post<ProcessResult[]>(apiUrl, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setResults(response.data);
    } catch (err: any) {
      console.error('API Error:', err);
      setError('ファイルの処理中にエラーが発生しました。バックエンドが起動しているか確認してください。');
      // エラー発生時は、全ファイルが失敗したかのような結果を表示
      setResults(selectedFiles.map(f => ({ fileName: f.name, status: 'error', message: 'サーバーエラー' })));
    } finally {
      setProcessingStatus('done');
    }
  };

  /**
   * 「クリア」ボタンクリック時のハンドラ
   */
  const handleClearClick = () => {
    setSelectedFiles([]);
    setResults([]);
    setProcessingStatus('idle');
    setError(null);
  };

  return (
    <main className="flex min-h-screen flex-col items-center p-6 md:p-12 bg-gray-50">
      <div className="w-full max-w-4xl bg-white p-6 md:p-8 rounded-lg shadow-md">
        <header className="text-center mb-10">
          <h1 className="text-3xl md:text-4xl font-bold text-gray-800">Excel パスワード解除ツール</h1>
          <p className="text-gray-500 mt-2">パスワードが設定されたExcelファイルを選択してください</p>
        </header>

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-6" role="alert">
            <strong className="font-bold">エラー: </strong>
            <span className="block sm:inline">{error}</span>
          </div>
        )}

        {processingStatus !== 'done' && <FileUpload onFilesAdded={handleFilesAdded} />}

        {selectedFiles.length > 0 && processingStatus === 'idle' && (
          <div className="mt-8 w-full">
            <h2 className="text-xl font-semibold mb-4 text-gray-700">選択されたファイル ({selectedFiles.length}件)</h2>
            <ul className="space-y-2 bg-gray-50 p-4 rounded-lg max-h-60 overflow-y-auto">
              {selectedFiles.map((file, index) => (
                <li key={index} className="text-gray-800 p-1 flex justify-between items-center">
                  <span>{file.name}</span>
                  <span className="text-gray-500 text-sm">({(file.size / 1024).toFixed(2)} KB)</span>
                </li>
              ))}
            </ul>
            <div className="mt-6 flex justify-center gap-4">
              <button
                onClick={handleProcessClick}
                className="px-8 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors"
              >
                解除開始
              </button>
              <button
                onClick={handleClearClick}
                className="px-8 py-3 bg-gray-200 text-gray-800 font-semibold rounded-lg hover:bg-gray-300 transition-colors"
              >
                クリア
              </button>
            </div>
          </div>
        )}

        {processingStatus === 'processing' && (
          <div className="text-center p-12">
            <p className="text-lg text-gray-600">処理中です、しばらくお待ちください...</p>
          </div>
        )}

        {processingStatus === 'done' && (
          <div className="mt-8 w-full">
            <h2 className="text-2xl font-semibold mb-4 text-gray-700 text-center">処理結果</h2>
            <div className="space-y-3">
              {results.map((result, index) => (
                <div key={index} className={`p-4 rounded-lg flex justify-between items-center ${result.status === 'success' ? 'bg-green-100' : 'bg-red-100'}`}>
                  <span className={`${result.status === 'success' ? 'text-green-800' : 'text-red-800'}`}>{result.fileName}</span>
                  {result.status === 'success' ? (
                    <a href={result.downloadUrl} download className="px-4 py-2 bg-green-600 text-white text-sm rounded hover:bg-green-700">ダウンロード</a>
                  ) : (
                    <p className="text-red-700 text-sm">{result.message}</p>
                  )}
                </div>
              ))}
            </div>
            <div className="mt-8 text-center">
              <button
                onClick={handleClearClick}
                className="px-8 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors"
              >
                もう一度試す
              </button>
            </div>
          </div>
        )}

      </div>
    </main>
  );
}
