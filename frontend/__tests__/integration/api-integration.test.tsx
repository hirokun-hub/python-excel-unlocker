/**
 * フロントエンド API統合テスト
 * JWT認証対応版
 */

import { getUploadUrl, unlockExcel, uploadFileToS3 } from '@/lib/api';

// モック設定
const mockApiBaseUrl = 'http://localhost:8000'; // テスト用のベースURL
const mockUserEmail = 'test@example.com';
const mockIdToken = 'mock.jwt.token';

// 環境変数をテスト用に設定
process.env.NEXT_PUBLIC_API_URL = mockApiBaseUrl;

// fetch のモック
global.fetch = jest.fn();

// getSession のモック
jest.mock('next-auth/react', () => ({
  getSession: jest.fn(() => Promise.resolve({
    user: {
      email: mockUserEmail,
      name: 'Test User'
    },
    idToken: mockIdToken,
    expires: '2025-12-31T23:59:59.999Z'
  }))
}));

describe('API統合テスト', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    
    // getSessionモックをデフォルト値にリセット
    const { getSession } = require('next-auth/react');
    (getSession as jest.Mock).mockResolvedValue({
      user: {
        email: mockUserEmail,
        name: 'Test User'
      },
      idToken: mockIdToken,
      expires: '2025-12-31T23:59:59.999Z'
    });
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
        expect.stringContaining('/presigned-urls'),
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${mockIdToken}`
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
        expect.stringContaining('/unlock'),
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${mockIdToken}`
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
        expect.stringContaining('/unlock'),
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${mockIdToken}`
          }),
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

  describe('JWT認証', () => {
    test('セッションがない場合は認証エラーが発生する', async () => {
      // getSessionをnullを返すようにモック
      const { getSession } = require('next-auth/react');
      (getSession as jest.Mock).mockResolvedValueOnce(null);

      await expect(getUploadUrl('test-file.xlsx', 1024, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'))
        .rejects.toThrow('認証が必要です。ログインしてください。');
    });

    test('IDトークンがない場合は認証エラーが発生する', async () => {
      // IDトークンなしのセッションをモック
      const { getSession } = require('next-auth/react');
      (getSession as jest.Mock).mockResolvedValueOnce({
        user: { email: mockUserEmail },
        // idTokenなし
      });

      await expect(getUploadUrl('test-file.xlsx', 1024, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'))
        .rejects.toThrow('認証トークンが見つかりません。再ログインしてください。');
    });

    test('401エラーで適切な認証エラーメッセージが表示される', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({
          success: false,
          error: 'unauthorized',
          message: 'Invalid token'
        })
      });

      await expect(getUploadUrl('test-file.xlsx', 1024, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'))
        .rejects.toThrow('認証に失敗しました。再ログインしてください。');
    });

    test('403エラーで適切な認証エラーメッセージが表示される', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 403,
        json: async () => ({
          success: false,
          error: 'forbidden',
          message: 'Access denied'
        })
      });

      await expect(unlockExcel('uploads/test-file.xlsx', ['password123']))
        .rejects.toThrow('認証に失敗しました。再ログインしてください。');
    });
  });

  describe('レスポンスバリデーション', () => {
    test('getUploadUrl: 必須フィールドが不足している場合はエラーが発生する', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          // uploadUrlとfileKeyが不足
        })
      });

      await expect(getUploadUrl('test-file.xlsx', 1024, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'))
        .rejects.toThrow('署名付きURL取得レスポンスの形式が不正です');
    });

    test('unlockExcel: successフィールドが不正な場合はエラーが発生する', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          // successフィールドがない
          downloadUrl: 'https://example.com/file.xlsx'
        })
      });

      await expect(unlockExcel('uploads/test-file.xlsx', ['password123']))
        .rejects.toThrow('Excel解除レスポンスの形式が不正です');
    });

    test('null レスポンスの場合はエラーが発生する', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => null
      });

      await expect(getUploadUrl('test-file.xlsx', 1024, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'))
        .rejects.toThrow('不正なAPIレスポンス形式です');
    });
  });

  describe('uploadFileToS3', () => {
    test('S3へのファイルアップロードが成功する', async () => {
      const mockFile = new File(['test content'], 'test.xlsx', {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
      });
      const mockUploadUrl = 'https://s3.amazonaws.com/bucket/key?signature=...';

      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
      });

      const result = await uploadFileToS3(mockUploadUrl, mockFile);

      expect(fetch).toHaveBeenCalledWith(
        mockUploadUrl,
        expect.objectContaining({
          method: 'PUT',
          body: mockFile,
          headers: {
            'Content-Type': mockFile.type,
          }
        })
      );

      expect(result.ok).toBe(true);
    });

    test('S3アップロードエラーが適切に処理される', async () => {
      const mockFile = new File(['test content'], 'test.xlsx', {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
      });
      const mockUploadUrl = 'https://s3.amazonaws.com/bucket/key?signature=...';

      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 403,
      });

      await expect(uploadFileToS3(mockUploadUrl, mockFile))
        .rejects.toThrow('ファイルアップロードエラー: 403');
    });
  });

  describe('リトライ機構', () => {
    test('一時的なエラーでリトライが実行される', async () => {
      // 将来のリトライ機能実装のためのプレースホルダー
      // 現在は基本的なエラーハンドリングのみテスト
      (fetch as jest.Mock).mockRejectedValueOnce(new Error('Temporary error'));

      await expect(getUploadUrl('test-file.xlsx', 1024, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'))
        .rejects.toThrow('Temporary error');
    });
  });
});