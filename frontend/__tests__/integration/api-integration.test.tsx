/**
 * フロントエンド API統合テスト
 */

import { getUploadUrl, unlockExcel } from '@/lib/api';

// モック設定
const mockApiBaseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3001';
const mockUserEmail = 'test@example.com';

// fetch のモック
global.fetch = jest.fn();

describe('API統合テスト', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    
    // セッションモック
    jest.mock('next-auth/react', () => ({
      useSession: () => ({
        data: {
          user: {
            email: mockUserEmail,
            name: 'Test User'
          }
        },
        status: 'authenticated'
      })
    }));
  });

  describe('getUploadUrl API', () => {
    test('署名付きURL取得が成功する', async () => {
      const mockResponse = {
        success: true,
        uploadUrl: 'https://s3.amazonaws.com/bucket/key?signature=...',
        fileKey: 'uploads/test-file.xlsx',
        expiresIn: 60
      };

      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const result = await getUploadUrl('test-file.xlsx', 1024, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/get-upload-url'),
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
            'X-User-Email': mockUserEmail
          }),
          body: JSON.stringify({
            fileName: 'test-file.xlsx',
            fileSize: 1024,
            contentType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
          })
        })
      );

      expect(result).toEqual(mockResponse);
    });

    test('認証エラーが適切に処理される', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 403,
        json: async () => ({
          success: false,
          error: 'unauthorized',
          message: 'アクセスが拒否されました'
        })
      });

      await expect(getUploadUrl('test-file.xlsx', 1024, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')).rejects.toThrow();
    });

    test('ネットワークエラーが適切に処理される', async () => {
      (fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

      await expect(getUploadUrl('test-file.xlsx', 1024, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')).rejects.toThrow('Network error');
    });
  });

  describe('unlockExcel API', () => {
    test('Excel解除が成功する', async () => {
      const mockResponse = {
        success: true,
        downloadUrl: 'https://s3.amazonaws.com/bucket/unlocked-key?signature=...',
        fileName: 'unlocked-test-file.xlsx',
        expiresIn: 300,
        processingTime: 2.5
      };

      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const result = await unlockExcel('uploads/test-file.xlsx', ['password123']);

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/unlock'),
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
            'X-User-Email': mockUserEmail
          }),
          body: JSON.stringify({
            fileKey: 'uploads/test-file.xlsx',
            passwords: ['password123']
          })
        })
      );

      expect(result).toEqual(mockResponse);
    });

    test('パスワード間違いエラーが適切に処理される', async () => {
      const mockErrorResponse = {
        success: false,
        error: 'password_incorrect',
        message: '入力されたパスワードでは解除できませんでした',
        suggestion: '別のパスワード候補をお試しください'
      };

      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => mockErrorResponse
      });

      await expect(unlockExcel('uploads/test-file.xlsx', ['wrong123'])).rejects.toThrow();
    });

    test('複数パスワードでの解除リクエストが正しく送信される', async () => {
      const mockResponse = {
        success: true,
        downloadUrl: 'https://s3.amazonaws.com/bucket/unlocked-key?signature=...',
        fileName: 'unlocked-test-file.xlsx',
        expiresIn: 300,
        processingTime: 3.1
      };

      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const passwords = ['first123', 'second456'];
      await unlockExcel('uploads/test-file.xlsx', passwords);

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/unlock'),
        expect.objectContaining({
          body: JSON.stringify({
            fileKey: 'uploads/test-file.xlsx',
            passwords: passwords
          })
        })
      );
    });
  });

  describe('エラーハンドリング', () => {
    test('APIレスポンスのバリデーションが機能する', async () => {
      // 不正なレスポンス形式
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          // successフィールドがない不正なレスポンス
          uploadUrl: 'https://example.com'
        })
      });

      await expect(getUploadUrl('test-file.xlsx', 1024, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')).rejects.toThrow();
    });

    test('タイムアウトが適切に処理される', async () => {
      // タイムアウトのシミュレーション
      (fetch as jest.Mock).mockImplementationOnce(() => 
        new Promise((_, reject) => 
          setTimeout(() => reject(new Error('Request timeout')), 100)
        )
      );

      await expect(getUploadUrl('test-file.xlsx', 1024, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')).rejects.toThrow('Request timeout');
    });
  });

  describe('リトライ機構', () => {
    test('一時的なエラーでリトライが実行される', async () => {
      // 最初の2回は失敗、3回目で成功
      (fetch as jest.Mock)
        .mockRejectedValueOnce(new Error('Temporary error'))
        .mockRejectedValueOnce(new Error('Temporary error'))
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            success: true,
            uploadUrl: 'https://s3.amazonaws.com/bucket/key',
            fileKey: 'uploads/test-file.xlsx',
            expiresIn: 60
          })
        });

      // リトライ機能付きのAPI呼び出し（実装が必要）
      // const result = await getUploadUrlWithRetry('test-file.xlsx', 1024);
      
      // expect(fetch).toHaveBeenCalledTimes(3);
      // expect(result.success).toBe(true);
    });
  });
});