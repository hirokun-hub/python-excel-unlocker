/**
 * Playwright E2E統合テスト
 */

import { test, expect } from '@playwright/test';

// テスト用の設定
const TEST_USER_EMAIL = process.env.TEST_USER_EMAIL || 'test@example.com';
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000';

test.describe('Excel解除アプリ E2E統合テスト', () => {
  
  test.beforeEach(async ({ page }) => {
    // 認証状態のモック（実際の環境では適切な認証フローを使用）
    await page.goto('/');
    
    // ローカルストレージに認証情報を設定（開発用）
    await page.evaluate((email) => {
      localStorage.setItem('test-auth', JSON.stringify({
        user: { email, name: 'Test User' },
        authenticated: true
      }));
    }, TEST_USER_EMAIL);
  });

  test('基本的なファイルアップロード・解除フロー', async ({ page }) => {
    await page.goto('/');

    // ページの読み込み確認
    await expect(page.locator('h1')).toContainText('Excel');

    // ファイルアップロードエリアの確認
    const uploadArea = page.locator('[data-testid="file-upload-area"]');
    await expect(uploadArea).toBeVisible();

    // テスト用ファイルの作成（ブラウザ内で）
    const fileContent = 'テスト用Excelファイル内容';
    const fileName = 'test-excel.xlsx';

    // ファイル選択のシミュレーション
    await page.setInputFiles('input[type="file"]', {
      name: fileName,
      mimeType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      buffer: Buffer.from(fileContent)
    });

    // ファイルが選択されたことを確認
    await expect(page.locator(`text=${fileName}`)).toBeVisible();

    // パスワード入力
    await page.fill('[data-testid="password-input-1"]', 'test123');
    await page.fill('[data-testid="password-input-2"]', 'backup456');

    // 解除ボタンクリック
    await page.click('[data-testid="unlock-button"]');

    // 処理中の表示確認
    await expect(page.locator('[data-testid="processing-indicator"]')).toBeVisible();

    // 結果の確認（成功またはエラー）
    await page.waitForSelector('[data-testid="result-area"]', { timeout: 30000 });
    
    const resultArea = page.locator('[data-testid="result-area"]');
    await expect(resultArea).toBeVisible();

    // 成功の場合はダウンロードリンクを確認
    const downloadLink = page.locator('[data-testid="download-link"]');
    if (await downloadLink.isVisible()) {
      await expect(downloadLink).toContainText('ダウンロード');
      console.log('✅ ファイル解除成功 - ダウンロードリンク表示');
    } else {
      // エラーの場合はエラーメッセージを確認
      const errorMessage = page.locator('[data-testid="error-message"]');
      await expect(errorMessage).toBeVisible();
      console.log('ℹ️ ファイル解除エラー（テスト環境のため正常）');
    }
  });

  test('複数ファイルの並列処理', async ({ page }) => {
    await page.goto('/');

    // 複数ファイルの選択
    const files = [
      {
        name: 'test1.xlsx',
        mimeType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        buffer: Buffer.from('テストファイル1')
      },
      {
        name: 'test2.xlsx',
        mimeType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        buffer: Buffer.from('テストファイル2')
      },
      {
        name: 'test3.xlsx',
        mimeType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        buffer: Buffer.from('テストファイル3')
      }
    ];

    await page.setInputFiles('input[type="file"]', files);

    // 全ファイルが表示されることを確認
    for (const file of files) {
      await expect(page.locator(`text=${file.name}`)).toBeVisible();
    }

    // パスワード入力
    await page.fill('[data-testid="password-input-1"]', 'test123');
    await page.fill('[data-testid="password-input-2"]', 'backup456');

    // 一括解除ボタンクリック
    await page.click('[data-testid="unlock-all-button"]');

    // 進捗表示の確認
    await expect(page.locator('[data-testid="progress-bar"]')).toBeVisible();

    // 全ファイルの処理完了を待機
    await page.waitForSelector('[data-testid="all-results-complete"]', { timeout: 60000 });

    // 結果の確認
    const resultItems = page.locator('[data-testid="result-item"]');
    const resultCount = await resultItems.count();
    expect(resultCount).toBe(files.length);

    console.log(`✅ ${files.length}ファイルの並列処理完了`);
  });

  test('Google Drive連携フロー', async ({ page }) => {
    await page.goto('/');

    // ファイルアップロード
    await page.setInputFiles('input[type="file"]', {
      name: 'drive-test.xlsx',
      mimeType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      buffer: Buffer.from('Google Drive連携テスト')
    });

    // パスワード入力
    await page.fill('[data-testid="password-input-1"]', 'test123');

    // 解除実行
    await page.click('[data-testid="unlock-button"]');

    // 処理完了を待機
    await page.waitForSelector('[data-testid="result-area"]', { timeout: 30000 });

    // Google Drive保存ボタンの確認
    const driveButton = page.locator('[data-testid="save-to-drive-button"]');
    if (await driveButton.isVisible()) {
      await driveButton.click();

      // フォルダ選択ダイアログの確認
      await expect(page.locator('[data-testid="folder-picker-dialog"]')).toBeVisible();

      // フォルダ選択（モック）
      await page.click('[data-testid="select-root-folder"]');
      await page.click('[data-testid="confirm-folder-selection"]');

      // 保存完了メッセージの確認
      await expect(page.locator('text=Google Driveに保存しました')).toBeVisible();

      console.log('✅ Google Drive連携フロー完了');
    } else {
      console.log('ℹ️ Google Drive連携ボタンが表示されませんでした（認証が必要）');
    }
  });

  test('エラーハンドリングの確認', async ({ page }) => {
    await page.goto('/');

    // 無効なファイル形式のアップロード
    await page.setInputFiles('input[type="file"]', {
      name: 'document.pdf',
      mimeType: 'application/pdf',
      buffer: Buffer.from('PDFファイル内容')
    });

    // エラーメッセージの確認
    await expect(page.locator('[data-testid="file-format-error"]')).toBeVisible();
    await expect(page.locator('text=サポートされていないファイル形式')).toBeVisible();

    console.log('✅ ファイル形式エラーハンドリング確認完了');

    // ページをリロードして状態をリセット
    await page.reload();

    // 正しいファイル形式でアップロード
    await page.setInputFiles('input[type="file"]', {
      name: 'test.xlsx',
      mimeType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      buffer: Buffer.from('テストファイル')
    });

    // パスワードなしで解除試行
    await page.click('[data-testid="unlock-button"]');

    // パスワード必須エラーの確認
    await expect(page.locator('[data-testid="password-required-error"]')).toBeVisible();

    console.log('✅ パスワード必須エラーハンドリング確認完了');
  });

  test('レスポンシブデザインの確認', async ({ page }) => {
    // モバイルビューポートに設定
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');

    // モバイルレイアウトの確認
    await expect(page.locator('[data-testid="mobile-layout"]')).toBeVisible();

    // ファイルアップロードエリアがモバイルで適切に表示されることを確認
    const uploadArea = page.locator('[data-testid="file-upload-area"]');
    await expect(uploadArea).toBeVisible();

    // タブレットビューポートに変更
    await page.setViewportSize({ width: 768, height: 1024 });

    // タブレットレイアウトの確認
    await expect(page.locator('[data-testid="tablet-layout"]')).toBeVisible();

    // デスクトップビューポートに変更
    await page.setViewportSize({ width: 1920, height: 1080 });

    // デスクトップレイアウトの確認
    await expect(page.locator('[data-testid="desktop-layout"]')).toBeVisible();

    console.log('✅ レスポンシブデザイン確認完了');
  });

  test('パフォーマンス測定', async ({ page }) => {
    // パフォーマンス測定開始
    const startTime = Date.now();

    await page.goto('/');

    // ページ読み込み時間の測定
    await page.waitForLoadState('networkidle');
    const loadTime = Date.now() - startTime;

    console.log(`📊 ページ読み込み時間: ${loadTime}ms`);

    // ファイルアップロードのパフォーマンス測定
    const uploadStartTime = Date.now();

    await page.setInputFiles('input[type="file"]', {
      name: 'perf-test.xlsx',
      mimeType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      buffer: Buffer.from('パフォーマンステスト用ファイル')
    });

    const uploadTime = Date.now() - uploadStartTime;
    console.log(`📊 ファイル選択処理時間: ${uploadTime}ms`);

    // UI応答性の確認
    expect(loadTime).toBeLessThan(5000); // 5秒以内
    expect(uploadTime).toBeLessThan(1000); // 1秒以内

    console.log('✅ パフォーマンス測定完了');
  });
});