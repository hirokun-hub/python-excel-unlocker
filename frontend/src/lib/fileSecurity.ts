/**
 * フロントエンド側のファイル安全性チェック機能
 * 
 * アップロード前の事前チェックを実装
 */

// セキュリティ設定
const MAX_FILE_SIZE = 20 * 1024 * 1024; // 20MB
const MIN_FILE_SIZE = 100; // 100バイト

// 許可されたファイル拡張子
const ALLOWED_EXTENSIONS = new Set(['.xlsx', '.xls']);

// 危険なファイル拡張子
const DANGEROUS_EXTENSIONS = new Set([
  '.xlsm',  // マクロ付きExcel
  '.xlsb',  // バイナリExcel（マクロ可能）
  '.xltm',  // マクロ付きテンプレート
  '.xla',   // Excel アドイン
  '.xlam',  // マクロ付きアドイン
  '.exe',   // 実行ファイル
  '.bat',   // バッチファイル
  '.cmd',   // コマンドファイル
  '.scr',   // スクリーンセーバー
  '.com',   // 実行ファイル
  '.pif',   // プログラム情報ファイル
  '.vbs',   // VBScript
  '.js',    // JavaScript
  '.jar',   // Java Archive
  '.zip',   // ZIP（偽装の可能性）
  '.rar',   // RAR（偽装の可能性）
]);

// 許可されたMIMEタイプ
const ALLOWED_MIME_TYPES = new Set([
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', // .xlsx
  'application/vnd.ms-excel', // .xls
  'application/octet-stream', // 一部のブラウザで送信される場合
]);

// セキュリティチェック結果の型定義
export interface SecurityCheckResult {
  safe: boolean;
  reason: string;
  riskLevel: 'low' | 'medium' | 'high' | 'critical';
  suggestion?: string;
  details?: Record<string, any>;
}

/**
 * ファイル拡張子のセキュリティチェック
 */
export function checkFileExtension(fileName: string): SecurityCheckResult {
  const extension = getFileExtension(fileName);
  
  // 危険な拡張子のチェック（最優先）
  if (DANGEROUS_EXTENSIONS.has(extension)) {
    if (extension === '.xlsm') {
      return {
        safe: false,
        reason: 'マクロ付きExcelファイル（.xlsm）は処理できません。セキュリティ上の理由により拒否されました。',
        riskLevel: 'high',
        suggestion: '.xlsx または .xls ファイルを選択してください',
        details: { detectedExtension: extension, threatType: 'macro_enabled' }
      };
    } else {
      return {
        safe: false,
        reason: `危険なファイル形式（${extension}）が検出されました。このファイル形式は処理できません。`,
        riskLevel: 'critical',
        suggestion: '.xlsx または .xls ファイルのみアップロード可能です',
        details: { detectedExtension: extension, threatType: 'dangerous_executable' }
      };
    }
  }
  
  // 許可された拡張子のチェック
  if (!ALLOWED_EXTENSIONS.has(extension)) {
    return {
      safe: false,
      reason: `サポートされていないファイル形式です（${extension}）。.xlsx または .xls ファイルのみ処理可能です。`,
      riskLevel: 'medium',
      suggestion: '.xlsx または .xls ファイルを選択してください',
      details: { detectedExtension: extension, allowedExtensions: Array.from(ALLOWED_EXTENSIONS) }
    };
  }
  
  return {
    safe: true,
    reason: 'ファイル拡張子チェック通過',
    riskLevel: 'low',
    details: { detectedExtension: extension }
  };
}

/**
 * ファイルサイズのセキュリティチェック
 */
export function checkFileSize(file: File): SecurityCheckResult {
  const fileSize = file.size;
  
  // 最大サイズチェック
  if (fileSize > MAX_FILE_SIZE) {
    return {
      safe: false,
      reason: `ファイルサイズ（${formatFileSize(fileSize)}）が上限（${formatFileSize(MAX_FILE_SIZE)}）を超えています。`,
      riskLevel: 'medium',
      suggestion: '20MB以下のファイルを選択してください',
      details: { fileSize, maxSize: MAX_FILE_SIZE }
    };
  }
  
  // 最小サイズチェック（空ファイル・破損ファイル対策）
  if (fileSize < MIN_FILE_SIZE) {
    return {
      safe: false,
      reason: `ファイルサイズ（${fileSize} bytes）が小さすぎます。破損している可能性があります。`,
      riskLevel: 'medium',
      suggestion: '有効なExcelファイルを選択してください',
      details: { fileSize, minSize: MIN_FILE_SIZE }
    };
  }
  
  return {
    safe: true,
    reason: 'ファイルサイズチェック通過',
    riskLevel: 'low',
    details: { fileSize }
  };
}

/**
 * MIMEタイプのセキュリティチェック
 */
export function checkMimeType(file: File): SecurityCheckResult {
  const mimeType = file.type;
  
  // MIMEタイプが設定されていない場合は警告レベル
  if (!mimeType) {
    return {
      safe: true,
      reason: 'MIMEタイプが設定されていませんが、拡張子チェックで検証します',
      riskLevel: 'low',
      details: { declaredMimeType: mimeType, warning: 'MIMEタイプ未設定' }
    };
  }
  
  // 許可されたMIMEタイプのチェック
  if (!ALLOWED_MIME_TYPES.has(mimeType)) {
    return {
      safe: false,
      reason: `許可されていないMIMEタイプです: ${mimeType}`,
      riskLevel: 'medium',
      suggestion: 'Excelファイル（.xlsx/.xls）を選択してください',
      details: { 
        declaredMimeType: mimeType, 
        allowedMimeTypes: Array.from(ALLOWED_MIME_TYPES) 
      }
    };
  }
  
  return {
    safe: true,
    reason: 'MIMEタイプチェック通過',
    riskLevel: 'low',
    details: { declaredMimeType: mimeType }
  };
}

/**
 * ファイル名の安全性チェック
 */
export function checkFileName(fileName: string): SecurityCheckResult {
  // 危険な文字のチェック
  const dangerousChars = /[<>:"|?*\x00-\x1f]/;
  if (dangerousChars.test(fileName)) {
    return {
      safe: false,
      reason: 'ファイル名に危険な文字が含まれています',
      riskLevel: 'medium',
      suggestion: '英数字、ハイフン、アンダースコアのみを使用してください',
      details: { fileName, issue: 'dangerous_characters' }
    };
  }
  
  // 長すぎるファイル名のチェック
  if (fileName.length > 255) {
    return {
      safe: false,
      reason: 'ファイル名が長すぎます',
      riskLevel: 'low',
      suggestion: '255文字以下のファイル名を使用してください',
      details: { fileName: fileName.substring(0, 50) + '...', length: fileName.length }
    };
  }
  
  // 予約語のチェック（Windows）
  const reservedNames = /^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(\.|$)/i;
  if (reservedNames.test(fileName)) {
    return {
      safe: false,
      reason: 'Windowsの予約語がファイル名に含まれています',
      riskLevel: 'medium',
      suggestion: '別のファイル名を使用してください',
      details: { fileName, issue: 'reserved_name' }
    };
  }
  
  return {
    safe: true,
    reason: 'ファイル名チェック通過',
    riskLevel: 'low',
    details: { fileName }
  };
}

/**
 * 包括的なファイル安全性チェック
 */
export function comprehensiveFileSecurityCheck(file: File): {
  safe: boolean;
  riskLevel: 'low' | 'medium' | 'high' | 'critical';
  failedChecks: Array<{ check: string; result: SecurityCheckResult }>;
  summary: string;
  details: Record<string, SecurityCheckResult>;
} {
  const checks = {
    extension: checkFileExtension(file.name),
    size: checkFileSize(file),
    mimeType: checkMimeType(file),
    fileName: checkFileName(file.name),
  };
  
  // 失敗したチェックの収集
  const failedChecks = Object.entries(checks)
    .filter(([_, result]) => !result.safe)
    .map(([check, result]) => ({ check, result }));
  
  // 全体的な安全性評価
  const overallSafe = failedChecks.length === 0;
  
  // 最高リスクレベルの決定
  const riskLevels = ['low', 'medium', 'high', 'critical'];
  const highestRisk = Object.values(checks).reduce((highest, check) => {
    const currentIndex = riskLevels.indexOf(check.riskLevel);
    const highestIndex = riskLevels.indexOf(highest);
    return currentIndex > highestIndex ? check.riskLevel : highest;
  }, 'low' as 'low' | 'medium' | 'high' | 'critical');
  
  // サマリーメッセージの生成
  let summary: string;
  if (overallSafe) {
    summary = 'ファイルは全てのセキュリティチェックに合格しました。';
  } else if (highestRisk === 'critical') {
    summary = 'クリティカルなセキュリティリスクが検出されました。このファイルは処理できません。';
  } else if (highestRisk === 'high') {
    summary = '高リスクのセキュリティ問題が検出されました。';
  } else if (highestRisk === 'medium') {
    summary = 'セキュリティ上の問題が検出されました。ファイルを確認してください。';
  } else {
    summary = '軽微なセキュリティ問題が検出されました。';
  }
  
  return {
    safe: overallSafe,
    riskLevel: highestRisk,
    failedChecks,
    summary,
    details: checks
  };
}

/**
 * 複数ファイルの一括セキュリティチェック
 */
export function batchFileSecurityCheck(files: File[]): {
  overallSafe: boolean;
  results: Array<{ file: File; check: ReturnType<typeof comprehensiveFileSecurityCheck> }>;
  summary: { safe: number; unsafe: number; critical: number };
} {
  const results = files.map(file => ({
    file,
    check: comprehensiveFileSecurityCheck(file)
  }));
  
  const summary = results.reduce(
    (acc, { check }) => {
      if (check.safe) {
        acc.safe++;
      } else {
        acc.unsafe++;
        if (check.riskLevel === 'critical') {
          acc.critical++;
        }
      }
      return acc;
    },
    { safe: 0, unsafe: 0, critical: 0 }
  );
  
  const overallSafe = summary.unsafe === 0;
  
  return {
    overallSafe,
    results,
    summary
  };
}

/**
 * ユーティリティ関数
 */

function getFileExtension(fileName: string): string {
  const lastDotIndex = fileName.lastIndexOf('.');
  return lastDotIndex === -1 ? '' : fileName.substring(lastDotIndex).toLowerCase();
}

function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * セキュリティチェック結果の表示用フォーマット
 */
export function formatSecurityCheckResult(result: SecurityCheckResult): {
  icon: string;
  color: string;
  title: string;
  message: string;
} {
  const formats = {
    critical: {
      icon: '🚨',
      color: 'text-red-600',
      title: 'クリティカル',
      message: result.reason
    },
    high: {
      icon: '⚠️',
      color: 'text-orange-600',
      title: '高リスク',
      message: result.reason
    },
    medium: {
      icon: '⚠️',
      color: 'text-yellow-600',
      title: '注意',
      message: result.reason
    },
    low: {
      icon: '✅',
      color: 'text-green-600',
      title: '安全',
      message: result.reason
    }
  };
  
  return formats[result.riskLevel];
}