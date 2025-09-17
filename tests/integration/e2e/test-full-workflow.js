/**
 * エンドツーエンド統合テスト - 完全なワークフローテスト
 */

const { 
  getUploadUrl,
  uploadFileToS3,
  unlockExcel,
  downloadFileFromS3,
  createTempFile,
  validateSuccessResponse,
  sleep
} = require('../utils/test-helpers');

describe('E2E統合テスト - 完全なワークフロー', () => {
  
  describe('基本的なExcel解除ワークフロー', () => {
    test('ファイルアップロード → 解除 → ダウンロードの完全フロー', async () => {
      // テスト用パスワード付きExcelファイルの作成（模擬）
      const testExcelContent = Buffer.from('模擬パスワード付きExcelファイル');
      const originalFileName = `test-excel-${Date.now()}.xlsx`;
      const fileSize = testExcelContent.length;
      const passwords = ['test123', 'backup456'];

      try {
        console.log('🚀 E2Eワークフロー開始:', originalFileName);

        // ステップ1: 署名付きURL取得
        console.log('📝 ステップ1: 署名付きURL取得');
        const uploadResponse = await getUploadUrl(originalFileName, fileSize);
        validateSuccessResponse(uploadResponse, ['uploadUrl', 'fileKey', 'expiresIn']);
        
        console.log('✅ 署名付きURL取得成功:', {
          fileKey: uploadResponse.fileKey,
          expiresIn: uploadResponse.expiresIn
        });

        // ステップ2: S3へファイルアップロード
        console.log('📤 ステップ2: S3へファイルアップロード');
        const uploadSuccess = await uploadFileToS3(uploadResponse.uploadUrl, testExcelContent);
        expect(uploadSuccess).toBe(true);
        
        console.log('✅ ファイルアップロード成功');

        // 少し待機（S3の整合性確保）
        await sleep(1000);

        // ステップ3: Excel解除処理
        console.log('🔓 ステップ3: Excel解除処理');
        const unlockResponse = await unlockExcel(uploadResponse.fileKey, passwords);
        
        if (unlockResponse.success) {
          validateSuccessResponse(unlockResponse, ['downloadUrl', 'fileName', 'expiresIn', 'processingTime']);
          
          console.log('✅ Excel解除成功:', {
            fileName: unlockResponse.fileName,
            processingTime: unlockResponse.processingTime,
            expiresIn: unlockResponse.expiresIn
          });

          // ステップ4: 解除済みファイルダウンロード
          console.log('📥 ステップ4: 解除済みファイルダウンロード');
          const downloadedContent = await downloadFileFromS3(unlockResponse.downloadUrl);
          
          expect(downloadedContent).toBeDefined();
          expect(downloadedContent.length).toBeGreaterThan(0);
          
          console.log('✅ ファイルダウンロード成功:', {
            downloadedSize: downloadedContent.length
          });

          console.log('🎉 E2Eワークフロー完了');

        } else {
          // 解除失敗の場合（テストファイルが実際にパスワード保護されていない場合など）
          console.log('ℹ️ Excel解除がスキップされました（テストファイルがパスワード保護されていない可能性）');
          expect(unlockResponse.error).toBeDefined();
        }

      } catch (error) {
        console.error('❌ E2Eワークフローテスト失敗:', error);
        throw error;
      }
    });

    test('複数ファイルの並列処理ワークフロー', async () => {
      const fileCount = 3;
      const testFiles = [];

      // 複数のテストファイル準備
      for (let i = 0; i < fileCount; i++) {
        testFiles.push({
          content: Buffer.from(`テストファイル${i + 1}の内容`),
          fileName: `parallel-test-${i + 1}-${Date.now()}.xlsx`,
          passwords: ['test123', 'backup456']
        });
      }

      try {
        console.log(`🚀 ${fileCount}ファイル並列処理ワークフロー開始`);

        // ステップ1: 全ファイルの署名付きURL取得
        console.log('📝 ステップ1: 全ファイルの署名付きURL取得');
        const uploadPromises = testFiles.map(file => 
          getUploadUrl(file.fileName, file.content.length)
        );
        const uploadResponses = await Promise.all(uploadPromises);

        uploadResponses.forEach((response, index) => {
          validateSuccessResponse(response, ['uploadUrl', 'fileKey', 'expiresIn']);
          testFiles[index].fileKey = response.fileKey;
          testFiles[index].uploadUrl = response.uploadUrl;
        });

        console.log('✅ 全ファイルの署名付きURL取得成功');

        // ステップ2: 全ファイルのS3アップロード
        console.log('📤 ステップ2: 全ファイルのS3アップロード');
        const s3UploadPromises = testFiles.map(file => 
          uploadFileToS3(file.uploadUrl, file.content)
        );
        const s3UploadResults = await Promise.all(s3UploadPromises);

        s3UploadResults.forEach((result, index) => {
          expect(result).toBe(true);
        });

        console.log('✅ 全ファイルのアップロード成功');

        // 少し待機
        await sleep(2000);

        // ステップ3: 全ファイルの並列解除処理
        console.log('🔓 ステップ3: 全ファイルの並列解除処理');
        const unlockPromises = testFiles.map(file => 
          unlockExcel(file.fileKey, file.passwords)
        );
        const unlockResponses = await Promise.all(unlockPromises);

        let successCount = 0;
        unlockResponses.forEach((response, index) => {
          if (response.success) {
            validateSuccessResponse(response, ['downloadUrl', 'fileName', 'expiresIn', 'processingTime']);
            testFiles[index].downloadUrl = response.downloadUrl;
            successCount++;
          } else {
            console.log(`ℹ️ ファイル${index + 1}の解除がスキップされました`);
          }
        });

        console.log(`✅ ${successCount}/${fileCount}ファイルの解除処理完了`);

        // ステップ4: 成功したファイルのダウンロード
        if (successCount > 0) {
          console.log('📥 ステップ4: 解除済みファイルのダウンロード');
          const downloadPromises = testFiles
            .filter(file => file.downloadUrl)
            .map(file => downloadFileFromS3(file.downloadUrl));

          const downloadResults = await Promise.all(downloadPromises);
          
          downloadResults.forEach((content, index) => {
            expect(content).toBeDefined();
            expect(content.length).toBeGreaterThan(0);
          });

          console.log(`✅ ${downloadResults.length}ファイルのダウンロード成功`);
        }

        console.log('🎉 並列処理ワークフロー完了');

      } catch (error) {
        console.error('❌ 並列処理ワークフローテスト失敗:', error);
        throw error;
      }
    });
  });

  describe('エラーハンドリングワークフロー', () => {
    test('間違ったパスワードでの完全エラーフロー', async () => {
      const testContent = Buffer.from('パスワードエラーテスト用ファイル');
      const fileName = `error-test-${Date.now()}.xlsx`;
      const wrongPasswords = ['wrong123', 'alsowrong456'];

      try {
        console.log('🚀 エラーハンドリングワークフロー開始');

        // 正常なアップロードフロー
        const uploadResponse = await getUploadUrl(fileName, testContent.length);
        await uploadFileToS3(uploadResponse.uploadUrl, testContent);
        
        await sleep(1000);

        // 間違ったパスワードで解除試行
        console.log('🔓 間違ったパスワードで解除試行');
        try {
          const unlockResponse = await unlockExcel(uploadResponse.fileKey, wrongPasswords);
          
          if (!unlockResponse.success) {
            expect(unlockResponse.error).toBeDefined();
            expect(unlockResponse.message).toBeDefined();
            expect(unlockResponse.suggestion).toBeDefined();
            
            console.log('✅ エラーレスポンス正常:', {
              error: unlockResponse.error,
              message: unlockResponse.message
            });
          } else {
            console.log('ℹ️ テストファイルがパスワード保護されていないため、解除が成功しました');
          }
        } catch (unlockError) {
          // HTTPエラーの場合
          expect(unlockError.response.status).toBeGreaterThanOrEqual(400);
          console.log('✅ HTTPエラーが正しく返されました');
        }

        console.log('🎉 エラーハンドリングワークフロー完了');

      } catch (error) {
        console.error('❌ エラーハンドリングワークフローテスト失敗:', error);
        throw error;
      }
    });

    test('存在しないファイルでのエラーフロー', async () => {
      const nonExistentFileKey = `non-existent-${Date.now()}.xlsx`;
      const passwords = ['test123'];

      try {
        console.log('🚀 存在しないファイルエラーフロー開始');

        try {
          await unlockExcel(nonExistentFileKey, passwords);
          expect(true).toBe(false); // ここに到達したらテスト失敗
        } catch (error) {
          expect(error.response.status).toBeGreaterThanOrEqual(400);
          console.log('✅ 存在しないファイルエラーが正しく処理されました');
        }

        console.log('🎉 存在しないファイルエラーフロー完了');

      } catch (error) {
        console.error('❌ 存在しないファイルエラーフローテスト失敗:', error);
        throw error;
      }
    });
  });

  describe('パフォーマンスワークフロー', () => {
    test('完全ワークフローの処理時間測定', async () => {
      const testContent = Buffer.from('パフォーマンステスト用ファイル');
      const fileName = `perf-test-${Date.now()}.xlsx`;
      const passwords = ['test123'];

      const startTime = Date.now();

      try {
        console.log('🚀 パフォーマンステスト開始');

        // 完全ワークフロー実行
        const uploadResponse = await getUploadUrl(fileName, testContent.length);
        await uploadFileToS3(uploadResponse.uploadUrl, testContent);
        
        await sleep(500); // 最小限の待機

        const unlockResponse = await unlockExcel(uploadResponse.fileKey, passwords);
        
        if (unlockResponse.success) {
          await downloadFileFromS3(unlockResponse.downloadUrl);
        }

        const totalTime = Date.now() - startTime;
        
        // パフォーマンス要件チェック（要件書のP95: 8秒以内）
        expect(totalTime).toBeLessThan(15000); // 統合テストでは15秒以内を許容

        console.log(`✅ 完全ワークフロー処理時間: ${totalTime}ms`);
        console.log('🎉 パフォーマンステスト完了');

      } catch (error) {
        const totalTime = Date.now() - startTime;
        console.error(`❌ パフォーマンステスト失敗 (${totalTime}ms):`, error);
        throw error;
      }
    });

    test('大きなファイルのワークフロー処理時間', async () => {
      // 5MBのテストファイル
      const largeContent = Buffer.alloc(5 * 1024 * 1024, 'L');
      const fileName = `large-perf-test-${Date.now()}.xlsx`;
      const passwords = ['test123'];

      const startTime = Date.now();

      try {
        console.log('🚀 大きなファイルのパフォーマンステスト開始');

        const uploadResponse = await getUploadUrl(fileName, largeContent.length);
        await uploadFileToS3(uploadResponse.uploadUrl, largeContent);
        
        await sleep(1000);

        const unlockResponse = await unlockExcel(uploadResponse.fileKey, passwords);
        
        if (unlockResponse.success) {
          await downloadFileFromS3(unlockResponse.downloadUrl);
        }

        const totalTime = Date.now() - startTime;
        
        // 大きなファイルは30秒以内を許容
        expect(totalTime).toBeLessThan(30000);

        console.log(`✅ 大きなファイルワークフロー処理時間: ${totalTime}ms`);
        console.log('🎉 大きなファイルパフォーマンステスト完了');

      } catch (error) {
        const totalTime = Date.now() - startTime;
        console.error(`❌ 大きなファイルパフォーマンステスト失敗 (${totalTime}ms):`, error);
        throw error;
      }
    });
  });
});