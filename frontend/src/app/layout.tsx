import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import AuthProvider from "@/components/AuthProvider";
import { getNonce } from "@/lib/csp";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Secure Excel Unlock",
  description: "Unlock password-protected Excel files easily and securely.",
};

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const nonce = await getNonce();

  return (
    <html lang="ja">
      <head>
        {/* CSP meta tag for additional security */}
        <meta
          httpEquiv="Content-Security-Policy"
          content={`default-src 'self'; script-src 'self' ${nonce ? `'nonce-${nonce}'` : "'unsafe-inline'"} 'strict-dynamic'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' https://fonts.gstatic.com; connect-src 'self' https://api.github.com https://*.execute-api.ap-northeast-1.amazonaws.com https://accounts.google.com https://www.googleapis.com; frame-src 'self' https://accounts.google.com; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none';`}
        />
      </head>
      <body className={inter.className}>
        <AuthProvider nonce={nonce}>{children}</AuthProvider>
      </body>
    </html>
  );
}
