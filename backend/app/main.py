import asyncio
import logging
import uuid
from typing import Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from graph.builder import get_graph
from api.stream import router as stream_router
from api.interview import router as interview_router
from api.projects import router as projects_router
from core.auth import prepare_dev_user_fallback, resolve_user_id
from core.project_repository import create_project, insert_interview, insert_project_event
from core.queue_store import project_queues

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Ghost Founder API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stream_router)
app.include_router(interview_router)
app.include_router(projects_router)


@app.on_event("startup")
async def prepare_dev_mode_user():
    dev_user_id = prepare_dev_user_fallback()
    if dev_user_id:
        logger.info("[startup] development user fallback ready user_id=%s", dev_user_id)


# ──────────────────────────────────────────
# Pydantic 요청 모델
# ──────────────────────────────────────────
class RunRequest(BaseModel):
    idea: str
    user_id: Optional[str] = None
    interview_questions: list[dict] = []
    interview_answers: list[dict] = []
    business_type: Optional[str] = None
    category_tags: list[str] = []


class ResumeStrategyRequest(BaseModel):
    approved: bool
    feedback: Optional[str] = None


class ResumeDeployRequest(BaseModel):
    approved: bool
    payment_done: bool


def build_graph_config(project_id: str):
    return {
        "configurable": {
            "thread_id": project_id,
            "log_queue": project_queues.setdefault(project_id, asyncio.Queue(maxsize=100)),
        }
    }


async def execute_graph(initial_state: dict, config: dict):
    graph = get_graph()
    await graph.ainvoke(initial_state, config=config)


# ──────────────────────────────────────────
# POST /run
# ──────────────────────────────────────────
@app.post("/run")
async def run(request: Request, body: RunRequest, background_tasks: BackgroundTasks):
    project_id = str(uuid.uuid4())
    config = build_graph_config(project_id)
    user_id = resolve_user_id(request, body.user_id)

    initial_state = {
        "project_id": project_id,
        "user_id": user_id,
        "raw_idea": body.idea,
        "current_node": "intake",
        "status": "strategy_processing" if body.interview_answers else "interviewing",
        "logs": [],
        "build_errors": [],
        "interview_answers": body.interview_answers,
        "business_type": body.business_type or "other",
        "category_tags": body.category_tags,
        "strategy_retry_count": 0,
        "build_retry_count": 0,
        "payment_done": False,
        "ceo_feedback": None,
        "ceo_approval": "pending",
        "revision_count": 0,
        "last_revised_items": [],
        "prd_json": None,
        "strategy_summary": None,
        "strategy_report_json": None,
        "strategy_report_ready": False,
        "code_files": None,
        "github_repo": None,
        "deploy_url": None,
        "error_message": None,
        "error_node": None,
    }

    logger.info("[/run] project_id=%s idea=%s", project_id, body.idea[:50])

    # Supabase에 프로젝트 row 생성 (strategy_node의 UPDATE가 동작하려면 row가 먼저 필요)
    try:
        create_project({
            "project_id": project_id,
            "user_id": user_id,
            "raw_idea": body.idea,
            "current_node": "intake",
            "status": "strategy_processing" if body.interview_answers else "interviewing",
            "business_type": body.business_type or "other",
            "category_tags": body.category_tags,
            "revision_count": 0,
            "last_revised_items": [],
            "strategy_report_ready": False,
            "ceo_approval": "pending",
            "strategy_report_json": None,
            "prd_json": None,
            "strategy_summary": None,
            "payment_done": False,
            "deploy_url": None,
            "error_message": None,
        })
        insert_project_event(
            project_id,
            agent_name="System",
            event_type="project_created",
            message="프로젝트가 생성되었습니다.",
            payload_json={"status": initial_state["status"], "user_id": user_id},
        )
        if body.interview_answers:
            insert_interview(
                project_id,
                business_type=body.business_type or "other",
                category_tags=body.category_tags,
                question_set_json=body.interview_questions,
                answers_json=body.interview_answers,
            )
            insert_project_event(
                project_id,
                agent_name="Alex",
                event_type="interview_saved",
                message="인터뷰 응답이 저장되었습니다.",
                payload_json={"answer_count": len(body.interview_answers)},
            )
        logger.info("[/run] Supabase project row 생성 완료 project_id=%s", project_id)
    except Exception as e:
        logger.error("[/run] Supabase insert 실패 project_id=%s error=%s", project_id, str(e))
        raise HTTPException(
            status_code=500,
            detail={
                "error": "PROJECT_CREATE_FAILED",
                "detail": str(e),
                "project_id": project_id,
            },
        )

    if body.interview_answers:
        background_tasks.add_task(execute_graph, initial_state, config)

    return {
        "project_id": project_id,
        "current_node": initial_state["current_node"],
        "status": initial_state["status"],
        "revision_count": 0,
        "last_revised_items": [],
        "prd_json": None,
        "strategy_summary": None,
        "strategy_report_json": None,
        "strategy_report_ready": False,
        "logs": [],
    }


# ──────────────────────────────────────────
# POST /resume/strategy/{project_id}
# ──────────────────────────────────────────
@app.post("/resume/strategy/{project_id}")
async def resume_strategy(project_id: str, body: ResumeStrategyRequest):
    # approved=false면 feedback 필수
    if not body.approved and not body.feedback:
        raise HTTPException(
            status_code=400,
            detail="거절 시 feedback 필드가 필요합니다.",
        )

    graph = get_graph()
    config = build_graph_config(project_id)

    if body.approved:
        # CEO 승인 → build 노드 진입 (interrupt ① 해제)
        retried = False
        logger.info("[/resume/strategy] project_id=%s approved=true", project_id)
        graph.update_state(config, {"ceo_approval": "approved", "status": "build_pending"})
    else:
        # CEO 수정 요청 → ceo_feedback 주입 후 strategy 재실행
        retried = True
        logger.info(
            "[/resume/strategy] project_id=%s approved=false feedback=%s",
            project_id,
            body.feedback[:40] if body.feedback else "",
        )
        graph.update_state(config, {"ceo_feedback": body.feedback, "ceo_approval": "rejected", "status": "strategy_processing"})

    result = await graph.ainvoke(None, config=config)

    response = {
        "project_id": project_id,
        "current_node": result.get("current_node"),
        "prd_json": result.get("prd_json"),
        "strategy_summary": result.get("strategy_summary"),
        "strategy_report_json": result.get("strategy_report_json"),
        "logs": result.get("logs", []),
    }
    if retried:
        response["retried"] = True

    return response


# ──────────────────────────────────────────
# POST /resume/deploy/{project_id}
# ──────────────────────────────────────────
@app.post("/resume/deploy/{project_id}")
async def resume_deploy(project_id: str, body: ResumeDeployRequest):
    # approved + payment_done 둘 다 true여야 배포 진행
    if not body.approved or not body.payment_done:
        raise HTTPException(
            status_code=400,
            detail="approved와 payment_done이 모두 true여야 배포가 진행됩니다.",
        )

    graph = get_graph()
    config = build_graph_config(project_id)

    logger.info("[/resume/deploy] project_id=%s", project_id)

    graph.update_state(config, {"payment_done": True, "status": "deploying"})
    result = await graph.ainvoke(None, config=config)

    return {
        "project_id": project_id,
        "current_node": result.get("current_node"),
        "deploy_url": result.get("deploy_url"),
        "logs": result.get("logs", []),
    }
