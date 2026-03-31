import type { Metadata } from 'next'
import { Syne, Inter } from 'next/font/google'
import { AuthProvider } from '@/lib/AuthContext'
import './globals.css'

const syne = Syne({ subsets: ['latin'], weight: ['700', '800'], variable: '--font-syne' })
const inter = Inter({ subsets: ['latin'], weight: ['400', '600'], variable: '--font-inter' })

export const metadata: Metadata = {
  title: 'AITT — Behavioral Interview Coach',
  description: 'AI-powered behavioral interview coaching with real-time voice feedback.',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${syne.variable} ${inter.variable}`}>
      <body><AuthProvider>{children}</AuthProvider></body>
    </html>
  )
}
