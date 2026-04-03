"use client"

import { useEffect, useRef } from "react"
import { useProjectStore } from "@/store/projectStore"
import { useChatStore }    from "@/store/chatStore"
import type { NodeId, NodeStatus } from "@/lib/canvas/nodeConfig"

const API_URL     = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"
const MAX_RETRY   = 5
const RETRY_DELAY = 3000  // ms

export function useSSE(projectId: string | null) {
  const setNodeStatus = useProjectStore((s) => s.setNodeStatus)
  const addMessage    = useChatStore((s) => s.addMessage)
  const esRef         = useRef<EventSource | null>(null)
  const retryRef      = useRef(0)
  const timerRef      = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    if (!projectId) return

    function connect() {
      if (esRef.current) esRef.current.close()

      const es = new EventSource(`${API_URL}/stream/${projectId}`)
      esRef.current = es

      es.onmessage = (e) => {
        try {
          const event = JSON.parse(e.data)
          retryRef.current = 0  // 수신 성공 시 재시도 카운터 초기화

          switch (event.type) {
            case "node_update":
              setNodeStatus(event.node as NodeId, event.status as NodeStatus)
              break

            case "log":
              addMessage({
                from:      event.from,
                to:        event.to,
                message:   event.message,
                timestamp: event.timestamp,
              })
              break

            case "interrupt":
              // Day 11: CEO 승인 모달 트리거
              console.log("[SSE] interrupt:", event.interrupt_type)
              break

            case "complete":
              es.close()
              break

            default:
              break
          }
        } catch (err) {
          console.error("[SSE] parse error", err)
        }
      }

      es.onerror = () => {
        es.close()
        if (retryRef.current < MAX_RETRY) {
          retryRef.current++
          console.warn(`[SSE] reconnecting... (${retryRef.current}/${MAX_RETRY})`)
          timerRef.current = setTimeout(connect, RETRY_DELAY)
        } else {
          console.error("[SSE] max retries exceeded")
        }
      }
    }

    connect()

    return () => {
      esRef.current?.close()
      if (timerRef.current) clearTimeout(timerRef.current)
    }
  }, [projectId])
}
