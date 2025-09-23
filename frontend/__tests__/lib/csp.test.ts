import { generateCSPPolicy, isDevelopment, getScriptProps, getNonce } from '@/lib/csp';
import { headers } from 'next/headers';

jest.mock('next/headers', () => ({
  headers: jest.fn(),
}));

// モック環境変数
const originalEnv = process.env.NODE_ENV;

describe('CSP Utilities', () => {
  afterEach(() => {
    // 環境変数を元に戻す
    Object.defineProperty(process.env, 'NODE_ENV', {
      value: originalEnv,
      writable: true,
      configurable: true
    });
    jest.clearAllMocks();
  });

  describe('generateCSPPolicy', () => {
    it('should generate CSP policy with nonce', () => {
      const nonce = 'test-nonce-123';
      const policy = generateCSPPolicy(nonce);
      
      expect(policy).toContain(`script-src 'self' 'nonce-${nonce}' 'strict-dynamic'`);
      expect(policy).toContain("default-src 'self'");
      expect(policy).toContain("object-src 'none'");
      expect(policy).toContain("frame-ancestors 'none'");
    });

    it('should include upgrade-insecure-requests in development', () => {
      Object.defineProperty(process.env, 'NODE_ENV', {
        value: 'development',
        writable: true,
        configurable: true
      });
      const nonce = 'test-nonce-123';
      const policy = generateCSPPolicy(nonce);
      
      expect(policy).toContain('upgrade-insecure-requests');
    });

    it('should not include upgrade-insecure-requests in production', () => {
      Object.defineProperty(process.env, 'NODE_ENV', {
        value: 'production',
        writable: true,
        configurable: true
      });
      const nonce = 'test-nonce-123';
      const policy = generateCSPPolicy(nonce);
      
      expect(policy).not.toContain('upgrade-insecure-requests');
    });
  });

  describe('isDevelopment', () => {
    it('should return true in development environment', () => {
      Object.defineProperty(process.env, 'NODE_ENV', {
        value: 'development',
        writable: true,
        configurable: true
      });
      expect(isDevelopment()).toBe(true);
    });

    it('should return false in production environment', () => {
      Object.defineProperty(process.env, 'NODE_ENV', {
        value: 'production',
        writable: true,
        configurable: true
      });
      expect(isDevelopment()).toBe(false);
    });
  });

  describe('getNonce', () => {
    it('ヘッダーからnonceを取得できる', async () => {
      (headers as jest.Mock).mockResolvedValue({
        get: jest.fn().mockReturnValue('header-nonce'),
      });

      await expect(getNonce()).resolves.toBe('header-nonce');
    });

    it('ヘッダー取得に失敗した場合はundefinedを返す', async () => {
      (headers as jest.Mock).mockRejectedValue(new Error('no headers'));

      await expect(getNonce()).resolves.toBeUndefined();
    });
  });

  describe('getScriptProps', () => {
    it('should return nonce prop when nonce is provided', () => {
      const nonce = 'test-nonce-123';
      const props = getScriptProps(nonce);
      
      expect(props).toEqual({ nonce });
    });

    it('should return empty object when nonce is not provided', () => {
      const props = getScriptProps();
      
      expect(props).toEqual({});
    });

    it('should return empty object when nonce is undefined', () => {
      const props = getScriptProps(undefined);
      
      expect(props).toEqual({});
    });
  });
});

describe('CSP Policy Content', () => {
  it('should allow necessary external domains', () => {
    const nonce = 'test-nonce';
    const policy = generateCSPPolicy(nonce);
    
    // Google OAuth and APIs
    expect(policy).toContain('https://accounts.google.com');
    expect(policy).toContain('https://www.googleapis.com');
    
    // AWS API Gateway
    expect(policy).toContain('https://*.execute-api.ap-northeast-1.amazonaws.com');
    
    // GitHub API
    expect(policy).toContain('https://api.github.com');
    
    // Google Fonts
    expect(policy).toContain('https://fonts.gstatic.com');
  });

  it('should have secure default policies', () => {
    const nonce = 'test-nonce';
    const policy = generateCSPPolicy(nonce);
    
    expect(policy).toContain("object-src 'none'");
    expect(policy).toContain("base-uri 'self'");
    expect(policy).toContain("form-action 'self'");
    expect(policy).toContain("frame-ancestors 'none'");
  });

  it('should allow inline styles for Tailwind CSS', () => {
    const nonce = 'test-nonce';
    const policy = generateCSPPolicy(nonce);
    
    expect(policy).toContain("style-src 'self' 'unsafe-inline'");
  });
});