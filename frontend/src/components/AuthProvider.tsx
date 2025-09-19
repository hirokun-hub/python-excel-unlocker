'use client'

import { SessionProvider } from 'next-auth/react'

type Props = {
  children: React.ReactNode
  nonce?: string
}

export default function AuthProvider({ children, nonce }: Props) {
  return (
    <SessionProvider>
      {children}
      {/* CSP nonce for inline scripts if needed */}
      {nonce && (
        <script
          nonce={nonce}
          dangerouslySetInnerHTML={{
            __html: `
              // CSP nonce available for dynamic scripts
              window.__CSP_NONCE__ = '${nonce}';
            `,
          }}
        />
      )}
    </SessionProvider>
  )
}
