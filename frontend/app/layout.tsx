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
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=DM+Mono:wght@400;500&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>{children}</body>
    </html>
  )
}
