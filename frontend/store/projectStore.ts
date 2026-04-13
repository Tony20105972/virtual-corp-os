import { create } from "zustand"
import type { NodeId } from "@/lib/canvas/nodeConfig"
import type { PRDJSON } from "@/types/project"
import type { FeedbackOption, ProjectStatus } from "@/types/approval"

export interface StrategySummary {
  headline?: string
  summary?: string
  narrative?: string
  target_customer?: string
  value_proposition?: string
  revenue_model?: string
  mvp_scope?: string[]
  category_tags?: string[]
  risks?: string[]
  next_steps?: string[]
}

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
  setProjectId: (id: string | null) => void
  pollingError: string | null
  setPollingError: (message: string | null) => void

  // Strategy 결과물
  prd_json: PRDJSON | null
  setPrdJson: (prd: PRDJSON | null) => void
  strategySummary: StrategySummary | null
  setStrategySummary: (summary: StrategySummary | null) => void
  strategyReportReady: boolean
  setStrategyReportReady: (ready: boolean) => void
  businessType: string | null
  categoryTags: string[]
  setBusinessContext: (payload: { businessType: string | null; categoryTags: string[] }) => void

  // Day 10: Canvas Modal State
  canvasModalOpen: boolean
  selectedCanvasNode: keyof PRDJSON | null
  openCanvasModal: () => void
  closeCanvasModal: () => void
  selectCanvasNode: (nodeId: keyof PRDJSON | null) => void

  // Day 11: Approval Workflow
  approvalModalOpen: boolean
  paymentConfirmModalOpen: boolean
  selectedFeedback: FeedbackOption | null
  customFeedback: string
  revisionCount: number
  lastRevisedItems: string[]
  status: ProjectStatus
  openApprovalModal: () => void
  closeApprovalModal: () => void
  openPaymentConfirmModal: () => void
  closePaymentConfirmModal: () => void
  setSelectedFeedback: (option: FeedbackOption | null) => void
  setCustomFeedback: (text: string) => void
  setRevisionCount: (count: number) => void
  setLastRevisedItems: (items: string[]) => void
  setStatus: (status: ProjectStatus) => void
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
  pollingError: null,
  setPollingError: (message) => set({ pollingError: message }),

  prd_json: null,
  setPrdJson: (prd) => set({ prd_json: prd }),
  strategySummary: null,
  setStrategySummary: (summary) => set({ strategySummary: summary }),
  strategyReportReady: false,
  setStrategyReportReady: (ready) => set({ strategyReportReady: ready }),
  businessType: null,
  categoryTags: [],
  setBusinessContext: ({ businessType, categoryTags }) => set({ businessType, categoryTags }),

  canvasModalOpen: false,
  selectedCanvasNode: null,
  openCanvasModal: () => set({ canvasModalOpen: true }),
  closeCanvasModal: () =>
    set({
      canvasModalOpen: false,
      selectedCanvasNode: null,
    }),
  selectCanvasNode: (nodeId) => set({ selectedCanvasNode: nodeId }),

  approvalModalOpen: false,
  paymentConfirmModalOpen: false,
  selectedFeedback: null,
  customFeedback: "",
  revisionCount: 0,
  lastRevisedItems: [],
  status: "intake_pending",
  openApprovalModal: () => set({ approvalModalOpen: true }),
  closeApprovalModal: () =>
    set({
      approvalModalOpen: false,
      selectedFeedback: null,
      customFeedback: "",
    }),
  openPaymentConfirmModal: () => set({ paymentConfirmModalOpen: true }),
  closePaymentConfirmModal: () => set({ paymentConfirmModalOpen: false }),
  setSelectedFeedback: (option) => set({ selectedFeedback: option }),
  setCustomFeedback: (text) => set({ customFeedback: text }),
  setRevisionCount: (count) => set({ revisionCount: count }),
  setLastRevisedItems: (items) => set({ lastRevisedItems: items }),
  setStatus: (status) => set({ status }),
}))
