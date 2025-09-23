import { getUploadUrl, unlockExcel, uploadFileToS3, unlockFiles } from '@/lib/api';
import { getSession } from 'next-auth/react';
import { getBotProtectionTokens } from '@/lib/botProtection';

jest.mock('next-auth/react', () => ({
  getSession: jest.fn(),
}));

jest.mock('@/lib/botProtection', () => ({
  getBotProtectionTokens: jest.fn(),
}));

const mockSession = {
  user: { email: 'tester@example.com' },
  idToken: 'id-token',
  expires: '2099-01-01T00:00:00.000Z',
};

describe('APIユーティリティのエラーハンドリング', () => {
  beforeEach(() => {
    global.fetch = jest.fn() as unknown as typeof fetch;
    (getSession as jest.Mock).mockResolvedValue(mockSession);
    (getBotProtectionTokens as jest.Mock).mockResolvedValue({});
    process.env.NEXT_PUBLIC_API_URL = 'http://localhost:8000';
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('セッションが取得できない場合に例外を投げる', async () => {
    (getSession as jest.Mock).mockResolvedValueOnce(null);

    await expect(
      getUploadUrl('sample.xlsx', 1000, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
    ).rejects.toThrow('認証が必要です');

    expect(global.fetch).not.toHaveBeenCalled();
  });

  it('IDトークンが存在しない場合に例外を投げる', async () => {
    (getSession as jest.Mock).mockResolvedValueOnce({
      user: { email: 'tester@example.com' },
      expires: '2099-01-01T00:00:00.000Z',
    });

    await expect(
      getUploadUrl('sample.xlsx', 1000, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
    ).rejects.toThrow('認証トークンが見つかりません');

    expect(global.fetch).not.toHaveBeenCalled();
  });

  it('Bot保護トークン取得に失敗してもAPIコールを継続する', async () => {
    const warnSpy = jest.spyOn(console, 'warn').mockImplementation(() => undefined);
    (getBotProtectionTokens as jest.Mock).mockRejectedValueOnce(new Error('Token error'));

    (global.fetch as unknown as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ success: true, uploadUrl: 'https://example.com', fileKey: 'key' }),
    });

    await getUploadUrl('sample.xlsx', 1000, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');

    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/presigned-urls'),
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: 'Bearer id-token',
          'Content-Type': 'application/json',
        }),
      }),
    );

    warnSpy.mockRestore();
  });

  it('APIがエラーを返した場合にメッセージ付きで失敗する', async () => {
    (global.fetch as unknown as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 400,
      json: async () => ({ message: 'Bad Request' }),
    });

    await expect(
      getUploadUrl('sample.xlsx', 1000, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
    ).rejects.toThrow('Bad Request');
  });

  it('uploadFileToS3でPOSTとPUTの両方の経路をカバーする', async () => {
    const file = new File(['dummy'], 'test.xlsx', {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    });

    (global.fetch as unknown as jest.Mock)
      .mockResolvedValueOnce({ ok: true, json: async () => ({}) })
      .mockResolvedValueOnce({ ok: true });

    await uploadFileToS3('https://example.com/post', file, { key: 'value' });
    expect(global.fetch).toHaveBeenCalledWith(
      'https://example.com/post',
      expect.objectContaining({
        method: 'POST',
      }),
    );

    await uploadFileToS3('https://example.com/put', file);
    expect(global.fetch).toHaveBeenCalledWith(
      'https://example.com/put',
      expect.objectContaining({
        method: 'PUT',
      }),
    );
  });

  it('unlockExcelがエラーを返した場合に例外を投げる', async () => {
    (global.fetch as unknown as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 500,
      json: async () => ({ message: 'Server error' }),
    });

    await expect(unlockExcel('uploads/key.xlsx', ['pass1'])).rejects.toThrow('Server error');
  });

  it('unlockFilesは空配列を拒否する', async () => {
    await expect(unlockFiles([], ['pass1'])).rejects.toThrow('解除するファイル情報がありません');
  });

  it('unlockFilesが正しいレスポンスを返す', async () => {
    (global.fetch as unknown as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        success: true,
        results: [
          { fileName: 'sample.xlsx', status: 'success', downloadUrl: 'https://example.com' },
        ],
      }),
    });

    const result = await unlockFiles(
      [{ s3_key: 'uploads/sample.xlsx', original_name: 'sample.xlsx' }],
      ['pass1'],
    );

    expect(result.success).toBe(true);
    expect(result.results).toHaveLength(1);
  });

  it('unlockFilesが不正なレスポンス形式を検知する', async () => {
    (global.fetch as unknown as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ success: true }),
    });

    await expect(
      unlockFiles([{ s3_key: 'uploads/sample.xlsx', original_name: 'sample.xlsx' }], ['pass1']),
    ).rejects.toThrow('Excel解除レスポンスの形式が不正です');
  });
});
