/**
 * バックエンドAPI呼び出し用のユーティリティ関数
 */
import { getSession } from "next-auth/react"
import { getBotProtectionTokens, type BotProtectionToken } from "./botProtection"
import type { ProcessResult } from "@/types/process-result"

type SessionResult = Awaited<ReturnType<typeof getSession>>

type SessionWithIdToken = SessionResult extends infer T
  ? T extends null
    ? null
    : T & { idToken?: string }
  : never

function extractIdToken(session: SessionResult): string | null {
  if (!session) {
    return null
  }

  const candidate = (session as SessionWithIdToken)?.idToken
  return typeof candidate === "string" && candidate.length > 0 ? candidate : null
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3001'

/**
 * 認証ヘッダー付きでAPIを呼び出す共通関数
 * JWT認証: Authorization Bearerヘッダーを使用
 * Bot保護: reCAPTCHA/Turnstileトークンを自動付与
 */
async function apiCall(endpoint: string, options: RequestInit = {}) {
  const session = await getSession()

  if (!session?.user?.email) {
    throw new Error('認証が必要です。ログインしてください。')
  }

  // JWT認証: ID Tokenを使用
  const idToken = extractIdToken(session)
  if (!idToken) {
    throw new Error('認証トークンが見つかりません。再ログインしてください。')
  }

  // Bot保護トークンを取得
  let botProtectionTokens: BotProtectionToken = {}
  try {
    botProtectionTokens = await getBotProtectionTokens(endpoint.replace('/', '_'))
  } catch (error) {
    console.warn('Bot protection token generation failed:', error)
    // Bot保護トークンの取得に失敗してもAPIコールは続行
  }

  const headerObject: Record<string, string> = {}

  const originalHeaders = options.headers
  if (originalHeaders instanceof Headers) {
    originalHeaders.forEach((value, key) => {
      headerObject[key] = value
    })
  } else if (Array.isArray(originalHeaders)) {
    originalHeaders.forEach(([key, value]) => {
      if (typeof value === 'string') {
        headerObject[key] = value
      }
    })
  } else if (originalHeaders && typeof originalHeaders === 'object') {
    Object.entries(originalHeaders).forEach(([key, value]) => {
      if (typeof value === 'string') {
        headerObject[key] = value
      }
    })
  }

  headerObject['Content-Type'] = 'application/json'
  headerObject['Authorization'] = `Bearer ${idToken}`

  // リクエストボディにBot保護トークンを追加
  let body = options.body
  if (options.method === 'POST' && body) {
    try {
      const bodyData = typeof body === 'string' ? JSON.parse(body) : body
      const enhancedBody = {
        ...bodyData,
        ...botProtectionTokens, // Bot保護トークンを追加
      }
      body = JSON.stringify(enhancedBody)
    } catch (error) {
      console.warn('Failed to add bot protection tokens to request body:', error)
    }
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: headerObject,
    body,
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
 * ファイルをS3にアップロード（条件拘束付きPOST形式対応）
 */
export async function uploadFileToS3(uploadUrl: string, file: File, uploadFields?: Record<string, string>) {
  // 新しいPOST形式の場合
  if (uploadFields) {
    const formData = new FormData()
    
    // 署名付きPOSTのフィールドを追加
    Object.entries(uploadFields).forEach(([key, value]) => {
      formData.append(key, value)
    })
    
    // ファイルを最後に追加（S3の要件）
    formData.append('file', file)
    
    const response = await fetch(uploadUrl, {
      method: 'POST',
      body: formData,
      // Content-Typeヘッダーは自動設定（multipart/form-data）
    })

    if (!response.ok) {
      const errorText = await response.text().catch(() => 'Unknown error')
      throw new Error(`ファイルアップロードエラー (POST): ${response.status} - ${errorText}`)
    }

    return response
  }
  
  // 従来のPUT形式（後方互換性）
  const response = await fetch(uploadUrl, {
    method: 'PUT',
    body: file,
    headers: {
      'Content-Type': file.type,
    },
  })

  if (!response.ok) {
    throw new Error(`ファイルアップロードエラー (PUT): ${response.status}`)
  }

  return response
}

export type UnlockFilePayload = {
  s3_key: string
  original_name: string
}

type UnlockFilesResponse = {
  success: boolean
  results: ProcessResult[]
}

/**
 * 複数ファイルのExcel解除処理
 */
export async function unlockFiles(files: UnlockFilePayload[], passwords: string[]) {
  if (!Array.isArray(files) || files.length === 0) {
    throw new Error('解除するファイル情報がありません')
  }

  const data = await apiCall('/unlock', {
    method: 'POST',
    body: JSON.stringify({
      files,
      passwords,
    }),
  })

  if (typeof data.success !== 'boolean' || !Array.isArray(data.results)) {
    throw new Error('Excel解除レスポンスの形式が不正です')
  }

  return data as UnlockFilesResponse
}

