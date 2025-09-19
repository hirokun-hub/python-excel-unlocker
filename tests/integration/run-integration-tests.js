#!/usr/bin/env node

/**
 * 統合テスト実行メインスクリプト
 */

const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

// 環境変数の読み込み
require('dotenv').config({ path: path.join(__dirname, '.env.test') });

const TEST_TYPES = {
  'sam-startup': '統合テスト環境起動確認',
  'api': 'API統合テスト',
  's3': 'S3連携テスト',
  'e2e': 'E2Eテスト',
  'all': '全統合テスト'
};

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

  console.log('🧪 Secure Excel Unlock 統合テスト実行');
  console.log('==========================================');
  console.log(`📋 実行テスト: ${TEST_TYPES[testType]}`);
  console.log('');

  try {
    // 環境変数チェック
    await checkEnvironment();
    
    // 依存関係インストール
    await installDependencies();
    
    // テスト実行
    await runTests(testType);
    
    console.log('');
    console.log('✅ 統合テスト完了');
    
  } catch (error) {
    console.error('');
    console.error('❌ 統合テスト失敗:', error.message);
    process.exit(1);
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
 * テスト実行
 */
async function runTests(testType) {
  console.log(`🧪 ${TEST_TYPES[testType]}実行中...`);
  
  const jestArgs = ['--verbose', '--detectOpenHandles'];
  
  // テストタイプに応じてパターンを指定
  switch (testType) {
    case 'sam-startup':
      jestArgs.push('test-sam-local-startup.js');
      break;
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

// スクリプト実行
if (require.main === module) {
  main().catch(error => {
    console.error('❌ 統合テスト実行エラー:', error);
    process.exit(1);
  });
}

module.exports = { main };