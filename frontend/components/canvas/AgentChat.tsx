"use client"

import { useEffect, useRef } from "react"
import { useChatStore, type ChatMessage } from "@/store/chatStore"
import { useInterviewStore } from "@/store/interviewStore"

const AGENT_COLORS: Record<string, string> = {
  Alex:   "#3B82F6",
  Jamie:  "#10B981",
  Sam:    "#F59E0B",
  Aria:   "#8B5CF6",
  System: "#94A3B8",
}

const PREVIEW_LINES = [
  { agent: "Alex", message: "Positioning defined. I am turning the brief into strategy." },
  { agent: "Jamie", message: "Landing page architecture is ready for a first build." },
  { agent: "Sam", message: "QA checkpoints are mapped before anything ships." },
  { agent: "Aria", message: "Launch copy is tuned for clarity, speed, and trust." },
]

function MessageRow({ msg }: { msg: ChatMessage }) {
  const color = AGENT_COLORS[msg.agent] ?? "#94A3B8"

  return (
    <div style={{ marginBottom: 8, lineHeight: 1.5 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 2 }}>
        <span style={{ fontFamily: "'DM Mono', monospace", fontSize: 11, color, fontWeight: 500 }}>
          {msg.agent}:
        </span>
      </div>
      <div style={{
        fontFamily:  "'Pretendard', sans-serif",
        fontSize:    12,
        color:       "#CBD5E1",
        paddingLeft: 8,
        borderLeft:  `2px solid ${color}44`,
      }}>
        {msg.message}
      </div>
    </div>
  )
}

export default function AgentChat() {
  const messages  = useChatStore((s) => s.messages)
  const status = useInterviewStore((s) => s.status)
  const bottomRef = useRef<HTMLDivElement>(null)
  const listRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const list = listRef.current
    if (!list) return
    list.scrollTop = list.scrollHeight
  }, [messages])

  const visibleMessages =
    messages.length > 0
      ? messages
      : PREVIEW_LINES.map((line, index) => ({
          id: `preview-${index}`,
          level: "info" as const,
          agent: line.agent,
          message: line.message,
        }))

  return (
    <div style={{ height: "100%", display: "flex", flexDirection: "column", minHeight: 0 }}>
      <div style={{
        padding: "18px 20px 14px",
        borderBottom: "1px solid rgba(255,255,255,0.06)",
        fontFamily: "'DM Mono', monospace",
        fontSize: 10,
        letterSpacing: "0.12em",
        color: "#64748B",
      }}>
        {status === "done" ? "AGENT FEED" : "YOUR AI BOARDROOM"}
      </div>

      <div
        ref={listRef}
        style={{ flex: 1, overflowY: "auto", padding: "16px 18px 20px", minHeight: 0 }}
      >
        {messages.length === 0 && status === "done" ? (
          <div style={{ fontSize: 11, color: "#64748B", fontFamily: "'DM Mono', monospace" }}>
            Waiting for agents...
          </div>
        ) : null}
        {visibleMessages.map((msg) => (
          <MessageRow key={msg.id} msg={msg} />
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  )
}
