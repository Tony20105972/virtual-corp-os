import type { Metadata } from "next"
import "./globals.css"

export const metadata: Metadata = {
  title: "Virtual Corp OS",
  description: "AI-powered virtual corporation operating system",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  )
}
