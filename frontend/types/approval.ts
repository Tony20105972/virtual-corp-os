export type FeedbackOption = {
  value: string
  label: string
  affectedItems: string[]
  promptHint?: string
}

export const FEEDBACK_OPTIONS: FeedbackOption[] = [
  {
    value: "vp_unclear",
    label: "💡 가치 제안이 명확하지 않습니다",
    affectedItems: ["vp"],
    promptHint: "독특한 가치와 차별점을 구체적으로 설명해주세요",
  },
  {
    value: "target_too_broad",
    label: "🎯 타겟 고객이 너무 광범위합니다",
    affectedItems: ["cs", "cr"],
    promptHint: "고객 세그먼트를 더 좁고 구체적으로 정의해주세요",
  },
  {
    value: "revenue_unrealistic",
    label: "💰 수익 모델이 비현실적입니다",
    affectedItems: ["rs", "cs_cost"],
    promptHint: "실현 가능한 가격과 비용 구조를 제시해주세요",
  },
  {
    value: "channel_mismatch",
    label: "📣 채널 전략이 타겟과 맞지 않습니다",
    affectedItems: ["ch", "cs"],
    promptHint: "타겟 고객이 실제로 사용하는 채널을 선택해주세요",
  },
  {
    value: "resource_insufficient",
    label: "🔧 핵심 리소스 설명이 부족합니다",
    affectedItems: ["kr", "ka", "kp"],
    promptHint: "비즈니스 운영에 필수적인 리소스를 구체적으로 나열해주세요",
  },
  {
    value: "cost_missing",
    label: "💸 비용 구조가 불완전합니다",
    affectedItems: ["cs_cost"],
    promptHint: "고정비와 변동비를 명확히 구분하여 작성해주세요",
  },
  {
    value: "overall_revision",
    label: "🔄 전체적으로 다시 검토가 필요합니다",
    affectedItems: ["vp", "cs", "cr", "ch", "rs", "kr", "ka", "kp", "cs_cost"],
    promptHint: "전체 비즈니스 모델을 재검토하여 일관성을 높여주세요",
  },
  {
    value: "custom",
    label: "✏️ 직접 입력 (구체적 피드백)",
    affectedItems: [],
    promptHint: "구체적인 피드백을 10자 이상 입력해주세요",
  },
]

export type RevisionRequest = {
  items: string[]
  reason: string
  custom_feedback: string | null
  timestamp: string
}

export type ProjectStatus =
  | "intake_pending"
  | "interviewing"
  | "strategy_running"
  | "strategy_ready"
  | "awaiting_ceo_approval"
  | "build_pending"
  | "building"
  | "build_ready"
  | "awaiting_payment_or_deploy_approval"
  | "deploying"
  | "complete"
  | "error"
