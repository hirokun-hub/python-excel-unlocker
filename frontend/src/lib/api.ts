/**
 * バックエンドAPI呼び出し用のユーティリティ関数
 */
import { getSession } from "next-auth/react"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3001'

/**
 * 認証ヘッダー付きでAPIを呼び出す共通関数
 */
async function apiCall(endpoint: string, options: RequestInit = {}) {
  const session = await getSession()
  
  if (!session?.user?.email) {
    throw new Error('認証が必要です。ログインしてください。')
  }

  const headers = {
    'Content-Type': 'application/json',
    'X-User-Email': session.user.email, // バックエンドが期待するヘッダー
    ...options.headers,
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    throw new Error(errorData.message || `API呼び出しエラー: ${response.status}`)
  }

  return response.json()
}

/**
 * 署名付きアップロードURL取得
 */
export async function getUploadUrl(fileName: string, fileSize: number, contentType: string) {
  return apiCall('/presigned-urls', {
    method: 'POST',
    body: JSON.stringify({
      fileName,
      fileSize,
      contentType,
    }),
  })
}

/**
 * Excel解除処理
 */
export async function unlockExcel(fileKey: string, passwords: string[]) {
  return apiCall('/unlock', {
    method: 'POST',
    body: JSON.stringify({
      fileKey,
      passwords,
    }),
  })
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