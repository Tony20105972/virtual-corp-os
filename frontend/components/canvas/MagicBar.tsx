"use client"

import { useState } from "react"
import { useInterviewStore } from "@/store/interviewStore"

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"

export default function MagicBar() {
  const [input, setInput] = useState("")
  const { status, setIdea, setQuestions, setStatus } = useInterviewStore()

  // 인터뷰 진행 중이면 숨김
  if (status !== "idle") return null

  const isURL = (v: string) =>
    v.startsWith("http://") || v.startsWith("https://")

  const handleSubmit = async () => {
    const trimmed = input.trim()
    if (!trimmed) return

    if (isURL(trimmed)) {
      // Day 22 URL 리버스엔지니어링 — 현재는 스텁
      alert("URL reverse-engineering is coming soon!")
      return
    }

    setIdea(trimmed)
    setStatus("loading")

    try {
      const res = await fetch(`${API_URL}/interview/questions`, {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({ idea: trimmed }),
      })
      const data = await res.json()
      setQuestions(data.questions)
    } catch (err) {
      console.error("[MagicBar] 질문 생성 실패:", err)
      setQuestions([
        "Who is your primary target customer?",
        "What core problem are you solving?",
        "What makes your solution unique?",
      ])
    }
  }

  return (
    <div style={{
      position:       "absolute",
      bottom:         24,
      left:           "50%",
      transform:      "translateX(-50%)",
      width:          "min(560px, calc(100vw - 48px))",
      zIndex:         20,
      background:     "rgba(15, 24, 41, 0.92)",
      backdropFilter: "blur(16px)",
      border:         "1px solid rgba(255,255,255,0.1)",
      borderRadius:   14,
      padding:        "14px 18px",
      display:        "flex",
      alignItems:     "center",
      gap:            12,
    }}>
      <span style={{ fontSize: 16, color: "var(--blue)" }}>⦿</span>
      <input
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
        placeholder="Describe your idea or paste a URL..."
        style={{
          flex:       1,
          background: "transparent",
          border:     "none",
          outline:    "none",
          color:      "#E2E8F0",
          fontSize:   14,
          fontFamily: "'Pretendard', sans-serif",
        }}
      />
      <button
        onClick={handleSubmit}
        style={{
          width:          32,
          height:         32,
          borderRadius:   8,
          background:     "var(--blue)",
          border:         "none",
          cursor:         "pointer",
          color:          "#fff",
          fontSize:       16,
          display:        "flex",
          alignItems:     "center",
          justifyContent: "center",
        }}
      >
        ↑
      </button>
    </div>
  )
}
