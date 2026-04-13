from typing import Literal, Optional
from typing_extensions import TypedDict


class RevisionRequest(TypedDict):
    items: list[str]
    reason: str
    custom_feedback: Optional[str]
    timestamp: str


class StrategySummary(TypedDict):
    headline: str
    narrative: str
    target_customer: str
    value_proposition: str
    revenue_model: str
    mvp_scope: list[str]


class ApprovalState(TypedDict, total=False):
    ceo_approval: Optional[str]
    approval_requested_at: Optional[str]
    approval_decided_at: Optional[str]
    revision_count: int
    revision_history: list[RevisionRequest]
    last_revised_items: list[str]
    strategy_report_ready: bool


ProjectStatus = Literal[
    "intake_pending",
    "interviewing",
    "strategy_running",
    "strategy_ready",
    "awaiting_ceo_approval",
    "build_pending",
    "building",
    "build_ready",
    "awaiting_payment_or_deploy_approval",
    "deploying",
    "complete",
    "error",
]


class FeedbackOption(TypedDict):
    value: str
    label: str
    affectedItems: list[str]
    promptHint: str


FEEDBACK_OPTIONS: list[FeedbackOption] = [
    {
        "value": "vp_unclear",
        "label": "가치 제안이 아직 날카롭지 않습니다",
        "affectedItems": ["vp"],
        "promptHint": "누구의 어떤 문제를 왜 더 잘 해결하는지 구체적으로 보강해주세요.",
    },
    {
        "value": "target_too_broad",
        "label": "타겟 고객 범위가 너무 넓습니다",
        "affectedItems": ["cs", "cr"],
        "promptHint": "첫 고객군을 더 좁고 선명하게 정리해주세요.",
    },
    {
        "value": "revenue_unrealistic",
        "label": "수익 모델이 현실성과 연결되지 않습니다",
        "affectedItems": ["rs", "cs_cost"],
        "promptHint": "실제 구매/결제 행동을 기준으로 수익 구조를 다시 설계해주세요.",
    },
    {
        "value": "channel_mismatch",
        "label": "채널 전략이 고객 행동과 맞지 않습니다",
        "affectedItems": ["ch", "cs"],
        "promptHint": "타겟 고객이 실제로 발견하고 전환하는 경로를 반영해주세요.",
    },
    {
        "value": "resource_insufficient",
        "label": "핵심 리소스와 운영 방식이 부족합니다",
        "affectedItems": ["kr", "ka", "kp"],
        "promptHint": "누가 무엇으로 어떻게 운영하는지 더 명확히 써주세요.",
    },
    {
        "value": "cost_missing",
        "label": "비용 구조 설명이 부족합니다",
        "affectedItems": ["cs_cost"],
        "promptHint": "고정비와 변동비를 나눠서 초기 운영비를 보여주세요.",
    },
    {
        "value": "overall_revision",
        "label": "전략 전체를 다시 정렬할 필요가 있습니다",
        "affectedItems": ["vp", "cs", "cr", "ch", "rs", "kr", "ka", "kp", "cs_cost"],
        "promptHint": "핵심 고객, 가치, 수익 모델이 한 방향으로 정렬되도록 다시 작성해주세요.",
    },
    {
        "value": "custom",
        "label": "직접 수정 포인트를 남기겠습니다",
        "affectedItems": [],
        "promptHint": "CEO 관점에서 바꾸고 싶은 방향을 10자 이상 적어주세요.",
    },
]


PRD_ITEM_KEY_MAP = {
    "vp": "VP",
    "cs": "CS",
    "ch": "CH",
    "cr": "CR",
    "rs": "R$",
    "kr": "KR",
    "ka": "KA",
    "kp": "KP",
    "cs_cost": "C$",
}
