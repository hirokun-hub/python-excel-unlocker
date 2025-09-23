/**
 * Bot保護機能のユーティリティ
 * reCAPTCHA v3 と Cloudflare Turnstile の統合
 */

export interface BotProtectionToken {
  recaptcha_token?: string;
  turnstile_token?: string;
}

export interface BotProtectionConfig {
  enabled: boolean;
  recaptchaSiteKey?: string;
  turnstileSiteKey?: string;
}

/**
 * Bot保護設定を取得する
 */
export function getBotProtectionConfig(): BotProtectionConfig {
  const recaptchaSiteKey = process.env.NEXT_PUBLIC_RECAPTCHA_SITE_KEY;
  const turnstileSiteKey = process.env.NEXT_PUBLIC_TURNSTILE_SITE_KEY;
  
  return {
    enabled: !!(recaptchaSiteKey || turnstileSiteKey),
    recaptchaSiteKey,
    turnstileSiteKey,
  };
}

/**
 * reCAPTCHA v3トークンを取得する
 */
export async function getRecaptchaToken(action: string = 'submit'): Promise<string | null> {
  const config = getBotProtectionConfig();
  
  if (!config.recaptchaSiteKey) {
    return null;
  }
  
  try {
    let grecaptcha = window.grecaptcha;

    // reCAPTCHA v3 スクリプトの動的読み込み
    if (!grecaptcha) {
      await loadRecaptchaScript(config.recaptchaSiteKey);
      grecaptcha = window.grecaptcha;
    }

    if (!grecaptcha) {
      console.warn('reCAPTCHA global is unavailable after script load');
      return null;
    }

    return await grecaptcha.execute(config.recaptchaSiteKey, { action });
  } catch (error) {
    console.warn('reCAPTCHA token generation failed:', error);
    return null;
  }
}

/**
 * Turnstileトークンを取得する
 */
export async function getTurnstileToken(): Promise<string | null> {
  const config = getBotProtectionConfig();
  
  if (!config.turnstileSiteKey) {
    return null;
  }
  
  const containerId = 'turnstile-container-' + Date.now();
  const container = document.createElement('div');
  container.id = containerId;
  container.style.display = 'none';
  document.body.appendChild(container);

  try {
    let turnstile = window.turnstile;

    // Turnstile スクリプトの動的読み込み
    if (!turnstile) {
      await loadTurnstileScript();
      turnstile = window.turnstile;
    }

    if (!turnstile) {
      document.body.removeChild(container);
      throw new Error('Turnstile global is unavailable after script load');
    }

    return await new Promise((resolve, reject) => {
      turnstile.render(container, {
        sitekey: config.turnstileSiteKey!,
        callback: (token: string) => {
          document.body.removeChild(container);
          resolve(token);
        },
        'error-callback': (error: any) => {
          document.body.removeChild(container);
          reject(error);
        },
      });
    });
  } catch (error) {
    if (document.body.contains(container)) {
      document.body.removeChild(container);
    }
    console.warn('Turnstile token generation failed:', error);
    return null;
  }
}

/**
 * Bot保護トークンを取得する（利用可能な方法を自動選択）
 */
export async function getBotProtectionTokens(action: string = 'submit'): Promise<BotProtectionToken> {
  const config = getBotProtectionConfig();
  
  if (!config.enabled) {
    return {};
  }
  
  const tokens: BotProtectionToken = {};
  
  // reCAPTCHA v3 トークンを取得
  if (config.recaptchaSiteKey) {
    try {
      const recaptchaToken = await getRecaptchaToken(action);
      if (recaptchaToken) {
        tokens.recaptcha_token = recaptchaToken;
      }
    } catch (error) {
      console.warn('Failed to get reCAPTCHA token:', error);
    }
  }
  
  // Turnstile トークンを取得
  if (config.turnstileSiteKey) {
    try {
      const turnstileToken = await getTurnstileToken();
      if (turnstileToken) {
        tokens.turnstile_token = turnstileToken;
      }
    } catch (error) {
      console.warn('Failed to get Turnstile token:', error);
    }
  }
  
  return tokens;
}

/**
 * reCAPTCHA v3 スクリプトを動的に読み込む
 */
function loadRecaptchaScript(siteKey: string): Promise<void> {
  return new Promise((resolve, reject) => {
    if (document.querySelector('script[src*="recaptcha"]')) {
      resolve();
      return;
    }
    
    const script = document.createElement('script');
    script.src = `https://www.google.com/recaptcha/api.js?render=${siteKey}`;
    script.async = true;
    script.defer = true;
    
    script.onload = () => {
      // reCAPTCHA の初期化を待つ
      const checkReady = () => {
        if (window.grecaptcha && window.grecaptcha.ready) {
          window.grecaptcha.ready(() => resolve());
        } else {
          setTimeout(checkReady, 100);
        }
      };
      checkReady();
    };
    
    script.onerror = () => reject(new Error('Failed to load reCAPTCHA script'));
    
    document.head.appendChild(script);
  });
}

/**
 * Turnstile スクリプトを動的に読み込む
 */
function loadTurnstileScript(): Promise<void> {
  return new Promise((resolve, reject) => {
    if (document.querySelector('script[src*="turnstile"]')) {
      resolve();
      return;
    }
    
    const script = document.createElement('script');
    script.src = 'https://challenges.cloudflare.com/turnstile/v0/api.js';
    script.async = true;
    script.defer = true;
    
    script.onload = () => {
      // Turnstile の初期化を待つ
      const checkReady = () => {
        if (window.turnstile) {
          resolve();
        } else {
          setTimeout(checkReady, 100);
        }
      };
      checkReady();
    };
    
    script.onerror = () => reject(new Error('Failed to load Turnstile script'));
    
    document.head.appendChild(script);
  });
}

// TypeScript型定義の拡張
declare global {
  interface Window {
    grecaptcha?: {
      ready: (callback: () => void) => void;
      execute: (siteKey: string, options: { action: string }) => Promise<string>;
    };
    turnstile?: {
      render: (container: HTMLElement | string, options: {
        sitekey: string;
        callback: (token: string) => void;
        'error-callback': (error: any) => void;
      }) => void;
    };
  }
}