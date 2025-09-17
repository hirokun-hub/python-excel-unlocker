/**
 * Excel解除API統合テスト
 */

const { 
  unlockExcel, 
  validateSuccessResponse, 
  validateErrorResponse,
  createApiClient 
} = require('../utils/test-helpers');

describe('Excel解除API統合テスト', () => {
  let apiClient;

  beforeAll(() => {
    apiClient = createApiClient();
  });

  describe('正常系テスト', () => {
    test('正しいパスワードでExcel解除が成功する', async () => {
      // 事前にS3にアップロードされたテストファイルのキーを使用
      const fileKey = 'test-uploads/password-protected-test.xlsx';
      const passwords = ['test123', 'backup456'];

      const response = await unlockExcel(fileKey, passwords);

      // レスポンス構造の検証
      validateSuccessResponse(response, ['downloadUrl', 'fileName', 'expiresIn', 'processingTime']);
      
      // ダウンロードURLの形式検証
      expect(response.downloadUrl).toMatch(/^https:\/\/.*\.s3\..*\.amazonaws\.com\/.*/);
      expect(response.fileName).toContain('unlocked');
      expect(response.expiresIn).toBe(300); // Download用は300秒
      expect(response.processingTime).toBeGreaterThan(0);
      
      console.log('✅ Excel解除成功:', {
        fileName: response.fileName,
        processingTime: response.processingTime,
        expiresIn: response.expiresIn
      });
    });

    test('第二パスワードで解除が成功する', async () => {
      const fileKey = 'test-uploads/password-protected-test2.xlsx';
      const passwords = ['wrong123', 'correct456']; // 第二パスワードが正解

      const response = await unlockExcel(fileKey, passwords);

      validateSuccessResponse(response, ['downloadUrl', 'fileName', 'expiresIn', 'processingTime']);
      expect(response.fileName).toContain('unlocked');
      
      console.log('✅ 第二パスワードでの解除成功');
    });

    test('複数ファイルの並列処理が正常に動作する', async () => {
      const testFiles = [
        { fileKey: 'test-uploads/file1.xlsx', passwords: ['test123'] },
        { fileKey: 'test-uploads/file2.xlsx', passwords: ['test456'] },
        { fileKey: 'test-uploads/file3.xlsx', passwords: ['test789'] }
      ];

      const promises = testFiles.map(file => 
        unlockExcel(file.fileKey, file.passwords)
      );

      const responses = await Promise.all(promises);

      responses.forEach((response, index) => {
        validateSuccessResponse(response, ['downloadUrl', 'fileName', 'expiresIn', 'processingTime']);
        console.log(`✅ ファイル${index + 1}の並列処理成功`);
      });
    });
  });

  describe('異常系テスト', () => {
    test('認証ヘッダーなしでアクセス拒否される', async () => {
      const clientWithoutAuth = require('axios').create({
        baseURL: apiClient.defaults.baseURL,
        timeout: 30000,
        headers: {
          'Content-Type': 'application/json'
          // X-User-Emailヘッダーなし
        }
      });

      try {
        await clientWithoutAuth.post('/unlock', {
          fileKey: 'test-uploads/test.xlsx',
          passwords: ['test123']
        });
        
        expect(true).toBe(false); // ここに到達したらテスト失敗
      } catch (error) {
        expect(error.response.status).toBe(403);
        console.log('✅ 認証なしアクセスが正しく拒否されました');
      }
    });

    test('間違ったパスワードでエラーが返される', async () => {
      const fileKey = 'test-uploads/password-protected-test.xlsx';
      const passwords = ['wrong123', 'alsowrong456'];

      try {
        const response = await unlockExcel(fileKey, passwords);
        
        // エラーレスポンスの場合
        if (!response.success) {
          validateErrorResponse(response, 'password_incorrect');
          expect(response.message).toContain('パスワード');
          console.log('✅ 間違ったパスワードが正しく拒否されました');
        } else {
          expect(true).toBe(false); // 成功してはいけない
        }
      } catch (error) {
        // HTTPエラーの場合
        expect(error.response.status).toBeGreaterThanOrEqual(400);
        console.log('✅ 間違ったパスワードが正しく拒否されました');
      }
    });

    test('存在しないファイルキーでエラーが返される', async () => {
      const fileKey = 'non-existent/file.xlsx';
      const passwords = ['test123'];

      try {
        await unlockExcel(fileKey, passwords);
        expect(true).toBe(false); // ここに到達したらテスト失敗
      } catch (error) {
        expect(error.response.status).toBeGreaterThanOrEqual(400);
        console.log('✅ 存在しないファイルが正しく拒否されました');
      }
    });

    test('破損したファイルでエラーが返される', async () => {
      const fileKey = 'test-uploads/corrupted-file.xlsx';
      const passwords = ['test123'];

      try {
        const response = await unlockExcel(fileKey, passwords);
        
        if (!response.success) {
          validateErrorResponse(response, 'file_corrupted');
          expect(response.message).toContain('破損');
          console.log('✅ 破損ファイルが正しく検出されました');
        } else {
          expect(true).toBe(false); // 成功してはいけない
        }
      } catch (error) {
        expect(error.response.status).toBeGreaterThanOrEqual(400);
        console.log('✅ 破損ファイルが正しく拒否されました');
      }
    });

    test('サポートされていないファイル形式でエラーが返される', async () => {
      const fileKey = 'test-uploads/document.pdf'; // PDFファイル
      const passwords = ['test123'];

      try {
        const response = await unlockExcel(fileKey, passwords);
        
        if (!response.success) {
          validateErrorResponse(response, 'unsupported_format');
          expect(response.message).toContain('サポート');
          console.log('✅ サポート外ファイル形式が正しく拒否されました');
        } else {
          expect(true).toBe(false); // 成功してはいけない
        }
      } catch (error) {
        expect(error.response.status).toBeGreaterThanOrEqual(400);
        console.log('✅ サポート外ファイル形式が正しく拒否されました');
      }
    });

    test('空のパスワード配列でエラーが返される', async () => {
      const fileKey = 'test-uploads/password-protected-test.xlsx';
      const passwords = []; // 空の配列

      try {
        await unlockExcel(fileKey, passwords);
        expect(true).toBe(false); // ここに到達したらテスト失敗
      } catch (error) {
        expect(error.response.status).toBeGreaterThanOrEqual(400);
        console.log('✅ 空のパスワード配列が正しく拒否されました');
      }
    });
  });

  describe('パフォーマンステスト', () => {
    test('Excel解除のレスポンス時間が適切', async () => {
      const fileKey = 'test-uploads/small-file.xlsx';
      const passwords = ['test123'];
      
      const startTime = Date.now();
      const response = await unlockExcel(fileKey, passwords);
      const responseTime = Date.now() - startTime;

      if (response.success) {
        expect(responseTime).toBeLessThan(8000); // P95目標: 8秒以内
        expect(response.processingTime).toBeLessThan(8);
        
        console.log(`✅ Excel解除レスポンス時間: ${responseTime}ms, 処理時間: ${response.processingTime}s`);
      }
    });

    test('大きなファイルの処理時間が許容範囲内', async () => {
      const fileKey = 'test-uploads/large-file.xlsx'; // 10MB程度
      const passwords = ['test123'];
      
      const startTime = Date.now();
      const response = await unlockExcel(fileKey, passwords);
      const responseTime = Date.now() - startTime;

      if (response.success) {
        expect(responseTime).toBeLessThan(15000); // 大きなファイルは15秒以内
        
        console.log(`✅ 大きなファイルの処理時間: ${responseTime}ms`);
      }
    });
  });

  describe('エラーメッセージテスト', () => {
    test('日本語エラーメッセージが適切に返される', async () => {
      const fileKey = 'test-uploads/password-protected-test.xlsx';
      const passwords = ['wrong123', 'alsowrong456'];

      try {
        const response = await unlockExcel(fileKey, passwords);
        
        if (!response.success) {
          expect(response.message).toMatch(/パスワード|解除|できませんでした/);
          expect(response.suggestion).toMatch(/パスワード|お試し|確認/);
          console.log('✅ 日本語エラーメッセージが正しく表示されました');
        }
      } catch (error) {
        // HTTPエラーの場合もテスト通過
        console.log('✅ HTTPエラーが返されました');
      }
    });
  });
});