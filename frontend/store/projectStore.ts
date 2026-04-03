import { create } from "zustand"
import type { NodeId } from "@/lib/canvas/nodeConfig"

export type NodeStatus = "idle" | "processing" | "done" | "error"

// 상태 순환 순서 — Day 4 클릭 테스트용
const STATUS_CYCLE: NodeStatus[] = ["idle", "processing", "done", "error"]

interface ProjectStore {
  // 노드 상태
  nodeStatuses: Record<NodeId, NodeStatus>
  setNodeStatus: (id: NodeId, status: NodeStatus) => void
  cycleNodeStatus: (id: NodeId) => void  // 클릭 테스트용

  // 프로젝트 메타 (Day 6에서 채워짐)
  projectId: string | null
  setProjectId: (id: string) => void
}

export const useProjectStore = create<ProjectStore>((set, get) => ({
  nodeStatuses: {
    intake:   "idle",
    strategy: "idle",
    build:    "idle",
    deploy:   "idle",
  },

  setNodeStatus: (id, status) =>
    set((s) => ({ nodeStatuses: { ...s.nodeStatuses, [id]: status } })),

  cycleNodeStatus: (id) => {
    const current = get().nodeStatuses[id]
    const idx = STATUS_CYCLE.indexOf(current)
    const next = STATUS_CYCLE[(idx + 1) % STATUS_CYCLE.length]
    set((s) => ({ nodeStatuses: { ...s.nodeStatuses, [id]: next } }))
  },

  projectId: null,
  setProjectId: (id) => set({ projectId: id }),
}))
