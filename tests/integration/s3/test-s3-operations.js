/**
 * S3連携統合テスト
 */

const { 
  getUploadUrl,
  uploadFileToS3,
  downloadFileFromS3,
  loadTestFile,
  createTempFile,
  validateSuccessResponse,
  S3_BUCKET_NAME
} = require('../utils/test-helpers');

const AWS = require('aws-sdk');

describe('S3連携統合テスト', () => {
  let s3Client;

  beforeAll(() => {
    // AWS SDK設定
    s3Client = new AWS.S3({
      region: process.env.AWS_REGION || 'ap-northeast-1'
    });
  });

  describe('ファイルアップロードテスト', () => {
    test('署名付きURLを使用したファイルアップロードが成功する', async () => {
      // テスト用ファイルの作成
      const testContent = Buffer.from('テストファイルの内容です');
      const fileName = `test-upload-${Date.now()}.xlsx`;
      const fileSize = testContent.length;

      try {
        // 1. 署名付きURL取得
        const urlResponse = await getUploadUrl(fileName, fileSize);
        validateSuccessResponse(urlResponse, ['uploadUrl', 'fileKey']);

        // 2. S3へのアップロード
        const uploadSuccess = await uploadFileToS3(urlResponse.uploadUrl, testContent);
        expect(uploadSuccess).toBe(true);

        // 3. S3でファイルの存在確認
        const headParams = {
          Bucket: S3_BUCKET_NAME,
          Key: urlResponse.fileKey
        };

        const headResult = await s3Client.headObject(headParams).promise();
        expect(headResult.ContentLength).toBe(fileSize);

        console.log('✅ ファイルアップロード成功:', {
          fileKey: urlResponse.fileKey,
          size: headResult.ContentLength
        });

        // クリーンアップ
        await s3Client.deleteObject(headParams).promise();

      } catch (error) {
        console.error('❌ ファイルアップロードテスト失敗:', error);
        throw error;
      }
    });

    test('大きなファイルのアップロードが成功する', async () => {
      // 5MBのテストファイル作成
      const largeContent = Buffer.alloc(5 * 1024 * 1024, 'A');
      const fileName = `large-test-${Date.now()}.xlsx`;
      const fileSize = largeContent.length;

      try {
        const urlResponse = await getUploadUrl(fileName, fileSize);
        const uploadSuccess = await uploadFileToS3(urlResponse.uploadUrl, largeContent);
        
        expect(uploadSuccess).toBe(true);

        // ファイル存在確認
        const headParams = {
          Bucket: S3_BUCKET_NAME,
          Key: urlResponse.fileKey
        };

        const headResult = await s3Client.headObject(headParams).promise();
        expect(headResult.ContentLength).toBe(fileSize);

        console.log('✅ 大きなファイルのアップロード成功:', {
          size: `${Math.round(fileSize / 1024 / 1024)}MB`
        });

        // クリーンアップ
        await s3Client.deleteObject(headParams).promise();

      } catch (error) {
        console.error('❌ 大きなファイルアップロードテスト失敗:', error);
        throw error;
      }
    });

    test('異なるファイル形式のアップロードが成功する', async () => {
      const testCases = [
        {
          fileName: 'test.xlsx',
          contentType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
          content: Buffer.from('XLSX content')
        },
        {
          fileName: 'test.xls',
          contentType: 'application/vnd.ms-excel',
          content: Buffer.from('XLS content')
        }
      ];

      for (const testCase of testCases) {
        try {
          const fileName = `${testCase.fileName}-${Date.now()}`;
          const urlResponse = await getUploadUrl(fileName, testCase.content.length, testCase.contentType);
          const uploadSuccess = await uploadFileToS3(urlResponse.uploadUrl, testCase.content, testCase.contentType);
          
          expect(uploadSuccess).toBe(true);

          console.log(`✅ ${testCase.fileName} アップロード成功`);

          // クリーンアップ
          await s3Client.deleteObject({
            Bucket: S3_BUCKET_NAME,
            Key: urlResponse.fileKey
          }).promise();

        } catch (error) {
          console.error(`❌ ${testCase.fileName} アップロードテスト失敗:`, error);
          throw error;
        }
      }
    });
  });

  describe('ファイルダウンロードテスト', () => {
    test('署名付きURLを使用したファイルダウンロードが成功する', async () => {
      const testContent = Buffer.from('ダウンロードテスト用ファイル');
      const fileKey = `test-download-${Date.now()}.xlsx`;

      try {
        // 1. テストファイルをS3に直接アップロード
        await s3Client.putObject({
          Bucket: S3_BUCKET_NAME,
          Key: fileKey,
          Body: testContent,
          ContentType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        }).promise();

        // 2. 署名付きダウンロードURL生成
        const downloadUrl = s3Client.getSignedUrl('getObject', {
          Bucket: S3_BUCKET_NAME,
          Key: fileKey,
          Expires: 300 // 5分
        });

        // 3. ファイルダウンロード
        const downloadedContent = await downloadFileFromS3(downloadUrl);
        
        expect(Buffer.compare(downloadedContent, testContent)).toBe(0);

        console.log('✅ ファイルダウンロード成功:', {
          originalSize: testContent.length,
          downloadedSize: downloadedContent.length
        });

        // クリーンアップ
        await s3Client.deleteObject({
          Bucket: S3_BUCKET_NAME,
          Key: fileKey
        }).promise();

      } catch (error) {
        console.error('❌ ファイルダウンロードテスト失敗:', error);
        throw error;
      }
    });

    test('期限切れ署名付きURLでダウンロードが失敗する', async () => {
      const fileKey = `test-expired-${Date.now()}.xlsx`;

      try {
        // テストファイルをS3にアップロード
        await s3Client.putObject({
          Bucket: S3_BUCKET_NAME,
          Key: fileKey,
          Body: Buffer.from('期限切れテスト'),
          ContentType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        }).promise();

        // 期限切れの署名付きURL生成（1秒）
        const expiredUrl = s3Client.getSignedUrl('getObject', {
          Bucket: S3_BUCKET_NAME,
          Key: fileKey,
          Expires: 1
        });

        // 2秒待機して期限切れにする
        await new Promise(resolve => setTimeout(resolve, 2000));

        // ダウンロード試行（失敗するはず）
        try {
          await downloadFileFromS3(expiredUrl);
          expect(true).toBe(false); // ここに到達したらテスト失敗
        } catch (downloadError) {
          expect(downloadError.response.status).toBeGreaterThanOrEqual(400);
          console.log('✅ 期限切れURLが正しく拒否されました');
        }

        // クリーンアップ
        await s3Client.deleteObject({
          Bucket: S3_BUCKET_NAME,
          Key: fileKey
        }).promise();

      } catch (error) {
        console.error('❌ 期限切れURLテスト失敗:', error);
        throw error;
      }
    });
  });

  describe('S3バケット設定テスト', () => {
    test('S3バケットのCORS設定が適切', async () => {
      try {
        const corsResult = await s3Client.getBucketCors({
          Bucket: S3_BUCKET_NAME
        }).promise();

        expect(corsResult.CORSRules).toBeDefined();
        expect(corsResult.CORSRules.length).toBeGreaterThan(0);

        const corsRule = corsResult.CORSRules[0];
        expect(corsRule.AllowedMethods).toContain('PUT');
        expect(corsRule.AllowedMethods).toContain('GET');
        expect(corsRule.AllowedHeaders).toContain('*');

        console.log('✅ S3バケットCORS設定確認完了');

      } catch (error) {
        console.error('❌ CORS設定確認失敗:', error);
        throw error;
      }
    });

    test('S3バケットのパブリックアクセスブロック設定が適切', async () => {
      try {
        const publicAccessResult = await s3Client.getPublicAccessBlock({
          Bucket: S3_BUCKET_NAME
        }).promise();

        const config = publicAccessResult.PublicAccessBlockConfiguration;
        expect(config.BlockPublicAcls).toBe(true);
        expect(config.IgnorePublicAcls).toBe(true);
        expect(config.BlockPublicPolicy).toBe(true);
        expect(config.RestrictPublicBuckets).toBe(true);

        console.log('✅ S3バケットパブリックアクセスブロック設定確認完了');

      } catch (error) {
        console.error('❌ パブリックアクセスブロック設定確認失敗:', error);
        throw error;
      }
    });
  });

  describe('パフォーマンステスト', () => {
    test('ファイルアップロード速度が適切', async () => {
      const testContent = Buffer.alloc(1024 * 1024, 'A'); // 1MB
      const fileName = `perf-test-${Date.now()}.xlsx`;

      const startTime = Date.now();

      try {
        const urlResponse = await getUploadUrl(fileName, testContent.length);
        await uploadFileToS3(urlResponse.uploadUrl, testContent);

        const uploadTime = Date.now() - startTime;
        expect(uploadTime).toBeLessThan(10000); // 10秒以内

        console.log(`✅ 1MBファイルアップロード時間: ${uploadTime}ms`);

        // クリーンアップ
        await s3Client.deleteObject({
          Bucket: S3_BUCKET_NAME,
          Key: urlResponse.fileKey
        }).promise();

      } catch (error) {
        console.error('❌ アップロード速度テスト失敗:', error);
        throw error;
      }
    });

    test('ファイルダウンロード速度が適切', async () => {
      const testContent = Buffer.alloc(1024 * 1024, 'B'); // 1MB
      const fileKey = `perf-download-${Date.now()}.xlsx`;

      try {
        // ファイルをS3にアップロード
        await s3Client.putObject({
          Bucket: S3_BUCKET_NAME,
          Key: fileKey,
          Body: testContent
        }).promise();

        // ダウンロード速度測定
        const downloadUrl = s3Client.getSignedUrl('getObject', {
          Bucket: S3_BUCKET_NAME,
          Key: fileKey,
          Expires: 300
        });

        const startTime = Date.now();
        await downloadFileFromS3(downloadUrl);
        const downloadTime = Date.now() - startTime;

        expect(downloadTime).toBeLessThan(10000); // 10秒以内

        console.log(`✅ 1MBファイルダウンロード時間: ${downloadTime}ms`);

        // クリーンアップ
        await s3Client.deleteObject({
          Bucket: S3_BUCKET_NAME,
          Key: fileKey
        }).promise();

      } catch (error) {
        console.error('❌ ダウンロード速度テスト失敗:', error);
        throw error;
      }
    });
  });
});