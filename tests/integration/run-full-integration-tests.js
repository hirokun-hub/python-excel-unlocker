#!/usr/bin/env node

/**
 * 完全統合テスト実行スクリプト（SAM Local API自動起動付き）
 */

const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const axios = require('axios');

// 環境変数の読み込み
require('dotenv').config({ path: path.join(__dirname, '.env.test') });

const TEST_TYPES = {
  'api': 'API統合テスト',
  's3': 'S3連携テスト',
  'e2e': 'E2Eテスト',
  'all': '全統合テスト'
};

let samProcess = null;

/**
 * メイン実行関数
 */
async function main() {
  const testType = process.argv[2] || 'all';
  
  if (!TEST_TYPES[testType]) {
    console.error('❌ 無効なテストタイプ:', testType);
    console.log('使用可能なテストタイプ:');
    Object.entries(TEST_TYPES).forEach(([key, desc]) => {
      console.log(`  ${key}: ${desc}`);
    });
    process.exit(1);
  }

  console.log('🧪 Secure Excel Unlock 完全統合テスト実行');
  console.log('===============================================');
  console.log(`📋 実行テスト: ${TEST_TYPES[testType]}`);
  console.log('');

  try {
    // 環境変数チェック
    await checkEnvironment();
    
    // 依存関係インストール
    await installDependencies();
    
    // SAM Local API起動
    await startSamLocalApi();
    
    // テスト実行
    await runTests(testType);
    
    console.log('');
    console.log('✅ 完全統合テスト完了');
    
  } catch (error) {
    console.error('');
    console.error('❌ 完全統合テスト失敗:', error.message);
    process.exit(1);
  } finally {
    // SAM Local API停止
    await stopSamLocalApi();
  }
}

/**
 * 環境変数チェック
 */
async function checkEnvironment() {
  console.log('🔍 環境変数チェック中...');
  
  const requiredEnvVars = [
    'S3_BUCKET_NAME',
    'API_BASE_URL',
    'TEST_USER_EMAIL'
  ];
  
  const missingVars = requiredEnvVars.filter(varName => !process.env[varName]);
  
  if (missingVars.length > 0) {
    throw new Error(`必須環境変数が設定されていません: ${missingVars.join(', ')}`);
  }
  
  console.log('✅ 環境変数チェック完了');
}

/**
 * 依存関係インストール
 */
async function installDependencies() {
  console.log('📦 依存関係インストール中...');
  
  return new Promise((resolve, reject) => {
    const npm = spawn('npm', ['install'], {
      cwd: __dirname,
      stdio: 'inherit'
    });
    
    npm.on('close', (code) => {
      if (code === 0) {
        console.log('✅ 依存関係インストール完了');
        resolve();
      } else {
        reject(new Error(`npm install failed with code ${code}`));
      }
    });
  });
}

/**
 * SAM Local API起動
 */
async function startSamLocalApi() {
  console.log('🚀 SAM Local API起動中...');
  
  // 既存のプロセスを停止
  const pidFile = path.join(__dirname, 'sam-local.pid');
  if (fs.existsSync(pidFile)) {
    const pid = fs.readFileSync(pidFile, 'utf8').trim();
    try {
      process.kill(pid, 'SIGTERM');
      fs.unlinkSync(pidFile);
      await sleep(2000); // 停止待機
    } catch (e) {
      // プロセスが既に停止している場合は無視
    }
  }

  // SAM build実行
  console.log('🔨 SAMアプリケーションビルド中...');
  await new Promise((resolve, reject) => {
    const samBuild = spawn('sam', ['build'], {
      cwd: path.join(__dirname, '../..'),
      stdio: 'inherit'
    });
    
    samBuild.on('close', (code) => {
      if (code === 0) {
        console.log('✅ SAMビルド完了');
        resolve();
      } else {
        reject(new Error(`SAM build failed with code ${code}`));
      }
    });
  });

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
  await waitForAPI('http://localhost:3001', 60000);
  console.log('✅ SAM Local API起動完了');
}

/**
 * SAM Local API停止
 */
async function stopSamLocalApi() {
  if (samProcess) {
    console.log('🛑 SAM Local API停止中...');
    samProcess.kill('SIGTERM');
    
    // PIDファイル削除
    const pidFile = path.join(__dirname, 'sam-local.pid');
    if (fs.existsSync(pidFile)) {
      fs.unlinkSync(pidFile);
    }
    
    console.log('✅ SAM Local API停止完了');
  }
}

/**
 * API起動待機関数
 */
async function waitForAPI(baseUrl, timeout) {
  const startTime = Date.now();
  
  while (Date.now() - startTime < timeout) {
    try {
      await axios.get(`${baseUrl}/health`, { timeout: 5000 });
      return;
    } catch (error) {
      if (error.response?.status) {
        // レスポンスが返ってきた場合はAPI起動済み
        return;
      }
      // 接続エラーの場合は待機継続
      await sleep(2000);
    }
  }
  
  throw new Error(`SAM Local API起動タイムアウト (${timeout}ms)`);
}

/**
 * テスト実行
 */
async function runTests(testType) {
  console.log(`🧪 ${TEST_TYPES[testType]}実行中...`);
  
  const jestArgs = ['--verbose', '--detectOpenHandles', '--forceExit'];
  
  // テストタイプに応じてパターンを指定
  switch (testType) {
    case 'api':
      jestArgs.push('api/');
      break;
    case 's3':
      jestArgs.push('s3/');
      break;
    case 'e2e':
      jestArgs.push('e2e/');
      break;
    case 'all':
      // すべてのテストを実行（sam-startup以外）
      jestArgs.push('--testPathIgnorePatterns=test-sam-local-startup.js');
      break;
  }
  
  return new Promise((resolve, reject) => {
    const jest = spawn('npx', ['jest', ...jestArgs], {
      cwd: __dirname,
      stdio: 'inherit',
      env: { ...process.env, NODE_ENV: 'test' }
    });
    
    jest.on('close', (code) => {
      if (code === 0) {
        console.log(`✅ ${TEST_TYPES[testType]}完了`);
        resolve();
      } else {
        reject(new Error(`テスト実行失敗 (exit code: ${code})`));
      }
    });
  });
}

/**
 * 待機ヘルパー
 */
function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// プロセス終了時のクリーンアップ
process.on('SIGINT', async () => {
  console.log('\n🛑 プロセス中断 - クリーンアップ中...');
  await stopSamLocalApi();
  process.exit(0);
});

process.on('SIGTERM', async () => {
  console.log('\n🛑 プロセス終了 - クリーンアップ中...');
  await stopSamLocalApi();
  process.exit(0);
});

// スクリプト実行
if (require.main === module) {
  main().catch(error => {
    console.error('❌ 完全統合テスト実行エラー:', error);
    process.exit(1);
  });
}

module.exports = { main };