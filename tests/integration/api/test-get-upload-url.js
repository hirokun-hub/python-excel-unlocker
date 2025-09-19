/**
 * 署名付きURL生成API統合テスト
 */

const { 
  getUploadUrl, 
  validateSuccessResponse, 
  validateErrorResponse,
  createApiClient 
} = require('../utils/test-helpers');

describe('署名付きURL生成API統合テスト', () => {
  let apiClient;

  beforeAll(() => {
    apiClient = createApiClient();
  });

  describe('正常系テスト', () => {
    test('有効なリクエストで署名付きURLが生成される', async () => {
      const fileName = 'test-file.xlsx';
      const fileSize = 1024;
      const contentType = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';

      const response = await getUploadUrl(fileName, fileSize, contentType);

      // レスポンス構造の検証
      validateSuccessResponse(response, ['uploadUrl', 'fileKey', 'expiresIn']);
      
      // 署名付きURLの形式検証
      expect(response.uploadUrl).toMatch(/^https:\/\/.*\.s3\..*\.amazonaws\.com\/.*/);
      expect(response.fileKey).toContain(fileName);
      expect(response.expiresIn).toBe(60); // Upload用は60秒
      
      console.log('✅ 署名付きURL生成成功:', {
        fileKey: response.fileKey,
        expiresIn: response.expiresIn
      });
    });

    test('異なるファイル形式でも署名付きURLが生成される', async () => {
      const testCases = [
        {
          fileName: 'test.xlsx',
          contentType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        },
        {
          fileName: 'test.xls',
          contentType: 'application/vnd.ms-excel'
        }
      ];

      for (const testCase of testCases) {
        const response = await getUploadUrl(testCase.fileName, 1024, testCase.contentType);
        
        validateSuccessResponse(response, ['uploadUrl', 'fileKey', 'expiresIn']);
        expect(response.fileKey).toContain(testCase.fileName);
        
        console.log(`✅ ${testCase.fileName} の署名付きURL生成成功`);
      }
    });

    test('大きなファイルサイズでも署名付きURLが生成される', async () => {
      const fileName = 'large-file.xlsx';
      const fileSize = 20 * 1024 * 1024; // 20MB

      const response = await getUploadUrl(fileName, fileSize);

      validateSuccessResponse(response, ['uploadUrl', 'fileKey', 'expiresIn']);
      expect(response.fileKey).toContain(fileName);
      
      console.log('✅ 大きなファイルの署名付きURL生成成功');
    });
  });

  describe('異常系テスト', () => {
    test('認証ヘッダーなしでアクセス拒否される', async () => {
      const clientWithoutAuth = require('axios').create({
        baseURL: apiClient.defaults.baseURL,
        timeout: 30000,
        headers: {
          'Content-Type': 'application/json'
          // Authorizationヘッダーなし
        }
      });

      try {
        await clientWithoutAuth.post('/presigned-urls', {
          fileName: 'test.xlsx',
          fileSize: 1024
        });
        
        // ここに到達したらテスト失敗
        expect(true).toBe(false);
      } catch (error) {
        expect(error.response.status).toBe(401);
        console.log('✅ 認証なしアクセスが正しく拒否されました');
      }
    });

    test('無効なファイル名でエラーが返される', async () => {
      try {
        await getUploadUrl('', 1024); // 空のファイル名
        expect(true).toBe(false); // ここに到達したらテスト失敗
      } catch (error) {
        expect(error.response.status).toBeGreaterThanOrEqual(400);
        console.log('✅ 無効なファイル名が正しく拒否されました');
      }
    });

    test('無効なファイルサイズでエラーが返される', async () => {
      try {
        await getUploadUrl('test.xlsx', -1); // 負のファイルサイズ
        expect(true).toBe(false); // ここに到達したらテスト失敗
      } catch (error) {
        expect(error.response.status).toBeGreaterThanOrEqual(400);
        console.log('✅ 無効なファイルサイズが正しく拒否されました');
      }
    });

    test('過大なファイルサイズでエラーが返される', async () => {
      const maxFileSize = 100 * 1024 * 1024; // 100MB（制限を超える）
      
      try {
        await getUploadUrl('huge-file.xlsx', maxFileSize);
        expect(true).toBe(false); // ここに到達したらテスト失敗
      } catch (error) {
        expect(error.response.status).toBeGreaterThanOrEqual(400);
        console.log('✅ 過大なファイルサイズが正しく拒否されました');
      }
    });
  });

  describe('パフォーマンステスト', () => {
    test('署名付きURL生成のレスポンス時間が適切', async () => {
      const startTime = Date.now();
      
      await getUploadUrl('performance-test.xlsx', 1024);
      
      const responseTime = Date.now() - startTime;
      expect(responseTime).toBeLessThan(5000); // 5秒以内
      
      console.log(`✅ 署名付きURL生成レスポンス時間: ${responseTime}ms`);
    });

    test('連続リクエストでも安定したレスポンス', async () => {
      const requests = [];
      const requestCount = 5;

      for (let i = 0; i < requestCount; i++) {
        requests.push(getUploadUrl(`concurrent-test-${i}.xlsx`, 1024));
      }

      const responses = await Promise.all(requests);
      
      responses.forEach((response, index) => {
        validateSuccessResponse(response, ['uploadUrl', 'fileKey', 'expiresIn']);
        expect(response.fileKey).toContain(`concurrent-test-${index}.xlsx`);
      });
      
      console.log(`✅ ${requestCount}件の連続リクエストが正常に処理されました`);
    });
  });
});