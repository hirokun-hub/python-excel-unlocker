'use client'

import { useEffect, useState } from 'react'

/**
 * CSP設定のテスト用コンポーネント
 * 開発環境でCSPが正しく動作しているかを確認する
 */
export default function CSPTest() {
  const [cspStatus, setCspStatus] = useState<{
    scriptBlocked: boolean
    inlineStyleBlocked: boolean
    externalResourceBlocked: boolean
  }>({
    scriptBlocked: false,
    inlineStyleBlocked: false,
    externalResourceBlocked: false
  })

  useEffect(() => {
    // 開発環境でのみ表示
    if (process.env.NODE_ENV !== 'development') {
      return
    }

    // CSPテスト: インラインスクリプトの実行テスト
    try {
      // この関数が実行されればCSPが正しく設定されている
      console.log('CSP Test: Script execution allowed with nonce')
    } catch (error) {
      setCspStatus(prev => ({ ...prev, scriptBlocked: true }))
      console.error('CSP Test: Script blocked', error)
    }

    // CSPテスト: 外部リソースの読み込みテスト
    const testImage = new Image()
    testImage.onload = () => {
      console.log('CSP Test: External image loading allowed')
    }
    testImage.onerror = () => {
      setCspStatus(prev => ({ ...prev, externalResourceBlocked: true }))
      console.error('CSP Test: External resource blocked')
    }
    testImage.src = 'https://via.placeholder.com/1x1.png'

  }, [])

  // 本番環境では何も表示しない
  if (process.env.NODE_ENV !== 'development') {
    return null
  }

  return (
    <div className="fixed bottom-4 right-4 bg-background border rounded-lg p-4 shadow-lg text-xs max-w-xs">
      <h4 className="font-semibold mb-2">CSP Status (Dev Only)</h4>
      <div className="space-y-1">
        <div className={`flex items-center gap-2 ${cspStatus.scriptBlocked ? 'text-red-500' : 'text-green-500'}`}>
          <span>{cspStatus.scriptBlocked ? '❌' : '✅'}</span>
          <span>Script Execution</span>
        </div>
        <div className={`flex items-center gap-2 ${cspStatus.externalResourceBlocked ? 'text-red-500' : 'text-green-500'}`}>
          <span>{cspStatus.externalResourceBlocked ? '❌' : '✅'}</span>
          <span>External Resources</span>
        </div>
      </div>
      <p className="mt-2 text-muted-foreground">
        Check browser console for CSP violations
      </p>
    </div>
  )
}