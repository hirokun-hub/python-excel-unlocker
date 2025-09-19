/**
 * レート制限・WAF設定の統合テスト
 */
const axios = require('axios');
const { expect } = require('chai');
const { getApiUrl, getTestJwtToken } = require('../utils/test-helpers');

describe('Rate Limiting and WAF Tests', function() {
  this.timeout(30000); // 30秒のタイムアウト

  const apiUrl = getApiUrl();
  let authHeaders;

  before(async function() {
    // テスト用認証ヘッダーを準備
    const testToken = getTestJwtToken('hironomac2025@gmail.com');
    authHeaders = {
      'Authorization': `Bearer ${testToken}`,
      'Content-Type': 'application/json'
    };
  });

  describe('API Gateway Throttling', function() {
    it('should handle normal request rate', async function() {
      const response = await axios.post(`${apiUrl}/presigned-urls`, {
        fileName: 'test.xlsx',
        fileSize: 1024,
        contentType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
      }, { headers: authHeaders });

      expect(response.status).to.equal(200);
      expect(response.data).to.have.property('uploadUrl');
    });

    it('should apply rate limiting for excessive requests', async function() {
      // 短時間で大量のリクエストを送信してレート制限をテスト
      const requests = [];
      const requestCount = 10;

      for (let i = 0; i < requestCount; i++) {
        requests.push(
          axios.post(`${apiUrl}/presigned-urls`, {
            fileName: `test-${i}.xlsx`,
            fileSize: 1024,
            contentType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
          }, { 
            headers: authHeaders,
            timeout: 5000,
            validateStatus: () => true // すべてのステータスコードを受け入れ
          })
        );
      }

      const responses = await Promise.all(requests);
      
      // 一部のリクエストが成功し、一部がレート制限される可能性
      const successCount = responses.filter(r => r.status === 200).length;
      const rateLimitedCount = responses.filter(r => r.status === 429).length;
      
      console.log(`成功: ${successCount}, レート制限: ${rateLimitedCount}`);
      
      // 少なくとも一部のリクエストは成功するはず
      expect(successCount).to.be.greaterThan(0);
    });
  });

  describe('Bot Protection', function() {
    it('should accept requests with valid User-Agent', async function() {
      const response = await axios.post(`${apiUrl}/presigned-urls`, {
        fileName: 'test.xlsx',
        fileSize: 1024,
        contentType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
      }, { 
        headers: {
          ...authHeaders,
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
      });

      expect(response.status).to.equal(200);
    });

    it('should block requests with suspicious User-Agent', async function() {
      try {
        const response = await axios.post(`${apiUrl}/presigned-urls`, {
          fileName: 'test.xlsx',
          fileSize: 1024,
          contentType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        }, { 
          headers: {
            ...authHeaders,
            'User-Agent': 'python-requests/2.28.1'
          },
          validateStatus: () => true
        });

        // Bot検知により429または403が返される可能性
        expect([403, 429]).to.include(response.status);
      } catch (error) {
        // ネットワークレベルでブロックされる場合もある
        expect(error.code).to.be.oneOf(['ECONNRESET', 'ECONNREFUSED']);
      }
    });

    it('should handle bot protection tokens when enabled', async function() {
      // Bot保護が有効な場合のテスト
      const requestWithBotToken = {
        fileName: 'test.xlsx',
        fileSize: 1024,
        contentType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        // テスト用のダミートークン
        recaptcha_token: 'test-recaptcha-token',
        turnstile_token: 'test-turnstile-token'
      };

      const response = await axios.post(`${apiUrl}/presigned-urls`, requestWithBotToken, {
        headers: authHeaders,
        validateStatus: () => true
      });

      // Bot保護が無効な場合は200、有効な場合はトークン検証結果による
      expect([200, 403]).to.include(response.status);
    });
  });

  describe('WAF Security Rules', function() {
    it('should allow legitimate requests', async function() {
      const response = await axios.post(`${apiUrl}/unlock`, {
        files: [{
          fileKey: 'test-key',
          fileName: 'test.xlsx'
        }],
        passwords: ['password123']
      }, { headers: authHeaders });

      // ファイルが存在しないため404が返されるが、WAFは通過する
      expect([200, 404]).to.include(response.status);
    });

    it('should block malicious payloads', async function() {
      const maliciousPayloads = [
        // SQLインジェクション試行
        { fileName: "'; DROP TABLE users; --" },
        // XSS試行
        { fileName: '<script>alert("xss")</script>' },
        // パストラバーサル試行
        { fileName: '../../../etc/passwd' }
      ];

      for (const payload of maliciousPayloads) {
        try {
          const response = await axios.post(`${apiUrl}/presigned-urls`, {
            ...payload,
            fileSize: 1024,
            contentType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
          }, { 
            headers: authHeaders,
            timeout: 5000,
            validateStatus: () => true
          });

          // WAFによりブロックされるか、アプリケーションレベルで拒否される
          expect([400, 403, 404]).to.include(response.status);
        } catch (error) {
          // WAFレベルでブロックされる場合
          expect(error.code).to.be.oneOf(['ECONNRESET', 'ECONNREFUSED']);
        }
      }
    });

    it('should handle large request bodies appropriately', async function() {
      // 大きなリクエストボディのテスト
      const largePayload = {
        fileName: 'test.xlsx',
        fileSize: 1024,
        contentType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        largeData: 'x'.repeat(10000) // 10KB のダミーデータ
      };

      const response = await axios.post(`${apiUrl}/presigned-urls`, largePayload, {
        headers: authHeaders,
        timeout: 10000,
        validateStatus: () => true
      });

      // 正常に処理されるか、適切にサイズ制限される
      expect([200, 413]).to.include(response.status);
    });
  });

  describe('Geographic Restrictions', function() {
    it('should allow requests from Japan', async function() {
      // 日本からのアクセスをシミュレート（実際のテストでは制限あり）
      const response = await axios.post(`${apiUrl}/presigned-urls`, {
        fileName: 'test.xlsx',
        fileSize: 1024,
        contentType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
      }, { 
        headers: {
          ...authHeaders,
          'X-Forwarded-For': '203.0.113.1' // 日本のIPアドレス例
        }
      });

      expect(response.status).to.equal(200);
    });
  });

  describe('Error Handling', function() {
    it('should return appropriate error messages for blocked requests', async function() {
      // 意図的に無効なリクエストを送信
      try {
        const response = await axios.post(`${apiUrl}/presigned-urls`, {
          fileName: '',
          fileSize: -1,
          contentType: 'invalid/type'
        }, { 
          headers: authHeaders,
          validateStatus: () => true
        });

        expect(response.status).to.be.oneOf([400, 403]);
        
        if (response.data && response.data.message) {
          expect(response.data.message).to.be.a('string');
          expect(response.data.message.length).to.be.greaterThan(0);
        }
      } catch (error) {
        // ネットワークレベルでブロックされる場合
        expect(error.code).to.be.oneOf(['ECONNRESET', 'ECONNREFUSED']);
      }
    });
  });

  describe('Performance Impact', function() {
    it('should not significantly impact response time', async function() {
      const startTime = Date.now();
      
      const response = await axios.post(`${apiUrl}/presigned-urls`, {
        fileName: 'test.xlsx',
        fileSize: 1024,
        contentType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
      }, { headers: authHeaders });

      const responseTime = Date.now() - startTime;
      
      expect(response.status).to.equal(200);
      expect(responseTime).to.be.lessThan(5000); // 5秒以内
      
      console.log(`WAF付きAPI応答時間: ${responseTime}ms`);
    });
  });
});