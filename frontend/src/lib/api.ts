/**
 * バックエンドAPI呼び出し用のユーティリティ関数
 */
import { getSession } from "next-auth/react"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3001'

/**
 * 認証ヘッダー付きでAPIを呼び出す共通関数
 * JWT認証: Authorization Bearerヘッダーを使用
 */
async function apiCall(endpoint: string, options: RequestInit = {}) {
  const session = await getSession()
  
  if (!session?.user?.email) {
    throw new Error('認証が必要です。ログインしてください。')
  }

  // JWT認証: ID Tokenを使用
  const idToken = (session as any).idToken
  if (!idToken) {
    throw new Error('認証トークンが見つかりません。再ログインしてください。')
  }

  const headers = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${idToken}`, // JWT認証ヘッダー
    ...options.headers,
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    
    // 認証エラーの場合は特別な処理
    if (response.status === 401 || response.status === 403) {
      throw new Error('認証に失敗しました。再ログインしてください。')
    }
    
    throw new Error(errorData.message || `API呼び出しエラー: ${response.status}`)
  }

  const data = await response.json()
  
  // レスポンスバリデーション
  if (typeof data !== 'object' || data === null) {
    throw new Error('不正なAPIレスポンス形式です')
  }

  return data
}

/**
 * 署名付きアップロードURL取得
 */
export async function getUploadUrl(fileName: string, fileSize: number, contentType: string) {
  const data = await apiCall('/presigned-urls', {
    method: 'POST',
    body: JSON.stringify({
      fileName,
      fileSize,
      contentType,
    }),
  })

  // レスポンス形式のバリデーション
  if (!data.success || !data.uploadUrl || !data.fileKey) {
    throw new Error('署名付きURL取得レスポンスの形式が不正です')
  }

  return data
}

/**
 * Excel解除処理
 */
export async function unlockExcel(fileKey: string, passwords: string[]) {
  const data = await apiCall('/unlock', {
    method: 'POST',
    body: JSON.stringify({
      fileKey,
      passwords,
    }),
  })

  // レスポンス形式のバリデーション
  if (typeof data.success !== 'boolean') {
    throw new Error('Excel解除レスポンスの形式が不正です')
  }

  return data
}

/**
 * ファイルをS3にアップロード
 */
export async function uploadFileToS3(uploadUrl: string, file: File) {
  const response = await fetch(uploadUrl, {
    method: 'PUT',
    body: file,
    headers: {
      'Content-Type': file.type,
    },
  })

  if (!response.ok) {
    throw new Error(`ファイルアップロードエラー: ${response.status}`)
  }

  return response
}