/**
 * Excel解除機能のメインコンポーネント
 */
"use client"

import { useState } from "react"
import { useSession } from "next-auth/react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Progress } from "@/components/ui/progress"
import { getUploadUrl, uploadFileToS3, unlockExcel } from "@/lib/api"
import { toast } from "sonner"

interface ProcessingStatus {
  status: 'idle' | 'uploading' | 'processing' | 'completed' | 'error'
  progress: number
  message: string
  downloadUrl?: string
  fileName?: string
}

export default function ExcelUnlocker() {
  const { data: session } = useSession()
  const [file, setFile] = useState<File | null>(null)
  const [passwords, setPasswords] = useState<string[]>(['', ''])
  const [processing, setProcessing] = useState<ProcessingStatus>({
    status: 'idle',
    progress: 0,
    message: ''
  })

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile) {
      // Excelファイルかチェック
      const validTypes = [
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/vnd.ms-excel'
      ]
      
      if (!validTypes.includes(selectedFile.type)) {
        toast.error('Excelファイル（.xlsx または .xls）を選択してください')
        return
      }
      
      setFile(selectedFile)
      setProcessing({ status: 'idle', progress: 0, message: '' })
    }
  }

  const handlePasswordChange = (index: number, value: string) => {
    const newPasswords = [...passwords]
    newPasswords[index] = value
    setPasswords(newPasswords)
  }

  const handleUnlock = async () => {
    if (!file || !session?.user?.email) {
      toast.error('ファイルを選択してログインしてください')
      return
    }

    const validPasswords = passwords.filter(p => p.trim())
    if (validPasswords.length === 0) {
      toast.error('少なくとも1つのパスワードを入力してください')
      return
    }

    try {
      // 1. 署名付きURL取得
      setProcessing({
        status: 'uploading',
        progress: 10,
        message: 'アップロード準備中...'
      })

      const uploadResponse = await getUploadUrl(
        file.name,
        file.size,
        file.type
      )

      // 2. ファイルアップロード
      setProcessing({
        status: 'uploading',
        progress: 30,
        message: 'ファイルアップロード中...'
      })

      await uploadFileToS3(uploadResponse.uploadUrl, file)

      // 3. Excel解除処理
      setProcessing({
        status: 'processing',
        progress: 60,
        message: 'パスワード解除処理中...'
      })

      const unlockResponse = await unlockExcel(
        uploadResponse.fileKey,
        validPasswords
      )

      if (unlockResponse.success) {
        setProcessing({
          status: 'completed',
          progress: 100,
          message: '解除完了！',
          downloadUrl: unlockResponse.downloadUrl,
          fileName: unlockResponse.fileName
        })
        toast.success('Excelファイルの解除が完了しました')
      } else {
        throw new Error(unlockResponse.message || '解除に失敗しました')
      }

    } catch (error) {
      console.error('Excel unlock error:', error)
      
      let errorMessage = '予期しないエラーが発生しました'
      
      if (error instanceof Error) {
        errorMessage = error.message
        
        // JWT認証エラーの場合は特別な処理
        if (errorMessage.includes('認証に失敗しました') || errorMessage.includes('認証が必要です')) {
          toast.error('認証エラーが発生しました。ページを更新して再ログインしてください。')
          // 必要に応じて自動的にログアウト処理を実行
          // signOut()
        } else {
          toast.error('解除処理に失敗しました')
        }
      }
      
      setProcessing({
        status: 'error',
        progress: 0,
        message: errorMessage
      })
    }
  }

  const handleDownload = () => {
    if (processing.downloadUrl) {
      const link = document.createElement('a')
      link.href = processing.downloadUrl
      link.download = processing.fileName || 'unlocked-file.xlsx'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    }
  }

  const resetForm = () => {
    setFile(null)
    setPasswords(['', ''])
    setProcessing({ status: 'idle', progress: 0, message: '' })
  }

  if (!session) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Excel解除ツール</CardTitle>
          <CardDescription>
            ログインが必要です
          </CardDescription>
        </CardHeader>
      </Card>
    )
  }

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle>Excel解除ツール</CardTitle>
        <CardDescription>
          パスワード付きExcelファイルを解除します
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* ファイル選択 */}
        <div className="space-y-2">
          <Label htmlFor="file">Excelファイル選択</Label>
          <Input
            id="file"
            type="file"
            accept=".xlsx,.xls"
            onChange={handleFileChange}
            disabled={processing.status === 'uploading' || processing.status === 'processing'}
          />
          {file && (
            <p className="text-sm text-muted-foreground">
              選択されたファイル: {file.name} ({Math.round(file.size / 1024)}KB)
            </p>
          )}
        </div>

        {/* パスワード入力 */}
        <div className="space-y-4">
          <Label>パスワード候補</Label>
          {passwords.map((password, index) => (
            <div key={index} className="space-y-2">
              <Label htmlFor={`password-${index}`}>
                パスワード {index + 1}
              </Label>
              <Input
                id={`password-${index}`}
                type="password"
                value={password}
                onChange={(e) => handlePasswordChange(index, e.target.value)}
                placeholder={`パスワード候補 ${index + 1}`}
                disabled={processing.status === 'uploading' || processing.status === 'processing'}
              />
            </div>
          ))}
        </div>

        {/* 処理状況 */}
        {processing.status !== 'idle' && (
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span>{processing.message}</span>
              <span>{processing.progress}%</span>
            </div>
            <Progress value={processing.progress} />
          </div>
        )}

        {/* エラー表示 */}
        {processing.status === 'error' && (
          <Alert variant="destructive">
            <AlertDescription>{processing.message}</AlertDescription>
          </Alert>
        )}

        {/* 成功時のダウンロード */}
        {processing.status === 'completed' && processing.downloadUrl && (
          <Alert>
            <AlertDescription>
              解除が完了しました！下のボタンからダウンロードできます。
            </AlertDescription>
          </Alert>
        )}

        {/* アクションボタン */}
        <div className="flex gap-2">
          {processing.status === 'completed' && processing.downloadUrl ? (
            <>
              <Button onClick={handleDownload} className="flex-1">
                解除済みファイルをダウンロード
              </Button>
              <Button variant="outline" onClick={resetForm}>
                新しいファイルを処理
              </Button>
            </>
          ) : (
            <Button
              onClick={handleUnlock}
              disabled={
                !file || 
                passwords.every(p => !p.trim()) || 
                processing.status === 'uploading' || 
                processing.status === 'processing'
              }
              className="w-full"
            >
              {processing.status === 'uploading' || processing.status === 'processing'
                ? '処理中...'
                : 'Excel解除を開始'
              }
            </Button>
          )}
        </div>

        {/* ユーザー情報表示 */}
        <div className="text-sm text-muted-foreground">
          ログイン中: {session.user.email}
        </div>
      </CardContent>
    </Card>
  )
}