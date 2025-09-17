/**
 * 統合テスト環境クリーンアップスクリプト
 */

const AWS = require('aws-sdk');
const path = require('path');

// 環境変数の読み込み
require('dotenv').config({ path: path.join(__dirname, '../.env.test') });

const S3_BUCKET_NAME = process.env.S3_BUCKET_NAME;
const AWS_REGION = process.env.AWS_REGION || 'ap-northeast-1';

async function cleanupTestEnvironment() {
  console.log('🧹 統合テスト環境クリーンアップ開始');

  try {
    // AWS SDK設定
    AWS.config.update({ region: AWS_REGION });
    const s3 = new AWS.S3();

    // テスト用ファイルの削除
    console.log('🗑️ テスト用ファイルの削除中...');
    await deleteTestFiles(s3);

    // 一時ファイルの削除
    console.log('🗑️ 一時ファイルの削除中...');
    await deleteTempFiles(s3);

    console.log('🎉 統合テスト環境クリーンアップ完了');

  } catch (error) {
    console.error('❌ クリーンアップ失敗:', error);
    process.exit(1);
  }
}

async function deleteTestFiles(s3) {
  // テスト用ファイルのプレフィックス
  const testPrefixes = [
    'test-uploads/',
    'uploads/test-',
    'uploads/parallel-test-',
    'uploads/error-test-',
    'uploads/perf-test-',
    'uploads/large-perf-test-',
    'unlocked/test-',
    'unlocked/parallel-test-',
    'unlocked/perf-test-'
  ];

  for (const prefix of testPrefixes) {
    try {
      // プレフィックスに一致するオブジェクトをリスト
      const listResult = await s3.listObjectsV2({
        Bucket: S3_BUCKET_NAME,
        Prefix: prefix
      }).promise();

      if (listResult.Contents && listResult.Contents.length > 0) {
        // オブジェクトを削除
        const deleteParams = {
          Bucket: S3_BUCKET_NAME,
          Delete: {
            Objects: listResult.Contents.map(obj => ({ Key: obj.Key }))
          }
        };

        const deleteResult = await s3.deleteObjects(deleteParams).promise();
        
        if (deleteResult.Deleted && deleteResult.Deleted.length > 0) {
          console.log(`  ✅ ${prefix}* - ${deleteResult.Deleted.length}ファイル削除完了`);
        }

        if (deleteResult.Errors && deleteResult.Errors.length > 0) {
          console.warn(`  ⚠️ ${prefix}* - ${deleteResult.Errors.length}ファイル削除失敗`);
          deleteResult.Errors.forEach(error => {
            console.warn(`    - ${error.Key}: ${error.Message}`);
          });
        }
      } else {
        console.log(`  ℹ️ ${prefix}* - 削除対象ファイルなし`);
      }
    } catch (error) {
      console.error(`  ❌ ${prefix}* 削除処理失敗:`, error);
    }
  }
}

async function deleteTempFiles(s3) {
  // 1時間以上前の一時ファイルを削除
  const oneHourAgo = new Date(Date.now() - 60 * 60 * 1000);

  try {
    const listResult = await s3.listObjectsV2({
      Bucket: S3_BUCKET_NAME,
      Prefix: 'uploads/'
    }).promise();

    if (listResult.Contents && listResult.Contents.length > 0) {
      const oldFiles = listResult.Contents.filter(obj => 
        obj.LastModified < oneHourAgo && 
        (obj.Key.includes('test-') || obj.Key.includes('temp-'))
      );

      if (oldFiles.length > 0) {
        const deleteParams = {
          Bucket: S3_BUCKET_NAME,
          Delete: {
            Objects: oldFiles.map(obj => ({ Key: obj.Key }))
          }
        };

        const deleteResult = await s3.deleteObjects(deleteParams).promise();
        
        if (deleteResult.Deleted && deleteResult.Deleted.length > 0) {
          console.log(`  ✅ 古い一時ファイル ${deleteResult.Deleted.length}件削除完了`);
        }
      } else {
        console.log('  ℹ️ 削除対象の古い一時ファイルなし');
      }
    }
  } catch (error) {
    console.error('  ❌ 一時ファイル削除処理失敗:', error);
  }
}

async function listRemainingFiles(s3) {
  console.log('📋 残存ファイル確認中...');
  
  try {
    const listResult = await s3.listObjectsV2({
      Bucket: S3_BUCKET_NAME,
      MaxKeys: 100
    }).promise();

    if (listResult.Contents && listResult.Contents.length > 0) {
      console.log(`  📁 バケット内ファイル数: ${listResult.Contents.length}`);
      
      // テスト関連ファイルが残っているかチェック
      const testFiles = listResult.Contents.filter(obj => 
        obj.Key.includes('test-') || 
        obj.Key.includes('temp-') ||
        obj.Key.startsWith('test-uploads/')
      );

      if (testFiles.length > 0) {
        console.warn(`  ⚠️ テスト関連ファイルが${testFiles.length}件残存しています:`);
        testFiles.forEach(file => {
          console.warn(`    - ${file.Key} (${file.Size} bytes)`);
        });
      } else {
        console.log('  ✅ テスト関連ファイルの残存なし');
      }
    } else {
      console.log('  ✅ バケットは空です');
    }
  } catch (error) {
    console.error('  ❌ ファイル一覧取得失敗:', error);
  }
}

// 強制クリーンアップ（全テストファイル削除）
async function forceCleanup() {
  console.log('💥 強制クリーンアップ実行中...');
  
  try {
    AWS.config.update({ region: AWS_REGION });
    const s3 = new AWS.S3();

    // 全オブジェクトをリスト
    const listResult = await s3.listObjectsV2({
      Bucket: S3_BUCKET_NAME
    }).promise();

    if (listResult.Contents && listResult.Contents.length > 0) {
      // 全オブジェクトを削除
      const deleteParams = {
        Bucket: S3_BUCKET_NAME,
        Delete: {
          Objects: listResult.Contents.map(obj => ({ Key: obj.Key }))
        }
      };

      const deleteResult = await s3.deleteObjects(deleteParams).promise();
      
      if (deleteResult.Deleted && deleteResult.Deleted.length > 0) {
        console.log(`  ✅ ${deleteResult.Deleted.length}ファイル強制削除完了`);
      }
    }

    console.log('🎉 強制クリーンアップ完了');
  } catch (error) {
    console.error('❌ 強制クリーンアップ失敗:', error);
    process.exit(1);
  }
}

// メイン実行
if (require.main === module) {
  const args = process.argv.slice(2);
  
  if (args.includes('--force')) {
    forceCleanup();
  } else {
    cleanupTestEnvironment().then(() => {
      return listRemainingFiles(new AWS.S3({ region: AWS_REGION }));
    });
  }
}

module.exports = {
  cleanupTestEnvironment,
  deleteTestFiles,
  deleteTempFiles,
  forceCleanup
};