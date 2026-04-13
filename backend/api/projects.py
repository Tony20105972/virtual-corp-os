import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field, field_validator, model_validator

from core.queue_store import project_queues
from core.supabase_client import get_supabase_client
from graph.builder import get_graph
from schemas.approval import FEEDBACK_OPTIONS

router = APIRouter(prefix="/projects", tags=["projects"])
logger = logging.getLogger(__name__)

ALL_AFFECTED_ITEMS = ["vp", "cs", "cr", "ch", "rs", "kr", "ka", "kp", "cs_cost"]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_graph_config(project_id: str):
    return {
        "configurable": {
            "thread_id": project_id,
            "log_queue": project_queues.setdefault(project_id, asyncio.Queue(maxsize=100)),
        }
    }


def get_feedback_option(value: str) -> dict:
    for option in FEEDBACK_OPTIONS:
        if option["value"] == value:
            return option
    raise HTTPException(
        status_code=400,
        detail={
            "error": "Invalid feedback option",
            "code": "VALIDATION_ERROR",
            "detail": f"feedback_option '{value}'은(는) 유효하지 않습니다.",
            "valid_options": [opt["value"] for opt in FEEDBACK_OPTIONS],
        },
    )


def get_project_or_404(project_id: str) -> dict:
    response = (
        get_supabase_client()
        .table("projects")
        .select(
            "project_id,status,raw_idea,prd_json,strategy_summary,business_type,category_tags,"
            "strategy_report_ready,revision_count,revision_history,last_revised_items,"
            "ceo_approval,approval_requested_at,approval_decided_at,updated_at,payment_done"
        )
        .eq("project_id", project_id)
        .limit(1)
        .execute()
    )
    rows = response.data or []
    if not rows:
        raise HTTPException(
            status_code=404,
            detail={"error": "Project not found", "code": "NOT_FOUND", "project_id": project_id},
        )
    return rows[0]


def update_graph_state(project_id: str, updates: dict) -> None:
    try:
        get_graph().update_state(build_graph_config(project_id), updates)
    except Exception as exc:
        logger.warning("[projects] graph.update_state failed project_id=%s error=%s", project_id, exc)


async def resume_graph(project_id: str) -> None:
    await get_graph().ainvoke(None, config=build_graph_config(project_id))


class ReviseRequest(BaseModel):
    feedback_option: str
    custom_feedback: Optional[str] = Field(default=None, min_length=10)

    @field_validator("feedback_option")
    @classmethod
    def validate_feedback_option(cls, value: str) -> str:
        valid = [opt["value"] for opt in FEEDBACK_OPTIONS]
        if value not in valid:
            raise ValueError(f"Invalid feedback_option: {value}")
        return value

    @model_validator(mode="after")
    def validate_custom_feedback(self) -> "ReviseRequest":
        if self.feedback_option == "custom" and not self.custom_feedback:
            raise ValueError("custom_feedback is required when feedback_option is 'custom'")
        return self


class PaymentConfirmRequest(BaseModel):
    stripe_payment_intent_id: str = Field(min_length=3)


@router.post("/{project_id}/approve")
async def approve_project(project_id: str, background_tasks: BackgroundTasks):
    project = get_project_or_404(project_id)
    if project["status"] != "awaiting_ceo_approval":
        raise HTTPException(
            status_code=409,
            detail={
                "error": "Cannot approve project",
                "code": "INVALID_STATUS",
                "detail": "전략 보고서가 준비되고 CEO 검토 단계일 때만 승인할 수 있습니다.",
                "current_status": project["status"],
            },
        )

    decided_at = utc_now_iso()
    get_supabase_client().table("projects").update(
        {
            "status": "build_pending",
            "ceo_approval": "approved",
            "approval_decided_at": decided_at,
        }
    ).eq("project_id", project_id).execute()

    update_graph_state(
        project_id,
        {
            "status": "build_pending",
            "ceo_approval": "approved",
            "approval_decided_at": decided_at,
        },
    )
    background_tasks.add_task(resume_graph, project_id)

    return {
        "status": "build_pending",
        "message": "CEO 승인 완료. 개발팀이 MVP 착수 준비에 들어갑니다.",
        "project_id": project_id,
        "updated_at": decided_at,
    }


@router.post("/{project_id}/revise", status_code=202)
async def request_revision(project_id: str, request: ReviseRequest, background_tasks: BackgroundTasks):
    project = get_project_or_404(project_id)
    if project["status"] != "awaiting_ceo_approval":
        raise HTTPException(
            status_code=409,
            detail={
                "error": "Cannot request revision",
                "code": "INVALID_STATUS",
                "detail": "CEO 브리핑 단계에서만 전략 수정을 요청할 수 있습니다.",
                "current_status": project["status"],
            },
        )
    if int(project.get("revision_count") or 0) >= 3:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Revision limit exceeded",
                "code": "REVISION_LIMIT",
                "detail": "수정 요청은 최대 3회까지 가능합니다.",
                "revision_count": project.get("revision_count", 0),
                "max_revisions": 3,
            },
        )

    feedback_opt = get_feedback_option(request.feedback_option)
    affected_items = feedback_opt["affectedItems"] or ALL_AFFECTED_ITEMS
    revision_count = int(project.get("revision_count") or 0) + 1
    decided_at = utc_now_iso()
    new_history = list(project.get("revision_history") or [])
    new_history.append(
        {
            "items": affected_items,
            "reason": feedback_opt["label"],
            "custom_feedback": request.custom_feedback,
            "timestamp": decided_at,
        }
    )

    get_supabase_client().table("projects").update(
        {
            "status": "strategy_running",
            "ceo_approval": "revise",
            "approval_decided_at": decided_at,
            "revision_count": revision_count,
            "revision_history": new_history,
            "last_revised_items": affected_items,
            "strategy_report_ready": False,
        }
    ).eq("project_id", project_id).execute()

    update_graph_state(
        project_id,
        {
            "status": "strategy_running",
            "ceo_approval": "revise",
            "approval_decided_at": decided_at,
            "revision_count": revision_count,
            "revision_history": new_history,
            "last_revised_items": affected_items,
            "strategy_report_ready": False,
        },
    )
    background_tasks.add_task(resume_graph, project_id)

    return {
        "status": "strategy_running",
        "message": "CEO 수정 요청을 반영해 전략 보고서를 다시 작성하고 있습니다.",
        "affected_items": affected_items,
        "revision_count": revision_count,
        "estimated_time_seconds": 30,
        "project_id": project_id,
    }


@router.post("/{project_id}/confirm-payment")
async def confirm_payment(project_id: str, request: PaymentConfirmRequest, background_tasks: BackgroundTasks):
    project = get_project_or_404(project_id)
    if project["ceo_approval"] != "approved":
        raise HTTPException(
            status_code=409,
            detail={
                "error": "Cannot confirm payment",
                "code": "CEO_APPROVAL_REQUIRED",
                "detail": "CEO 승인 이전에는 결제/배포 승인으로 넘어갈 수 없습니다.",
                "current_status": project["status"],
            },
        )
    if project["status"] != "awaiting_payment_or_deploy_approval":
        raise HTTPException(
            status_code=409,
            detail={
                "error": "Cannot confirm payment",
                "code": "INVALID_STATUS",
                "detail": "빌드가 완료되어 배포 승인 대기 상태일 때만 결제를 확인할 수 있습니다.",
                "current_status": project["status"],
            },
        )

    approved_at = utc_now_iso()
    get_supabase_client().table("projects").update(
        {
            "status": "deploying",
            "approval_decided_at": approved_at,
            "payment_done": True,
        }
    ).eq("project_id", project_id).execute()

    update_graph_state(
        project_id,
        {
            "status": "deploying",
            "payment_done": True,
            "stripe_session_id": request.stripe_payment_intent_id,
        },
    )
    background_tasks.add_task(resume_graph, project_id)

    return {
        "status": "deploying",
        "message": "배포 승인이 확인되었습니다. 런칭 절차를 진행합니다.",
        "next_node": "deploy",
        "project_id": project_id,
        "approved_at": approved_at,
    }


@router.get("/{project_id}/status")
async def get_project_status(project_id: str):
    project = get_project_or_404(project_id)
    return {
        "project_id": project["project_id"],
        "status": project["status"],
        "raw_idea": project.get("raw_idea"),
        "business_type": project.get("business_type"),
        "category_tags": project.get("category_tags") or [],
        "strategy_report_ready": project.get("strategy_report_ready", False),
        "strategy_summary": project.get("strategy_summary"),
        "prd_json": project.get("prd_json"),
        "revision_count": project.get("revision_count", 0),
        "last_revised_items": project.get("last_revised_items") or [],
        "ceo_approval": project.get("ceo_approval"),
        "updated_at": project.get("updated_at"),
        "approval_requested_at": project.get("approval_requested_at"),
    }
