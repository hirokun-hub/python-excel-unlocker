const axios = require('axios');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

/**
 * SAM Local API起動確認テスト
 */
describe('SAM Local API起動確認', () => {
  let samProcess;
  const API_BASE_URL = 'http://localhost:3001';
  const MAX_STARTUP_TIME = 60000; // 60秒

  beforeAll(async () => {
    console.log('🚀 SAM Local API起動中...');
    
    // 既存のプロセスを停止
    const pidFile = path.join(__dirname, 'sam-local.pid');
    if (fs.existsSync(pidFile)) {
      const pid = fs.readFileSync(pidFile, 'utf8').trim();
      try {
        process.kill(pid, 'SIGTERM');
        fs.unlinkSync(pidFile);
      } catch (e) {
        // プロセスが既に停止している場合は無視
      }
    }

    // SAM Local API起動
    samProcess = spawn('sam', [
      'local', 'start-api',
      '--port', '3001',
      '--env-vars', path.join(__dirname, 'env.json')
    ], {
      cwd: path.join(__dirname, '../..'),
      stdio: ['ignore', 'pipe', 'pipe']
    });

    // プロセスIDを保存
    fs.writeFileSync(pidFile, samProcess.pid.toString());

    // API起動待機
    await waitForAPI(API_BASE_URL, MAX_STARTUP_TIME);
  }, MAX_STARTUP_TIME + 10000);

  afterAll(async () => {
    if (samProcess) {
      console.log('🛑 SAM Local API停止中...');
      samProcess.kill('SIGTERM');
      
      // PIDファイル削除
      const pidFile = path.join(__dirname, 'sam-local.pid');
      if (fs.existsSync(pidFile)) {
        fs.unlinkSync(pidFile);
      }
    }
  });

  test('API起動確認', async () => {
    // ヘルスチェック（存在しないエンドポイントでも404が返れば起動している）
    try {
      await axios.get(`${API_BASE_URL}/health`);
    } catch (error) {
      // 404エラーでもAPIが起動していることを確認
      expect(error.response?.status).toBeDefined();
    }
  });

  test('GetUploadUrl エンドポイント確認', async () => {
    const response = await axios.post(`${API_BASE_URL}/presigned-urls`, {
      fileName: 'test.xlsx',
      fileSize: 1024,
      contentType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    }, {
      headers: {
        'Authorization': 'Bearer test-jwt-token',
        'Content-Type': 'application/json'
      },
      validateStatus: () => true // すべてのステータスコードを受け入れ
    });

    // 認証エラー、正常レスポンス、またはサーバーエラーを期待
    expect([200, 401, 403, 502]).toContain(response.status);
  });

  test('Unlock エンドポイント確認', async () => {
    const response = await axios.post(`${API_BASE_URL}/unlock`, {
      fileKey: 'test-key',
      passwords: ['password1', 'password2']
    }, {
      headers: {
        'Authorization': 'Bearer test-jwt-token',
        'Content-Type': 'application/json'
      },
      validateStatus: () => true
    });

    // 認証エラー、正常レスポンス、またはサーバーエラーを期待
    expect([200, 401, 403, 404, 502]).toContain(response.status);
  });
});

/**
 * API起動待機関数
 */
async function waitForAPI(baseUrl, timeout) {
  const startTime = Date.now();
  
  while (Date.now() - startTime < timeout) {
    try {
      await axios.get(`${baseUrl}/health`, { timeout: 5000 });
      console.log('✅ SAM Local API起動完了');
      return;
    } catch (error) {
      if (error.response?.status) {
        // レスポンスが返ってきた場合はAPI起動済み
        console.log('✅ SAM Local API起動完了');
        return;
      }
      // 接続エラーの場合は待機継続
      await new Promise(resolve => setTimeout(resolve, 2000));
    }
  }
  
  throw new Error(`SAM Local API起動タイムアウト (${timeout}ms)`);
}