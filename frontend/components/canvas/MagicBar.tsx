"use client"

import { useState } from "react"
import { useInterviewStore } from "@/store/interviewStore"
import { BOARDROOM_QUESTIONS } from "@/lib/strategy/questions"
import styles from "./boardroom.module.css"

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"

interface MagicBarProps {
  compact?: boolean
  className?: string
}

export default function MagicBar({
  compact = false,
  className,
}: MagicBarProps) {
  const [input, setInput] = useState("")
  const { status, setIdea, setQuestions, setStatus } = useInterviewStore()

  if (status !== "idle" && status !== "done") return null

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
      await fetch(`${API_URL}/interview/questions`, {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({ idea: trimmed }),
      })
    } catch (err) {
      console.error("[MagicBar] 질문 생성 실패:", err)
    }

    setQuestions(BOARDROOM_QUESTIONS.map((question) => question.prompt))
    setInput("")
  }

  return (
    <div
      className={className}
      style={{
        width: compact ? "min(520px, 100%)" : "min(720px, 100%)",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: compact ? 10 : 14,
          width: "100%",
          padding: compact ? "10px 12px" : "16px 18px",
          border: "1px solid rgba(255,255,255,0.1)",
          borderRadius: compact ? 18 : 24,
          background: compact ? "rgba(12, 18, 32, 0.82)" : "rgba(12, 18, 32, 0.9)",
          backdropFilter: "blur(16px)",
          boxShadow: compact
            ? "0 16px 32px rgba(0,0,0,0.18)"
            : "0 24px 50px rgba(0,0,0,0.24)",
          boxSizing: "border-box",
        }}
      >
        <span
          style={{
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            width: compact ? 28 : 36,
            height: compact ? 28 : 36,
            borderRadius: "50%",
            border: "1px solid rgba(96,165,250,0.35)",
            color: "var(--blue)",
            fontSize: compact ? 12 : 14,
            flexShrink: 0,
          }}
        >
          ⦿
        </span>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
          placeholder={compact ? "Start a new company brief..." : "Describe your next company idea..."}
          style={{
            flex: 1,
            background: "transparent",
            border: "none",
            outline: "none",
            color: "#E2E8F0",
            fontSize: compact ? 13 : 15,
            fontFamily: "'Pretendard', sans-serif",
          }}
        />
        <button
          onClick={handleSubmit}
          style={{
            width: compact ? 36 : 42,
            height: compact ? 36 : 42,
            borderRadius: compact ? 12 : 14,
            background: "linear-gradient(135deg, var(--blue), #60a5fa)",
            border: "none",
            cursor: "pointer",
            color: "#fff",
            fontSize: compact ? 15 : 18,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flexShrink: 0,
          }}
        >
          ↑
        </button>
      </div>

      {!compact ? (
        <div
          className={styles.eyebrow}
          style={{
            marginTop: 12,
            textAlign: "left",
            color: "rgba(148, 163, 184, 0.86)",
          }}
        >
          Magic Bar · enter your idea and brief Alex in one line
        </div>
      ) : null}
    </div>
  )
}
