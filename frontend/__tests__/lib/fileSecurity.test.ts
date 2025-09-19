/**
 * フロントエンド側ファイル安全性チェック機能のテスト
 */

import {
  checkFileExtension,
  checkFileSize,
  checkMimeType,
  checkFileName,
  comprehensiveFileSecurityCheck,
  batchFileSecurityCheck,
  formatSecurityCheckResult
} from '../../src/lib/fileSecurity';

// テスト用のFileオブジェクトを作成するヘルパー
function createMockFile(name: string, size: number, type: string = ''): File {
  const file = new File(['x'.repeat(size)], name, { type });
  return file;
}

describe('ファイル安全性チェック機能', () => {
  
  describe('checkFileExtension', () => {
    
    test('許可された拡張子（.xlsx）', () => {
      const result = checkFileExtension('test.xlsx');
      expect(result.safe).toBe(true);
      expect(result.riskLevel).toBe('low');
      expect(result.details?.detectedExtension).toBe('.xlsx');
    });
    
    test('許可された拡張子（.xls）', () => {
      const result = checkFileExtension('test.xls');
      expect(result.safe).toBe(true);
      expect(result.riskLevel).toBe('low');
      expect(result.details?.detectedExtension).toBe('.xls');
    });
    
    test('大文字小文字を区別しない', () => {
      const result = checkFileExtension('TEST.XLSX');
      expect(result.safe).toBe(true);
      expect(result.details?.detectedExtension).toBe('.xlsx');
    });
    
    test('マクロ付きファイル（.xlsm）の拒否', () => {
      const result = checkFileExtension('macro_file.xlsm');
      expect(result.safe).toBe(false);
      expect(result.riskLevel).toBe('high');
      expect(result.reason).toContain('マクロ付き');
      expect(result.details?.threatType).toBe('macro_enabled');
    });
    
    test('危険な実行ファイル（.exe）の拒否', () => {
      const result = checkFileExtension('malware.exe');
      expect(result.safe).toBe(false);
      expect(result.riskLevel).toBe('critical');
      expect(result.reason).toContain('危険なファイル形式');
      expect(result.details?.threatType).toBe('dangerous_executable');
    });
    
    test('サポートされていない拡張子（.pdf）', () => {
      const result = checkFileExtension('document.pdf');
      expect(result.safe).toBe(false);
      expect(result.riskLevel).toBe('medium');
      expect(result.reason).toContain('サポートされていない');
    });
    
    test('拡張子なしのファイル', () => {
      const result = checkFileExtension('noextension');
      expect(result.safe).toBe(false);
      expect(result.riskLevel).toBe('medium');
    });
  });
  
  describe('checkFileSize', () => {
    
    test('有効なファイルサイズ（1KB）', () => {
      const file = createMockFile('test.xlsx', 1024);
      const result = checkFileSize(file);
      expect(result.safe).toBe(true);
      expect(result.riskLevel).toBe('low');
      expect(result.details?.fileSize).toBe(1024);
    });
    
    test('有効なファイルサイズ（10MB）', () => {
      const file = createMockFile('test.xlsx', 10 * 1024 * 1024);
      const result = checkFileSize(file);
      expect(result.safe).toBe(true);
      expect(result.riskLevel).toBe('low');
    });
    
    test('ファイルサイズ上限超過（25MB）', () => {
      const file = createMockFile('large.xlsx', 25 * 1024 * 1024);
      const result = checkFileSize(file);
      expect(result.safe).toBe(false);
      expect(result.riskLevel).toBe('medium');
      expect(result.reason).toContain('上限');
      expect(result.suggestion).toContain('20MB以下');
    });
    
    test('ファイルサイズ下限未満（50バイト）', () => {
      const file = createMockFile('tiny.xlsx', 50);
      const result = checkFileSize(file);
      expect(result.safe).toBe(false);
      expect(result.riskLevel).toBe('medium');
      expect(result.reason).toContain('小さすぎます');
    });
    
    test('空ファイル（0バイト）', () => {
      const file = createMockFile('empty.xlsx', 0);
      const result = checkFileSize(file);
      expect(result.safe).toBe(false);
      expect(result.riskLevel).toBe('medium');
    });
  });
  
  describe('checkMimeType', () => {
    
    test('許可されたMIMEタイプ（.xlsx）', () => {
      const file = createMockFile(
        'test.xlsx', 
        1024, 
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
      );
      const result = checkMimeType(file);
      expect(result.safe).toBe(true);
      expect(result.riskLevel).toBe('low');
    });
    
    test('許可されたMIMEタイプ（.xls）', () => {
      const file = createMockFile('test.xls', 1024, 'application/vnd.ms-excel');
      const result = checkMimeType(file);
      expect(result.safe).toBe(true);
      expect(result.riskLevel).toBe('low');
    });
    
    test('MIMEタイプ未設定', () => {
      const file = createMockFile('test.xlsx', 1024, '');
      const result = checkMimeType(file);
      expect(result.safe).toBe(true);
      expect(result.riskLevel).toBe('low');
      expect(result.details?.warning).toContain('未設定');
    });
    
    test('許可されていないMIMEタイプ', () => {
      const file = createMockFile('test.pdf', 1024, 'application/pdf');
      const result = checkMimeType(file);
      expect(result.safe).toBe(false);
      expect(result.riskLevel).toBe('medium');
      expect(result.reason).toContain('許可されていない');
    });
  });
  
  describe('checkFileName', () => {
    
    test('有効なファイル名', () => {
      const result = checkFileName('valid_file_name.xlsx');
      expect(result.safe).toBe(true);
      expect(result.riskLevel).toBe('low');
    });
    
    test('日本語ファイル名', () => {
      const result = checkFileName('テストファイル.xlsx');
      expect(result.safe).toBe(true);
      expect(result.riskLevel).toBe('low');
    });
    
    test('危険な文字を含むファイル名', () => {
      const result = checkFileName('file<script>.xlsx');
      expect(result.safe).toBe(false);
      expect(result.riskLevel).toBe('medium');
      expect(result.reason).toContain('危険な文字');
    });
    
    test('長すぎるファイル名', () => {
      const longName = 'a'.repeat(300) + '.xlsx';
      const result = checkFileName(longName);
      expect(result.safe).toBe(false);
      expect(result.riskLevel).toBe('low');
      expect(result.reason).toContain('長すぎます');
    });
    
    test('Windows予約語', () => {
      const result = checkFileName('CON.xlsx');
      expect(result.safe).toBe(false);
      expect(result.riskLevel).toBe('medium');
      expect(result.reason).toContain('予約語');
    });
  });
  
  describe('comprehensiveFileSecurityCheck', () => {
    
    test('安全なファイル', () => {
      const file = createMockFile(
        'safe_file.xlsx', 
        1024, 
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
      );
      const result = comprehensiveFileSecurityCheck(file);
      
      expect(result.safe).toBe(true);
      expect(result.riskLevel).toBe('low');
      expect(result.failedChecks).toHaveLength(0);
      expect(result.summary).toContain('合格');
    });
    
    test('マクロ付きファイル', () => {
      const file = createMockFile('macro.xlsm', 1024);
      const result = comprehensiveFileSecurityCheck(file);
      
      expect(result.safe).toBe(false);
      expect(result.riskLevel).toBe('high');
      expect(result.failedChecks.length).toBeGreaterThan(0);
      expect(result.summary).toContain('高リスク');
    });
    
    test('実行ファイル', () => {
      const file = createMockFile('malware.exe', 1024);
      const result = comprehensiveFileSecurityCheck(file);
      
      expect(result.safe).toBe(false);
      expect(result.riskLevel).toBe('critical');
      expect(result.summary).toContain('クリティカル');
    });
    
    test('複数の問題があるファイル', () => {
      const file = createMockFile('bad<file>.exe', 50); // 危険な拡張子 + 危険な文字 + 小さすぎるサイズ
      const result = comprehensiveFileSecurityCheck(file);
      
      expect(result.safe).toBe(false);
      expect(result.riskLevel).toBe('critical');
      expect(result.failedChecks.length).toBeGreaterThan(1);
    });
  });
  
  describe('batchFileSecurityCheck', () => {
    
    test('全て安全なファイル', () => {
      const files = [
        createMockFile('file1.xlsx', 1024, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
        createMockFile('file2.xls', 2048, 'application/vnd.ms-excel')
      ];
      
      const result = batchFileSecurityCheck(files);
      
      expect(result.overallSafe).toBe(true);
      expect(result.summary.safe).toBe(2);
      expect(result.summary.unsafe).toBe(0);
      expect(result.summary.critical).toBe(0);
    });
    
    test('一部危険なファイル', () => {
      const files = [
        createMockFile('safe.xlsx', 1024, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
        createMockFile('macro.xlsm', 1024),
        createMockFile('malware.exe', 1024)
      ];
      
      const result = batchFileSecurityCheck(files);
      
      expect(result.overallSafe).toBe(false);
      expect(result.summary.safe).toBe(1);
      expect(result.summary.unsafe).toBe(2);
      expect(result.summary.critical).toBe(1); // .exe ファイル
    });
    
    test('空の配列', () => {
      const result = batchFileSecurityCheck([]);
      
      expect(result.overallSafe).toBe(true);
      expect(result.summary.safe).toBe(0);
      expect(result.summary.unsafe).toBe(0);
      expect(result.summary.critical).toBe(0);
    });
  });
  
  describe('formatSecurityCheckResult', () => {
    
    test('クリティカルレベルのフォーマット', () => {
      const result = {
        safe: false,
        reason: 'テストエラー',
        riskLevel: 'critical' as const,
        suggestion: 'テスト提案'
      };
      
      const formatted = formatSecurityCheckResult(result);
      
      expect(formatted.icon).toBe('🚨');
      expect(formatted.color).toBe('text-red-600');
      expect(formatted.title).toBe('クリティカル');
      expect(formatted.message).toBe('テストエラー');
    });
    
    test('安全レベルのフォーマット', () => {
      const result = {
        safe: true,
        reason: 'テスト成功',
        riskLevel: 'low' as const
      };
      
      const formatted = formatSecurityCheckResult(result);
      
      expect(formatted.icon).toBe('✅');
      expect(formatted.color).toBe('text-green-600');
      expect(formatted.title).toBe('安全');
      expect(formatted.message).toBe('テスト成功');
    });
  });
  
  describe('エッジケース', () => {
    
    test('非常に長いファイル名', () => {
      const longName = 'a'.repeat(1000) + '.xlsx';
      const result = checkFileName(longName);
      expect(result.safe).toBe(false);
    });
    
    test('特殊文字を含むファイル名', () => {
      const specialName = 'file\x00\x01\x02.xlsx';
      const result = checkFileName(specialName);
      expect(result.safe).toBe(false);
    });
    
    test('最大サイズぎりぎりのファイル', () => {
      const file = createMockFile('max_size.xlsx', 20 * 1024 * 1024); // 20MB
      const result = checkFileSize(file);
      expect(result.safe).toBe(true);
    });
    
    test('最大サイズを1バイト超過', () => {
      const file = createMockFile('over_max.xlsx', 20 * 1024 * 1024 + 1); // 20MB + 1byte
      const result = checkFileSize(file);
      expect(result.safe).toBe(false);
    });
  });
});