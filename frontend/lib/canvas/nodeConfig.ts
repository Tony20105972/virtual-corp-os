import type { Node, Edge } from "@xyflow/react"
import type { AgentNodeData } from "@/components/canvas/AgentNode"

export type NodeId = "intake" | "strategy" | "build" | "deploy"

// 에이전트별 색상 매핑 — CSS 변수와 동기화
export const AGENT_COLORS: Record<NodeId, string> = {
  intake:   "#3B82F6",  // --blue
  strategy: "#8B5CF6",  // --violet
  build:    "#10B981",  // --green
  deploy:   "#F59E0B",  // --amber
}

// 에이전트 메타데이터
export const AGENT_META: Record<NodeId, { label: string; persona: string; role: string }> = {
  intake:   { label: "INTAKE",   persona: "Alex",  role: "Strategy Consultant" },
  strategy: { label: "STRATEGY", persona: "Alex",  role: "PRD Design" },
  build:    { label: "BUILD",    persona: "Jamie", role: "Full-Stack Dev" },
  deploy:   { label: "DEPLOY",   persona: "Sam",   role: "QA + Deploy" },
}

// 고정 레이아웃 좌표 — Day 10 dagre 교체 시 이 블록만 제거
const POSITIONS: Record<NodeId, { x: number; y: number }> = {
  intake:   { x: 80,  y: 80  },
  strategy: { x: 360, y: 80  },
  build:    { x: 80,  y: 280 },
  deploy:   { x: 360, y: 280 },
}

// React Flow Node 초기값 생성
export function buildInitialNodes(): Node<AgentNodeData>[] {
  return (Object.keys(POSITIONS) as NodeId[]).map((id) => ({
    id,
    type: "agentNode",
    position: POSITIONS[id],
    data: {
      id,
      label:   AGENT_META[id].label,
      persona: AGENT_META[id].persona,
      role:    AGENT_META[id].role,
      color:   AGENT_COLORS[id],
    },
    draggable: true,
  }))
}

// React Flow Edge 초기값 생성
// 2×2 grid: intake(top-left) strategy(top-right) build(bottom-left) deploy(bottom-right)
export function buildInitialEdges(): Edge[] {
  return [
    { id: "e-intake-strategy", source: "intake",   sourceHandle: "right",  target: "strategy", targetHandle: "left",   type: "animatedEdge" },
    { id: "e-strategy-deploy", source: "strategy", sourceHandle: "bottom", target: "deploy",   targetHandle: "top",    type: "animatedEdge" },
    { id: "e-intake-build",    source: "intake",   sourceHandle: "bottom", target: "build",    targetHandle: "top",    type: "animatedEdge" },
    { id: "e-build-deploy",    source: "build",    sourceHandle: "right",  target: "deploy",   targetHandle: "left",   type: "animatedEdge" },
  ]
}
