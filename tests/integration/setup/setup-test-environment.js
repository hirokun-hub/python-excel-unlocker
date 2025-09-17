/**
 * 統合テスト環境セットアップスクリプト
 */

const AWS = require('aws-sdk');
const fs = require('fs');
const path = require('path');

// 環境変数の読み込み
require('dotenv').config({ path: path.join(__dirname, '../.env.test') });

const S3_BUCKET_NAME = process.env.S3_BUCKET_NAME;
const AWS_REGION = process.env.AWS_REGION || 'ap-northeast-1';

async function setupTestEnvironment() {
  console.log('🚀 統合テスト環境セットアップ開始');

  try {
    // AWS SDK設定
    AWS.config.update({ region: AWS_REGION });
    const s3 = new AWS.S3();

    // S3バケットの存在確認
    console.log('📦 S3バケットの確認中...');
    try {
      await s3.headBucket({ Bucket: S3_BUCKET_NAME }).promise();
      console.log(`✅ S3バケット確認完了: ${S3_BUCKET_NAME}`);
    } catch (error) {
      if (error.statusCode === 404) {
        console.log(`❌ S3バケットが存在しません: ${S3_BUCKET_NAME}`);
        console.log('以下のコマンドでバケットを作成してください:');
        console.log(`aws s3 mb s3://${S3_BUCKET_NAME} --region ${AWS_REGION}`);
        process.exit(1);
      } else {
        throw error;
      }
    }

    // テスト用ファイルのアップロード
    console.log('📁 テスト用ファイルのアップロード中...');
    await uploadTestFiles(s3);

    // CORS設定の確認
    console.log('🔧 CORS設定の確認中...');
    await checkCorsConfiguration(s3);

    console.log('🎉 統合テスト環境セットアップ完了');

  } catch (error) {
    console.error('❌ セットアップ失敗:', error);
    process.exit(1);
  }
}

async function uploadTestFiles(s3) {
  const testFiles = [
    {
      key: 'test-uploads/password-protected-test.xlsx',
      content: Buffer.from('模擬パスワード付きExcelファイル1'),
      contentType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    },
    {
      key: 'test-uploads/password-protected-test2.xlsx',
      content: Buffer.from('模擬パスワード付きExcelファイル2'),
      contentType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    },
    {
      key: 'test-uploads/small-file.xlsx',
      content: Buffer.from('小さなテストファイル'),
      contentType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    },
    {
      key: 'test-uploads/large-file.xlsx',
      content: Buffer.alloc(10 * 1024 * 1024, 'L'), // 10MB
      contentType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    },
    {
      key: 'test-uploads/corrupted-file.xlsx',
      content: Buffer.from('破損したファイル内容'),
      contentType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    },
    {
      key: 'test-uploads/document.pdf',
      content: Buffer.from('PDFファイル内容'),
      contentType: 'application/pdf'
    }
  ];

  for (const file of testFiles) {
    try {
      await s3.putObject({
        Bucket: S3_BUCKET_NAME,
        Key: file.key,
        Body: file.content,
        ContentType: file.contentType
      }).promise();

      console.log(`  ✅ ${file.key} アップロード完了`);
    } catch (error) {
      console.error(`  ❌ ${file.key} アップロード失敗:`, error);
      throw error;
    }
  }
}

async function checkCorsConfiguration(s3) {
  try {
    const corsResult = await s3.getBucketCors({ Bucket: S3_BUCKET_NAME }).promise();
    console.log('  ✅ CORS設定確認完了');
    
    const corsRule = corsResult.CORSRules[0];
    if (!corsRule.AllowedMethods.includes('PUT') || !corsRule.AllowedMethods.includes('GET')) {
      console.warn('  ⚠️ CORS設定にPUTまたはGETメソッドが含まれていません');
    }
  } catch (error) {
    if (error.code === 'NoSuchCORSConfiguration') {
      console.warn('  ⚠️ CORS設定が見つかりません。以下の設定を追加してください:');
      console.warn(`
{
  "CORSRules": [
    {
      "AllowedHeaders": ["*"],
      "AllowedMethods": ["GET", "PUT", "POST", "DELETE"],
      "AllowedOrigins": ["*"],
      "ExposeHeaders": ["ETag"],
      "MaxAgeSeconds": 3000
    }
  ]
}
      `);
    } else {
      throw error;
    }
  }
}

// 環境変数チェック
function checkEnvironmentVariables() {
  const requiredVars = ['S3_BUCKET_NAME', 'API_BASE_URL', 'TEST_USER_EMAIL'];
  const missingVars = requiredVars.filter(varName => !process.env[varName]);

  if (missingVars.length > 0) {
    console.error('❌ 以下の環境変数が設定されていません:');
    missingVars.forEach(varName => console.error(`  - ${varName}`));
    console.error('\n.env.testファイルを作成して必要な環境変数を設定してください。');
    process.exit(1);
  }
}

// .env.testファイルのサンプル作成
function createSampleEnvFile() {
  const envFilePath = path.join(__dirname, '../.env.test');
  
  if (!fs.existsSync(envFilePath)) {
    const sampleContent = `# 統合テスト用環境変数
# 実際の値に置き換えてください

# AWS設定
AWS_REGION=ap-northeast-1
S3_BUCKET_NAME=your-excel-unlock-test-bucket

# API設定
API_BASE_URL=https://your-api-gateway-url.execute-api.ap-northeast-1.amazonaws.com/prod

# テストユーザー設定
TEST_USER_EMAIL=test@example.com

# オプション設定
LOG_LEVEL=DEBUG
`;

    fs.writeFileSync(envFilePath, sampleContent);
    console.log(`📝 サンプル環境変数ファイルを作成しました: ${envFilePath}`);
    console.log('実際の値に置き換えてから再実行してください。');
    process.exit(0);
  }
}

// メイン実行
if (require.main === module) {
  // .env.testファイルが存在しない場合はサンプルを作成
  const envFilePath = path.join(__dirname, '../.env.test');
  if (!fs.existsSync(envFilePath)) {
    createSampleEnvFile();
  }

  checkEnvironmentVariables();
  setupTestEnvironment();
}

module.exports = {
  setupTestEnvironment,
  uploadTestFiles,
  checkCorsConfiguration
};