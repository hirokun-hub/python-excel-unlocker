/**
 * 統合テスト用ヘルパー関数
 */

const fs = require('fs');
const path = require('path');
const axios = require('axios');

// 環境変数から設定を取得
const API_BASE_URL = process.env.API_BASE_URL || 'https://your-api-gateway-url.execute-api.ap-northeast-1.amazonaws.com/prod';
const S3_BUCKET_NAME = process.env.S3_BUCKET_NAME || 'your-excel-unlock-bucket';
const TEST_USER_EMAIL = process.env.TEST_USER_EMAIL || 'test@example.com';

/**
 * テスト用JWTトークンを生成（モック）
 */
function generateTestJWT() {
  // 実際のJWTトークンの代わりにテスト用の識別子を使用
  // 本来はGoogle OAuth2のID Tokenを使用するが、テスト環境では簡略化
  return `test-jwt-token-${TEST_USER_EMAIL}`;
}

/**
 * APIクライアントの作成
 */
function createApiClient() {
  return axios.create({
    baseURL: API_BASE_URL,
    timeout: 30000,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${generateTestJWT()}`
    }
  });
}

/**
 * テスト用ファイルの読み込み
 */
function loadTestFile(filename) {
  const filePath = path.join(__dirname, '../fixtures', filename);
  if (!fs.existsSync(filePath)) {
    throw new Error(`テストファイルが見つかりません: ${filePath}`);
  }
  return fs.readFileSync(filePath);
}

/**
 * 署名付きURLの取得
 */
async function getUploadUrl(fileName, fileSize, contentType = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet') {
  const client = createApiClient();
  
  const response = await client.post('/presigned-urls', {
    fileName,
    fileSize,
    contentType
  });
  
  return response.data;
}

/**
 * S3へのファイルアップロード
 */
async function uploadFileToS3(uploadUrl, fileBuffer, contentType = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet') {
  const response = await axios.put(uploadUrl, fileBuffer, {
    headers: {
      'Content-Type': contentType
    },
    timeout: 30000
  });
  
  return response.status === 200;
}

/**
 * Excel解除APIの呼び出し
 */
async function unlockExcel(fileKey, passwords) {
  const client = createApiClient();
  
  const response = await client.post('/unlock', {
    fileKey,
    passwords
  });
  
  return response.data;
}

/**
 * S3からのファイルダウンロード
 */
async function downloadFileFromS3(downloadUrl) {
  const response = await axios.get(downloadUrl, {
    responseType: 'arraybuffer',
    timeout: 30000
  });
  
  return Buffer.from(response.data);
}

/**
 * テスト用の一時ファイル作成
 */
function createTempFile(content, extension = '.xlsx') {
  const tempDir = path.join(__dirname, '../temp');
  if (!fs.existsSync(tempDir)) {
    fs.mkdirSync(tempDir, { recursive: true });
  }
  
  const tempFileName = `test-${Date.now()}${extension}`;
  const tempFilePath = path.join(tempDir, tempFileName);
  
  fs.writeFileSync(tempFilePath, content);
  
  return {
    path: tempFilePath,
    name: tempFileName,
    cleanup: () => {
      if (fs.existsSync(tempFilePath)) {
        fs.unlinkSync(tempFilePath);
      }
    }
  };
}

/**
 * テスト後のクリーンアップ
 */
function cleanup() {
  const tempDir = path.join(__dirname, '../temp');
  if (fs.existsSync(tempDir)) {
    const files = fs.readdirSync(tempDir);
    files.forEach(file => {
      fs.unlinkSync(path.join(tempDir, file));
    });
    fs.rmdirSync(tempDir);
  }
}

/**
 * レスポンス検証ヘルパー
 */
function validateApiResponse(response, expectedFields) {
  if (!response || typeof response !== 'object') {
    throw new Error('レスポンスが無効です');
  }
  
  expectedFields.forEach(field => {
    if (!(field in response)) {
      throw new Error(`必須フィールドが不足しています: ${field}`);
    }
  });
}

/**
 * エラーレスポンス検証ヘルパー
 */
function validateErrorResponse(response, expectedErrorCode) {
  validateApiResponse(response, ['success', 'error', 'message']);
  
  if (response.success !== false) {
    throw new Error('エラーレスポンスのsuccessフィールドがfalseではありません');
  }
  
  if (expectedErrorCode && response.error !== expectedErrorCode) {
    throw new Error(`期待されるエラーコード: ${expectedErrorCode}, 実際: ${response.error}`);
  }
}

/**
 * 成功レスポンス検証ヘルパー
 */
function validateSuccessResponse(response, expectedFields = []) {
  const defaultFields = ['success'];
  const allFields = [...defaultFields, ...expectedFields];
  
  validateApiResponse(response, allFields);
  
  if (response.success !== true) {
    throw new Error('成功レスポンスのsuccessフィールドがtrueではありません');
  }
}

/**
 * 待機ヘルパー
 */
function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

module.exports = {
  API_BASE_URL,
  S3_BUCKET_NAME,
  TEST_USER_EMAIL,
  generateTestJWT,
  createApiClient,
  loadTestFile,
  getUploadUrl,
  uploadFileToS3,
  unlockExcel,
  downloadFileFromS3,
  createTempFile,
  cleanup,
  validateApiResponse,
  validateErrorResponse,
  validateSuccessResponse,
  sleep
};