export type ProcessResult = {
  fileName: string
  status: 'success' | 'error'
  message?: string
  downloadUrl?: string
}
