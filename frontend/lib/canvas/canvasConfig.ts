import type { PRDJSON } from "@/types/project"

export interface CanvasNodeConfig {
  id: keyof PRDJSON
  label: string
  icon: string
  color: string
  group: "customer" | "revenue" | "operation"
  position: { row: number; col: number }
  description: string
}

export const CANVAS_NODES: Record<keyof PRDJSON, CanvasNodeConfig> = {
  VP: {
    id: "VP",
    label: "가치 제안",
    icon: "💡",
    color: "var(--blue)",
    group: "customer",
    position: { row: 0, col: 0 },
    description: "고객에게 제공하는 핵심 가치를 정리합니다.",
  },
  CS: {
    id: "CS",
    label: "고객 세그먼트",
    icon: "👥",
    color: "var(--blue)",
    group: "customer",
    position: { row: 0, col: 1 },
    description: "우리가 집중해야 할 핵심 고객군입니다.",
  },
  CH: {
    id: "CH",
    label: "채널",
    icon: "📢",
    color: "var(--blue)",
    group: "customer",
    position: { row: 0, col: 2 },
    description: "고객에게 도달하고 가치를 전달하는 경로입니다.",
  },
  CR: {
    id: "CR",
    label: "고객 관계",
    icon: "🤝",
    color: "var(--green)",
    group: "revenue",
    position: { row: 1, col: 0 },
    description: "고객과 어떤 관계를 만들고 유지할지 설명합니다.",
  },
  "R$": {
    id: "R$",
    label: "수익원",
    icon: "💰",
    color: "var(--green)",
    group: "revenue",
    position: { row: 1, col: 1 },
    description: "수익이 발생하는 구조와 방식입니다.",
  },
  KR: {
    id: "KR",
    label: "핵심 자원",
    icon: "🔧",
    color: "var(--violet)",
    group: "operation",
    position: { row: 1, col: 2 },
    description: "사업 운영에 반드시 필요한 자원입니다.",
  },
  KA: {
    id: "KA",
    label: "핵심 활동",
    icon: "⚙️",
    color: "var(--violet)",
    group: "operation",
    position: { row: 2, col: 0 },
    description: "가치를 실현하기 위해 반복적으로 수행할 활동입니다.",
  },
  KP: {
    id: "KP",
    label: "핵심 파트너",
    icon: "🔗",
    color: "var(--violet)",
    group: "operation",
    position: { row: 2, col: 1 },
    description: "협업해야 하는 파트너와 외부 리소스입니다.",
  },
  "C$": {
    id: "C$",
    label: "비용 구조",
    icon: "💸",
    color: "var(--violet)",
    group: "operation",
    position: { row: 2, col: 2 },
    description: "사업 운영에서 핵심이 되는 비용 항목입니다.",
  },
}

export function getCanvasNodesOrdered(): CanvasNodeConfig[] {
  return Object.values(CANVAS_NODES).sort((a, b) => {
    if (a.position.row !== b.position.row) return a.position.row - b.position.row
    return a.position.col - b.position.col
  })
}
