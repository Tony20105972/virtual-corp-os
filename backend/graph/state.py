import operator
from typing import Annotated, Literal, Optional
from typing_extensions import TypedDict
from schemas.approval import ProjectStatus, StrategyReport
from schemas.interview import InterviewAnswer


class ProjectState(TypedDict, total=False):
    # ──────────────────────────────────────────
    # 누적 필드 — operator.add (덮어쓰기 금지)
    # ──────────────────────────────────────────
    logs: Annotated[list[str], operator.add]
    build_errors: Annotated[list[str], operator.add]
    interview_answers: Annotated[list[InterviewAnswer], operator.add]

    # ──────────────────────────────────────────
    # 단일값 필드 — 마지막 write가 이김
    # ──────────────────────────────────────────
    project_id: str
    user_id: Optional[str]
    current_node: Literal[
        "intake",
        "strategy",
        "approval_decision",
        "build",
        "deploy",
        "live",
        "error",
    ]
    raw_idea: str
    business_type: str
    category_tags: list[str]
    strategy_report_ready: bool

    # strategy
    prd_json: Optional[dict]
    strategy_summary: Optional[str]
    strategy_report_json: Optional[StrategyReport]
    ceo_feedback: Optional[str]        # 승인 후 반드시 None으로 초기화
    strategy_retry_count: int          # max 3
    status: ProjectStatus
    ceo_approval: Optional[str]
    revision_count: int
    last_revised_items: list[str]

    # build
    code_files: Optional[dict]         # {"app/page.tsx": "..."}
    github_repo: Optional[str]
    build_retry_count: int             # max 3

    # deploy
    deploy_url: Optional[str]

    # payment
    payment_done: bool

    # error
    error_message: Optional[str]
    error_node: Optional[str]
