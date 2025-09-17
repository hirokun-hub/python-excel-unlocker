/**
 * Jest統合テスト用セットアップ
 */

// テストタイムアウトの設定
jest.setTimeout(60000); // 60秒

// 環境変数の設定
process.env.NODE_ENV = 'test';

// AWS SDK設定
process.env.AWS_REGION = process.env.AWS_REGION || 'ap-northeast-1';

// テスト用環境変数の検証
const requiredEnvVars = [
  'API_BASE_URL',
  'S3_BUCKET_NAME',
  'TEST_USER_EMAIL'
];

const missingEnvVars = requiredEnvVars.filter(envVar => !process.env[envVar]);

if (missingEnvVars.length > 0) {
  console.warn('⚠️ 以下の環境変数が設定されていません:');
  missingEnvVars.forEach(envVar => {
    console.warn(`  - ${envVar}`);
  });
  console.warn('統合テストが正常に動作しない可能性があります。');
  console.warn('.env.testファイルまたは環境変数を設定してください。');
}

// グローバルテストヘルパーの設定
global.testConfig = {
  apiBaseUrl: process.env.API_BASE_URL,
  s3BucketName: process.env.S3_BUCKET_NAME,
  testUserEmail: process.env.TEST_USER_EMAIL,
  awsRegion: process.env.AWS_REGION || 'ap-northeast-1'
};

// テスト開始時のログ
console.log('🧪 統合テスト環境初期化完了');
console.log('📋 テスト設定:');
console.log(`  - API Base URL: ${global.testConfig.apiBaseUrl || '未設定'}`);
console.log(`  - S3 Bucket: ${global.testConfig.s3BucketName || '未設定'}`);
console.log(`  - Test User: ${global.testConfig.testUserEmail || '未設定'}`);
console.log(`  - AWS Region: ${global.testConfig.awsRegion}`);

// テスト後のクリーンアップ
afterAll(async () => {
  console.log('🧹 統合テスト終了 - クリーンアップ実行');
  
  // 必要に応じてクリーンアップ処理を追加
  // 例: 一時ファイルの削除、テスト用S3オブジェクトの削除など
});

// エラーハンドリング
process.on('unhandledRejection', (reason, promise) => {
  console.error('❌ 未処理のPromise拒否:', reason);
});

process.on('uncaughtException', (error) => {
  console.error('❌ 未処理の例外:', error);
  process.exit(1);
});