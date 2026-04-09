"use client"

import { useEffect, useRef } from "react"
import { useChatStore, type ChatMessage } from "@/store/chatStore"

const AGENT_COLORS: Record<string, string> = {
  Alex:   "#3B82F6",
  Jamie:  "#10B981",
  Sam:    "#F59E0B",
  System: "#94A3B8",
}

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
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  return (
    <div style={{
      position:       "absolute",
      bottom:         80,
      right:          16,
      width:          280,
      height:         220,
      background:     "rgba(10, 15, 30, 0.88)",
      backdropFilter: "blur(12px)",
      border:         "1px solid rgba(255,255,255,0.08)",
      borderRadius:   10,
      zIndex:         10,
      display:        "flex",
      flexDirection:  "column",
      overflow:       "hidden",
    }}>
      <div style={{
        padding:       "8px 12px",
        borderBottom:  "1px solid rgba(255,255,255,0.06)",
        fontFamily:    "'DM Mono', monospace",
        fontSize:      10,
        letterSpacing: "0.12em",
        color:         "#64748B",
      }}>
        AGENT CHAT
      </div>

      <div style={{ flex: 1, overflowY: "auto", padding: "10px 12px" }}>
        {messages.length === 0 && (
          <div style={{ fontSize: 11, color: "#64748B", fontFamily: "'DM Mono', monospace" }}>
            Waiting for agents...
          </div>
        )}
        {messages.map((msg) => (
          <MessageRow key={msg.id} msg={msg} />
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  )
}
