"use client"

import { useState } from "react"
import { useInterviewStore } from "@/store/interviewStore"
import { useProjectStore } from "@/store/projectStore"
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
  const { status, setIdea, setPlan, setStatus } = useInterviewStore()
  const setBusinessContext = useProjectStore((state) => state.setBusinessContext)
  const setProjectId = useProjectStore((state) => state.setProjectId)
  const setProjectStatus = useProjectStore((state) => state.setStatus)
  const setNodeStatus = useProjectStore((state) => state.setNodeStatus)
  const setPollingError = useProjectStore((state) => state.setPollingError)
  const setPrdJson = useProjectStore((state) => state.setPrdJson)
  const setStrategySummary = useProjectStore((state) => state.setStrategySummary)
  const setStrategyReportReady = useProjectStore((state) => state.setStrategyReportReady)

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
    setProjectId(null)
    setPollingError(null)
    setPrdJson(null)
    setStrategySummary(null)
    setStrategyReportReady(false)
    setStatus("loading")
    setProjectStatus("interviewing")
    setNodeStatus("intake", "processing")

    try {
      const res = await fetch(`${API_URL}/interview/questions`, {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({ idea: trimmed }),
      })
      const data = await res.json()
      setPlan(data)
      setBusinessContext({
        businessType: data.business_type,
        categoryTags: data.tags ?? [],
      })
      setNodeStatus("intake", "done")
    } catch (err) {
      console.error("[MagicBar] 질문 생성 실패:", err)
      setStatus("idle")
      setProjectStatus("error")
      setNodeStatus("intake", "error")
      return
    }
    setInput("")
  }

  return (
    <div
      className={className}
      style={{
        width: compact ? "min(520px, 100%)" : "min(48rem, 100%)",
      }}
    >
      <div
        className={`${styles.magicBarFrame} ${compact ? styles.magicBarFrameCompact : ""}`}
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
          className={`${styles.magicBarInput} ${compact ? styles.magicBarInputCompact : ""}`}
        />
        <button
          onClick={handleSubmit}
          className={`${styles.magicBarButton} ${compact ? styles.magicBarButtonCompact : ""}`}
        >
          ↑
        </button>
      </div>

      {!compact ? (
        <div className={`${styles.eyebrow} ${styles.magicBarMeta}`}>
          Magic Bar · enter your idea and brief Alex in one line
        </div>
      ) : null}
    </div>
  )
}
