/**
 * S3条件拘束付きアップロード機能の統合テスト
 * タスク19: S3プリサイン条件拘束の実装テスト
 */

const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');
const path = require('path');

// テスト設定
const API_BASE_URL = process.env.API_BASE_URL || 'http://localhost:3001';
const TEST_JWT_TOKEN = process.env.TEST_JWT_TOKEN || 'test-jwt-token';

describe('S3条件拘束付きアップロード統合テスト', () => {
  let uploadResponse;
  
  beforeAll(async () => {
    // テスト用のExcelファイルを作成
    const testFilePath = path.join(__dirname, '../fixtures/test-file.xlsx');
    if (!fs.existsSync(testFilePath)) {
      // 簡単なテストファイルを作成（実際のExcelファイルではないが、テスト用）
      fs.writeFileSync(testFilePath, 'PK\x03\x04test excel content');
    }
  });

  test('条件拘束付き署名付きURL取得 - 正常系', async () => {
    const requestData = {
      fileName: 'test-file.xlsx',
      fileSize: 1024000,
      contentType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    };

    const response = await axios.post(
      `${API_BASE_URL}/presigned-urls`,
      requestData,
      {
        headers: {
          'Authorization': `Bearer ${TEST_JWT_TOKEN}`,
          'Content-Type': 'application/json'
        }
      }
    );

    expect(response.status).toBe(200);
    expect(response.data.success).toBe(true);
    expect(response.data.uploadUrl).toBeDefined();
    expect(response.data.uploadFields).toBeDefined();
    expect(response.data.method).toBe('POST');
    expect(response.data.fileKey).toBeDefined();
    expect(response.data.expiresIn).toBe(60);

    // アップロードフィールドの検証
    const uploadFields = response.data.uploadFields;
    expect(uploadFields['Content-Type']).toBe(requestData.contentType);
    expect(uploadFields.key).toBeDefined();

    uploadResponse = response.data;
  });

  test('条件拘束付きファイルアップロード - 正常系', async () => {
    if (!uploadResponse) {
      throw new Error('署名付きURL取得テストが先に実行される必要があります');
    }

    // テストファイルの作成
    const testContent = Buffer.from('PK\x03\x04test excel content for constrained upload');
    const testFilePath = path.join(__dirname, '../fixtures/constrained-test.xlsx');
    fs.writeFileSync(testFilePath, testContent);

    // FormDataを作成
    const formData = new FormData();
    
    // 署名付きPOSTのフィールドを追加
    Object.entries(uploadResponse.uploadFields).forEach(([key, value]) => {
      formData.append(key, value);
    });
    
    // ファイルを最後に追加
    formData.append('file', fs.createReadStream(testFilePath));

    try {
      const response = await axios.post(uploadResponse.uploadUrl, formData, {
        headers: {
          ...formData.getHeaders()
        },
        maxRedirects: 0,
        validateStatus: (status) => status < 400
      });

      // S3へのアップロードは通常204または200を返す
      expect([200, 204]).toContain(response.status);
    } catch (error) {
      if (error.response) {
        console.error('アップロードエラー:', error.response.status, error.response.data);
      }
      throw error;
    } finally {
      // テストファイルをクリーンアップ
      if (fs.existsSync(testFilePath)) {
        fs.unlinkSync(testFilePath);
      }
    }
  });

  test('ファイルサイズ制限超過 - エラー系', async () => {
    const requestData = {
      fileName: 'large-file.xlsx',
      fileSize: 25 * 1024 * 1024, // 25MB（制限超過）
      contentType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    };

    try {
      await axios.post(
        `${API_BASE_URL}/presigned-urls`,
        requestData,
        {
          headers: {
            'Authorization': `Bearer ${TEST_JWT_TOKEN}`,
            'Content-Type': 'application/json'
          }
        }
      );
      
      // ここに到達すべきではない
      expect(true).toBe(false);
    } catch (error) {
      expect(error.response.status).toBe(400);
      expect(error.response.data.success).toBe(false);
      expect(error.response.data.error).toBe('file_too_large');
      expect(error.response.data.message).toContain('20MB以下');
    }
  });

  test('非対応ファイル形式 - エラー系', async () => {
    const requestData = {
      fileName: 'document.pdf',
      fileSize: 1024000,
      contentType: 'application/pdf' // 非対応形式
    };

    try {
      await axios.post(
        `${API_BASE_URL}/presigned-urls`,
        requestData,
        {
          headers: {
            'Authorization': `Bearer ${TEST_JWT_TOKEN}`,
            'Content-Type': 'application/json'
          }
        }
      );
      
      // ここに到達すべきではない
      expect(true).toBe(false);
    } catch (error) {
      expect(error.response.status).toBe(400);
      expect(error.response.data.success).toBe(false);
      expect(error.response.data.error).toBe('unsupported_format');
      expect(error.response.data.message).toContain('.xlsx または .xls');
    }
  });

  test('Content-Type偽装防止テスト', async () => {
    // 正しいContent-Typeで署名付きURL取得
    const requestData = {
      fileName: 'test-file.xlsx',
      fileSize: 1024,
      contentType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    };

    const response = await axios.post(
      `${API_BASE_URL}/presigned-urls`,
      requestData,
      {
        headers: {
          'Authorization': `Bearer ${TEST_JWT_TOKEN}`,
          'Content-Type': 'application/json'
        }
      }
    );

    expect(response.status).toBe(200);
    
    // 異なるContent-Typeでアップロードを試行
    const testContent = Buffer.from('fake content');
    const testFilePath = path.join(__dirname, '../fixtures/fake-content.txt');
    fs.writeFileSync(testFilePath, testContent);

    const formData = new FormData();
    
    // 署名付きPOSTのフィールドを追加
    Object.entries(response.data.uploadFields).forEach(([key, value]) => {
      if (key === 'Content-Type') {
        // Content-Typeを偽装
        formData.append(key, 'text/plain');
      } else {
        formData.append(key, value);
      }
    });
    
    formData.append('file', fs.createReadStream(testFilePath));

    try {
      await axios.post(response.data.uploadUrl, formData, {
        headers: {
          ...formData.getHeaders()
        },
        maxRedirects: 0
      });
      
      // 偽装が成功した場合はテスト失敗
      expect(true).toBe(false);
    } catch (error) {
      // S3が条件拘束により拒否することを期待
      expect(error.response.status).toBeGreaterThanOrEqual(400);
    } finally {
      // テストファイルをクリーンアップ
      if (fs.existsSync(testFilePath)) {
        fs.unlinkSync(testFilePath);
      }
    }
  });

  test('認証なしアクセス - エラー系', async () => {
    const requestData = {
      fileName: 'test-file.xlsx',
      fileSize: 1024000,
      contentType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    };

    try {
      await axios.post(
        `${API_BASE_URL}/presigned-urls`,
        requestData,
        {
          headers: {
            'Content-Type': 'application/json'
            // Authorizationヘッダーなし
          }
        }
      );
      
      // ここに到達すべきではない
      expect(true).toBe(false);
    } catch (error) {
      expect(error.response.status).toBe(401);
      expect(error.response.data.success).toBe(false);
      expect(error.response.data.error).toBe('authentication_failed');
    }
  });

  afterAll(async () => {
    // テストファイルのクリーンアップ
    const testFiles = [
      path.join(__dirname, '../fixtures/test-file.xlsx'),
      path.join(__dirname, '../fixtures/constrained-test.xlsx'),
      path.join(__dirname, '../fixtures/fake-content.txt')
    ];

    testFiles.forEach(filePath => {
      if (fs.existsSync(filePath)) {
        fs.unlinkSync(filePath);
      }
    });
  });
});