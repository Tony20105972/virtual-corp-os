"use client"

import { memo } from "react"
import { Handle, Position, type NodeProps, type Node } from "@xyflow/react"
import { motion } from "framer-motion"
import { useProjectStore, type NodeStatus } from "@/store/projectStore"
import type { NodeId } from "@/lib/canvas/nodeConfig"

export interface AgentNodeData extends Record<string, unknown> {
  id: NodeId
  label: string
  persona: string
  role: string
  color: string
}

export type AgentNodeType = Node<AgentNodeData, "agentNode">

// 상태별 스타일 매핑
function getStatusStyle(status: NodeStatus, color: string) {
  switch (status) {
    case "processing":
      return {
        border: `1px solid ${color}`,
        background: `${color}14`,  // ~8% opacity
      }
    case "done":
      return {
        border: `1px solid ${color}`,
        background: `${color}1F`,  // ~12% opacity
      }
    case "error":
      return {
        border: "1px solid #EF4444",
        background: "rgba(239,68,68,0.08)",
      }
    default: // idle
      return {
        border: "1px solid rgba(255,255,255,0.08)",
        background: "rgba(255,255,255,0.04)",
      }
  }
}

function StatusIcon({ status }: { status: NodeStatus }) {
  if (status === "done")
    return <span style={{ color: "#10B981", fontSize: 14, lineHeight: 1 }}>✓</span>
  if (status === "error")
    return <span style={{ color: "#EF4444", fontSize: 14, lineHeight: 1 }}>⚠</span>
  if (status === "processing")
    return (
      <span
        style={{
          display: "inline-block",
          width: 10,
          height: 10,
          border: "2px solid currentColor",
          borderTopColor: "transparent",
          borderRadius: "50%",
          animation: "spin 0.8s linear infinite",
          color: "var(--slate)",
        }}
      />
    )
  return null
}

const AgentNode = memo(({ data }: NodeProps<AgentNodeType>) => {
  const status = useProjectStore((s) => s.nodeStatuses[data.id])
  const cycleNodeStatus = useProjectStore((s) => s.cycleNodeStatus)
  const openCanvasModal = useProjectStore((s) => s.openCanvasModal)
  const style = getStatusStyle(status, data.color)

  return (
    <>
      <Handle id="left"   type="target" position={Position.Left}   style={{ opacity: 0 }} />
      <Handle id="top"    type="target" position={Position.Top}    style={{ opacity: 0 }} />

      {/* Pulse glow — processing 상태에서만 */}
      {status === "processing" && (
        <motion.div
          style={{
            position: "absolute",
            inset: -2,
            borderRadius: 10,
            pointerEvents: "none",
          }}
          animate={{
            boxShadow: [
              `0 0 0px 0px ${data.color}00`,
              `0 0 18px 4px ${data.color}66`,
              `0 0 0px 0px ${data.color}00`,
            ],
          }}
          transition={{ duration: 1.4, repeat: Infinity, ease: "easeInOut" }}
        />
      )}

      {/* 노드 본체 */}
      <div
        onClick={() => cycleNodeStatus(data.id)}
        style={{
          ...style,
          borderRadius: 8,
          padding: "14px 18px",
          minWidth: 160,
          cursor: "pointer",
          userSelect: "none",
          transition: "all 0.2s",
          position: "relative",
        }}
      >
        {/* 상단: 라벨 + 아이콘 */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            marginBottom: 6,
          }}
        >
          <span
            style={{
              fontFamily: "'DM Mono', monospace",
              fontSize: 10,
              letterSpacing: "0.15em",
              color: status === "idle" ? "var(--slate-d)" : data.color,
              textTransform: "uppercase",
            }}
          >
            {data.label}
          </span>
          <StatusIcon status={status} />
        </div>

        {/* 퍼소나 이름 */}
        <div
          style={{
            fontFamily: "'Syne', sans-serif",
            fontSize: 15,
            fontWeight: 700,
            color: status === "idle" ? "var(--slate)" : "#F8FAFC",
            marginBottom: 2,
          }}
        >
          {data.persona}
        </div>

        {/* 역할 */}
        <div
          style={{
            fontFamily: "'DM Mono', monospace",
            fontSize: 10,
            color: "var(--slate-d)",
          }}
        >
          {data.role}
        </div>

        {/* 상태 배지 */}
        <div
          style={{
            marginTop: 8,
            display: "inline-block",
            padding: "2px 8px",
            borderRadius: 100,
            background: status === "idle" ? "rgba(255,255,255,0.04)" : `${data.color}22`,
            color: status === "idle" ? "var(--slate-d)" : data.color,
            fontFamily: "'DM Mono', monospace",
            fontSize: 9,
            letterSpacing: "0.1em",
            textTransform: "uppercase",
          }}
        >
          {status}
        </div>

        {data.id === "strategy" && status === "done" ? (
          <motion.button
            type="button"
            onClick={(event) => {
              event.stopPropagation()
              openCanvasModal()
            }}
            style={{
              position: "absolute",
              left: "50%",
              bottom: -14,
              transform: "translateX(-50%)",
              border: "1px solid rgba(147,197,253,0.45)",
              borderRadius: 999,
              background: "linear-gradient(135deg, rgba(59,130,246,0.96), rgba(96,165,250,0.96))",
              color: "#EFF6FF",
              padding: "6px 12px",
              fontFamily: "'DM Mono', monospace",
              fontSize: 10,
              letterSpacing: "0.06em",
              cursor: "pointer",
              whiteSpace: "nowrap",
              boxShadow: "0 10px 24px rgba(59,130,246,0.32)",
            }}
            animate={{
              boxShadow: [
                "0 10px 24px rgba(59,130,246,0.24)",
                "0 14px 32px rgba(59,130,246,0.42)",
                "0 10px 24px rgba(59,130,246,0.24)",
              ],
            }}
            transition={{ duration: 1.8, repeat: Infinity, ease: "easeInOut" }}
          >
            📊 보고서 보기
          </motion.button>
        ) : null}
      </div>

      <Handle id="right"  type="source" position={Position.Right}  style={{ opacity: 0 }} />
      <Handle id="bottom" type="source" position={Position.Bottom} style={{ opacity: 0 }} />
    </>
  )
})

AgentNode.displayName = "AgentNode"
export default AgentNode
