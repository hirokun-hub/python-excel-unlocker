import React, { useState } from 'react';
import { Alert, AlertDescription } from './ui/alert';
import { batchFileSecurityCheck, formatSecurityCheckResult } from '../lib/fileSecurity';

type BatchSecurityCheckResult = ReturnType<typeof batchFileSecurityCheck>;

// ファイルアップロードコンポーネントのPropsの型定義
interface FileUploadProps {
  onFilesAdded: (files: File[]) => void; // ファイルが追加されたときに呼び出されるコールバック関数
  onSecurityCheckFailed?: (results: BatchSecurityCheckResult) => void; // セキュリティチェック失敗時のコールバック
}

/**
 * ファイル選択ボタンとドラッグ＆ドロップエリアを提供するコンポーネント
 * セキュリティチェック機能を統合
 * @param {FileUploadProps} props - コンポーネントのプロパティ
 */
const FileUpload: React.FC<FileUploadProps> = ({ onFilesAdded, onSecurityCheckFailed }) => {
  const [securityAlerts, setSecurityAlerts] = useState<Array<{
    file: string;
    message: string;
    level: 'critical' | 'high' | 'medium' | 'low';
    icon: string;
    color: string;
  }>>([]);
  // ドラッグオーバーイベントのハンドラ
  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault(); // デフォルトの動作（ファイルを開くなど）を防ぐ
    e.stopPropagation();
  };

  // ファイルのセキュリティチェックと処理
  const processFiles = (files: File[]) => {
    // セキュリティアラートをクリア
    setSecurityAlerts([]);
    
    // 一括セキュリティチェックを実行
    const securityCheck = batchFileSecurityCheck(files);
    
    // セキュリティチェック結果の処理
    const alerts: typeof securityAlerts = [];
    const safeFiles: File[] = [];
    
    securityCheck.results.forEach(({ file, check }) => {
      if (check.safe) {
        safeFiles.push(file);
      } else {
        // 失敗したチェックの詳細を収集
        check.failedChecks.forEach(({ result }) => {
          const formatted = formatSecurityCheckResult(result);
          alerts.push({
            file: file.name,
            message: result.reason,
            level: result.riskLevel,
            icon: formatted.icon,
            color: formatted.color
          });
        });
      }
    });
    
    // セキュリティアラートを設定
    if (alerts.length > 0) {
      setSecurityAlerts(alerts);
      
      // セキュリティチェック失敗のコールバックを呼び出し
      if (onSecurityCheckFailed) {
        onSecurityCheckFailed(securityCheck);
      }
    }
    
    // 安全なファイルのみを親コンポーネントに渡す
    if (safeFiles.length > 0) {
      onFilesAdded(safeFiles);
    }
    
    // 結果のログ出力（開発用）
    console.log('セキュリティチェック結果:', {
      total: files.length,
      safe: safeFiles.length,
      unsafe: files.length - safeFiles.length,
      alerts: alerts.length
    });
  };

  // ドロップイベントのハンドラ
  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault(); // デフォルトの動作を防ぐ
    e.stopPropagation();

    const files = Array.from(e.dataTransfer.files); // ドロップされたファイルを取得
    if (files && files.length > 0) {
      processFiles(files); // セキュリティチェック付きでファイルを処理
    }
  };

  // ファイル選択ダイアログからのファイル選択イベントのハンドラ
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []); // 選択されたファイルを取得
    if (files && files.length > 0) {
      processFiles(files); // セキュリティチェック付きでファイルを処理
    }
    
    // ファイル入力をリセット（同じファイルを再選択可能にする）
    e.target.value = '';
  };

  return (
    <div className="w-full space-y-4">
      {/* セキュリティアラートの表示 */}
      {securityAlerts.length > 0 && (
        <div className="space-y-2">
          {securityAlerts.map((alert, index) => (
            <Alert key={index} className={`border-l-4 ${
              alert.level === 'critical' ? 'border-red-500 bg-red-50' :
              alert.level === 'high' ? 'border-orange-500 bg-orange-50' :
              alert.level === 'medium' ? 'border-yellow-500 bg-yellow-50' :
              'border-blue-500 bg-blue-50'
            }`}>
              <AlertDescription className="flex items-start space-x-2">
                <span className="text-lg">{alert.icon}</span>
                <div className="flex-1">
                  <div className="font-medium text-sm">
                    {alert.file}
                  </div>
                  <div className={`text-sm ${alert.color}`}>
                    {alert.message}
                  </div>
                </div>
              </AlertDescription>
            </Alert>
          ))}
        </div>
      )}
      
      {/* ファイルアップロードエリア */}
      <div
        className="w-full box-border p-8 border-2 border-dashed border-gray-300 rounded-lg text-center cursor-pointer hover:border-blue-500 transition-colors"
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        onClick={() => document.getElementById('fileInput')?.click()} // divクリックでファイル入力をトリガー
      >
        <input
          type="file"
          id="fileInput"
          multiple // 複数ファイルの選択を許可
          className="hidden" // input要素は非表示にする
          onChange={handleFileChange}
          accept=".xlsx, .xls" // Excelファイルのみを許可
        />
        <div className="space-y-2">
          <p className="text-gray-500">
            ここにファイルをドラッグ＆ドロップするか、クリックしてファイルを選択してください
          </p>
          <p className="text-sm text-gray-400">
            (対応ファイル: .xlsx, .xls)
          </p>
          <div className="text-xs text-gray-400 mt-4 space-y-1">
            <p>🔒 セキュリティチェック機能:</p>
            <p>• マクロ付きファイル（.xlsm）の自動検出・拒否</p>
            <p>• ファイルサイズ制限（最大20MB）</p>
            <p>• 危険なファイル形式の検出</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FileUpload;
