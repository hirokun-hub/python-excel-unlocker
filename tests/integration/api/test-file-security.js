/**
 * ファイル安全性チェック機能の統合テスト
 * 
 * 基本的なマルウェア対策機能のテストを実装
 */

const fs = require('fs');
const path = require('path');
const axios = require('axios');

// テスト設定
const API_BASE_URL = process.env.API_BASE_URL || 'http://localhost:3001';
const TEST_USER_EMAIL = process.env.TEST_USER_EMAIL || 'test@example.com';

// テスト用ファイルの作成
function createTestFile(filename, content, magicBytes = null) {
    const filePath = path.join(__dirname, '..', 'fixtures', filename);
    
    // ディレクトリが存在しない場合は作成
    const dir = path.dirname(filePath);
    if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
    }
    
    let fileContent = content;
    if (magicBytes) {
        fileContent = Buffer.concat([magicBytes, Buffer.from(content)]);
    }
    
    fs.writeFileSync(filePath, fileContent);
    return filePath;
}

// テスト用ファイルのクリーンアップ
function cleanupTestFile(filePath) {
    if (fs.existsSync(filePath)) {
        fs.unlinkSync(filePath);
    }
}

// APIリクエストヘルパー
async function makeApiRequest(endpoint, data, headers = {}) {
    const defaultHeaders = {
        'Content-Type': 'application/json',
        'X-User-Email': TEST_USER_EMAIL,
        ...headers
    };
    
    try {
        const response = await axios.post(`${API_BASE_URL}${endpoint}`, data, {
            headers: defaultHeaders,
            timeout: 30000
        });
        return response.data;
    } catch (error) {
        if (error.response) {
            return error.response.data;
        }
        throw error;
    }
}

// Jest環境でない場合のフォールバック
if (typeof describe === 'undefined') {
    global.describe = (name, fn) => {
        console.log(`\n=== ${name} ===`);
        fn();
    };
    global.test = (name, fn) => {
        console.log(`  ✓ ${name}`);
        return fn();
    };
    global.expect = (actual) => ({
        toBe: (expected) => {
            if (actual !== expected) {
                throw new Error(`Expected ${expected}, got ${actual}`);
            }
        },
        toContain: (expected) => {
            if (!actual.includes(expected)) {
                throw new Error(`Expected "${actual}" to contain "${expected}"`);
            }
        },
        toBeDefined: () => {
            if (actual === undefined) {
                throw new Error(`Expected value to be defined`);
            }
        },
        toHaveLength: (expected) => {
            if (actual.length !== expected) {
                throw new Error(`Expected length ${expected}, got ${actual.length}`);
            }
        },
        toBeGreaterThan: (expected) => {
            if (actual <= expected) {
                throw new Error(`Expected ${actual} to be greater than ${expected}`);
            }
        },
        toBeLessThan: (expected) => {
            if (actual >= expected) {
                throw new Error(`Expected ${actual} to be less than ${expected}`);
            }
        }
    });
}

describe('ファイル安全性チェック統合テスト', () => {
    
    describe('署名付きURL生成時のセキュリティチェック', () => {
        
        test('正常なExcelファイル（.xlsx）のアップロードURL生成', async () => {
            const requestData = {
                fileName: 'test.xlsx',
                fileSize: 1024,
                contentType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            };
            
            const response = await makeApiRequest('/presigned-urls', requestData);
            
            expect(response.success).toBe(true);
            expect(response.data.uploadUrl).toBeDefined();
            expect(response.data.fileKey).toBeDefined();
            expect(response.data.expiresIn).toBe(60);
        });
        
        test('正常なExcelファイル（.xls）のアップロードURL生成', async () => {
            const requestData = {
                fileName: 'test.xls',
                fileSize: 1024,
                contentType: 'application/vnd.ms-excel'
            };
            
            const response = await makeApiRequest('/presigned-urls', requestData);
            
            expect(response.success).toBe(true);
            expect(response.data.uploadUrl).toBeDefined();
        });
        
        test('マクロ付きExcelファイル（.xlsm）の拒否', async () => {
            const requestData = {
                fileName: 'macro_file.xlsm',
                fileSize: 1024,
                contentType: 'application/vnd.ms-excel.sheet.macroEnabled.12'
            };
            
            const response = await makeApiRequest('/presigned-urls', requestData);
            
            expect(response.success).toBe(false);
            expect(response.error.code).toBe('macro_file_rejected');
            expect(response.error.message).toContain('マクロ付き');
        });
        
        test('危険なファイル形式（.exe）の拒否', async () => {
            const requestData = {
                fileName: 'malware.exe',
                fileSize: 1024,
                contentType: 'application/octet-stream'
            };
            
            const response = await makeApiRequest('/presigned-urls', requestData);
            
            expect(response.success).toBe(false);
            expect(response.error.code).toBe('dangerous_file_type');
            expect(response.error.message).toContain('危険なファイル形式');
        });
        
        test('サポートされていないファイル形式（.pdf）の拒否', async () => {
            const requestData = {
                fileName: 'document.pdf',
                fileSize: 1024,
                contentType: 'application/pdf'
            };
            
            const response = await makeApiRequest('/presigned-urls', requestData);
            
            expect(response.success).toBe(false);
            expect(response.error.code).toBe('unsupported_format');
            expect(response.error.message).toContain('サポートされていない');
        });
        
        test('ファイルサイズ上限超過の拒否', async () => {
            const requestData = {
                fileName: 'large_file.xlsx',
                fileSize: 25 * 1024 * 1024, // 25MB（制限は20MB）
                contentType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            };
            
            const response = await makeApiRequest('/presigned-urls', requestData);
            
            expect(response.success).toBe(false);
            expect(response.error.code).toBe('file_too_large');
            expect(response.error.message).toContain('上限');
        });
        
        test('ファイルサイズ下限未満の拒否', async () => {
            const requestData = {
                fileName: 'tiny_file.xlsx',
                fileSize: 50, // 50バイト（最小は100バイト）
                contentType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            };
            
            const response = await makeApiRequest('/presigned-urls', requestData);
            
            expect(response.success).toBe(false);
            expect(response.error.code).toBe('file_too_small');
            expect(response.error.message).toContain('小さすぎます');
        });
        
        test('許可されていないMIMEタイプの拒否', async () => {
            const requestData = {
                fileName: 'test.xlsx',
                fileSize: 1024,
                contentType: 'application/pdf' // 不正なMIMEタイプ
            };
            
            const response = await makeApiRequest('/presigned-urls', requestData);
            
            expect(response.success).toBe(false);
            expect(response.error.code).toBe('invalid_mime_type');
            expect(response.error.message).toContain('許可されていない');
        });
    });
    
    describe('ファイル処理時のセキュリティチェック', () => {
        let testFiles = [];
        
        afterEach(() => {
            // テストファイルのクリーンアップ
            testFiles.forEach(filePath => {
                cleanupTestFile(filePath);
            });
            testFiles = [];
        });
        
        test('正常なExcelファイルの処理', async () => {
            // 最小限の有効なZIPファイル（.xlsx）を作成
            const JSZip = require('jszip');
            const zip = new JSZip();
            zip.file('[Content_Types].xml', '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>');
            zip.file('_rels/.rels', '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>');
            
            const zipBuffer = await zip.generateAsync({ type: 'nodebuffer' });
            const testFilePath = createTestFile('valid_test.xlsx', zipBuffer);
            testFiles.push(testFilePath);
            
            // ファイルをS3にアップロード（モック）
            // 実際のテストでは、S3アップロード処理をモックまたは実際に実行
            
            const requestData = {
                files: [{
                    s3_key: 'uploads/test-key',
                    original_name: 'valid_test.xlsx'
                }],
                passwords: ['password123']
            };
            
            const response = await makeApiRequest('/unlock', requestData);
            
            // セキュリティチェックが通過することを確認
            // 実際の解除処理は別のテストで検証
            expect(response.success).toBeDefined();
        });
        
        test('マクロ付きファイルの処理拒否', async () => {
            // マクロ付きファイルのシミュレーション
            const JSZip = require('jszip');
            const zip = new JSZip();
            zip.file('[Content_Types].xml', '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>');
            zip.file('_rels/.rels', '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>');
            zip.file('xl/vbaProject.bin', 'macro content'); // マクロファイル
            
            const zipBuffer = await zip.generateAsync({ type: 'nodebuffer' });
            const testFilePath = createTestFile('macro_test.xlsx', zipBuffer);
            testFiles.push(testFilePath);
            
            const requestData = {
                files: [{
                    s3_key: 'uploads/macro-test-key',
                    original_name: 'macro_test.xlsx'
                }],
                passwords: ['password123']
            };
            
            const response = await makeApiRequest('/unlock', requestData);
            
            expect(response.success).toBe(true); // APIは成功するが、個別ファイルでエラー
            expect(response.data.results[0].status).toBe('error');
            expect(response.data.results[0].message).toContain('マクロ');
        });
        
        test('実行ファイルの処理拒否', async () => {
            // Windows実行ファイルのマジックバイト
            const executableContent = Buffer.from('MZ' + 'x'.repeat(1000));
            const testFilePath = createTestFile('malware.exe', executableContent);
            testFiles.push(testFilePath);
            
            const requestData = {
                files: [{
                    s3_key: 'uploads/malware-test-key',
                    original_name: 'malware.exe'
                }],
                passwords: ['password123']
            };
            
            const response = await makeApiRequest('/unlock', requestData);
            
            expect(response.success).toBe(true); // APIは成功するが、個別ファイルでエラー
            expect(response.data.results[0].status).toBe('error');
            expect(response.data.results[0].message).toContain('実行ファイル');
        });
        
        test('破損したファイルの処理拒否', async () => {
            // 無効なマジックバイトを持つファイル
            const corruptedContent = Buffer.from('INVALID' + 'x'.repeat(1000));
            const testFilePath = createTestFile('corrupted.xlsx', corruptedContent);
            testFiles.push(testFilePath);
            
            const requestData = {
                files: [{
                    s3_key: 'uploads/corrupted-test-key',
                    original_name: 'corrupted.xlsx'
                }],
                passwords: ['password123']
            };
            
            const response = await makeApiRequest('/unlock', requestData);
            
            expect(response.success).toBe(true); // APIは成功するが、個別ファイルでエラー
            expect(response.data.results[0].status).toBe('error');
            expect(response.data.results[0].message).toContain('認識できません');
        });
    });
    
    describe('S3アップロード条件拘束テスト', () => {
        
        test('署名付きURLの条件拘束確認', async () => {
            const requestData = {
                fileName: 'test.xlsx',
                fileSize: 1024,
                contentType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            };
            
            const response = await makeApiRequest('/presigned-urls', requestData);
            
            expect(response.success).toBe(true);
            expect(response.data.uploadFields).toBeDefined();
            
            // 条件拘束の確認
            const fields = response.data.uploadFields;
            expect(fields['Content-Type']).toBe(requestData.contentType);
            expect(fields['x-amz-server-side-encryption']).toBe('AES256');
            
            // POSTメソッドの指定確認
            expect(response.data.method).toBe('POST');
        });
    });
    
    describe('エラーハンドリングテスト', () => {
        
        test('認証失敗時のエラー', async () => {
            const requestData = {
                fileName: 'test.xlsx',
                fileSize: 1024,
                contentType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            };
            
            const response = await makeApiRequest('/presigned-urls', requestData, {
                'X-User-Email': '' // 空の認証情報
            });
            
            expect(response.success).toBe(false);
            expect(response.error.code).toBe('authentication_failed');
        });
        
        test('必須パラメータ不足時のエラー', async () => {
            const requestData = {
                // fileName が不足
                fileSize: 1024,
                contentType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            };
            
            const response = await makeApiRequest('/presigned-urls', requestData);
            
            expect(response.success).toBe(false);
            expect(response.error.code).toBe('missing_filename');
        });
        
        test('不正なJSONリクエスト時のエラー', async () => {
            try {
                const response = await axios.post(`${API_BASE_URL}/presigned-urls`, 'invalid json', {
                    headers: {
                        'Content-Type': 'application/json',
                        'X-User-Email': TEST_USER_EMAIL
                    },
                    timeout: 30000
                });
            } catch (error) {
                expect(error.response.status).toBe(400);
                expect(error.response.data.error.code).toBe('invalid_json');
            }
        });
    });
    
    describe('パフォーマンステスト', () => {
        
        test('セキュリティチェックの応答時間', async () => {
            const startTime = Date.now();
            
            const requestData = {
                fileName: 'performance_test.xlsx',
                fileSize: 1024,
                contentType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            };
            
            const response = await makeApiRequest('/presigned-urls', requestData);
            
            const responseTime = Date.now() - startTime;
            
            expect(response.success).toBe(true);
            expect(responseTime).toBeLessThan(5000); // 5秒以内
        });
        
        test('複数ファイルのセキュリティチェック', async () => {
            const files = Array.from({ length: 5 }, (_, i) => ({
                fileName: `test_${i}.xlsx`,
                fileSize: 1024,
                contentType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            }));
            
            const startTime = Date.now();
            
            const promises = files.map(file => makeApiRequest('/presigned-urls', file));
            const responses = await Promise.all(promises);
            
            const responseTime = Date.now() - startTime;
            
            responses.forEach(response => {
                expect(response.success).toBe(true);
            });
            
            expect(responseTime).toBeLessThan(10000); // 10秒以内
        });
    });
});

module.exports = {
    createTestFile,
    cleanupTestFile,
    makeApiRequest
};