import logging
import uuid
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from graph.builder import get_graph

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Ghost Founder API", version="0.2.0")


# ──────────────────────────────────────────
# Pydantic 요청 모델
# ──────────────────────────────────────────
class RunRequest(BaseModel):
    idea: str
    user_id: Optional[str] = None


class ResumeStrategyRequest(BaseModel):
    approved: bool
    feedback: Optional[str] = None


class ResumeDeployRequest(BaseModel):
    approved: bool
    payment_done: bool


# ──────────────────────────────────────────
# POST /run
# ──────────────────────────────────────────
@app.post("/run")
async def run(body: RunRequest):
    graph = get_graph()
    project_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": project_id}}

    initial_state = {
        "project_id": project_id,
        "user_id": body.user_id,
        "raw_idea": body.idea,
        "current_node": "intake",
        "logs": [],
        "build_errors": [],
        "interview_answers": [],
        "strategy_retry_count": 0,
        "build_retry_count": 0,
        "payment_done": False,
        "ceo_feedback": None,
        "prd_json": None,
        "strategy_summary": None,
        "code_files": None,
        "github_repo": None,
        "deploy_url": None,
        "preview_url": None,
        "vercel_project_id": None,
        "stripe_session_id": None,
        "error_message": None,
        "error_node": None,
    }

    logger.info("[/run] project_id=%s idea=%s", project_id, body.idea[:50])

    result = await graph.ainvoke(initial_state, config=config)

    return {
        "project_id": project_id,
        "current_node": result.get("current_node"),
        "prd_json": result.get("prd_json"),
        "strategy_summary": result.get("strategy_summary"),
        "logs": result.get("logs", []),
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
    config = {"configurable": {"thread_id": project_id}}

    if body.approved:
        # CEO 승인 → build 노드 진입 (interrupt ① 해제)
        retried = False
        logger.info("[/resume/strategy] project_id=%s approved=true", project_id)
    else:
        # CEO 거절 → ceo_feedback 주입 후 strategy 재실행
        retried = True
        logger.info(
            "[/resume/strategy] project_id=%s approved=false feedback=%s",
            project_id,
            body.feedback[:40] if body.feedback else "",
        )
        graph.update_state(config, {"ceo_feedback": body.feedback})

    result = await graph.ainvoke(None, config=config)

    response = {
        "project_id": project_id,
        "current_node": result.get("current_node"),
        "prd_json": result.get("prd_json"),
        "strategy_summary": result.get("strategy_summary"),
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
    config = {"configurable": {"thread_id": project_id}}

    logger.info("[/resume/deploy] project_id=%s", project_id)

    graph.update_state(config, {"payment_done": True})
    result = await graph.ainvoke(None, config=config)

    return {
        "project_id": project_id,
        "current_node": result.get("current_node"),
        "deploy_url": result.get("deploy_url"),
        "logs": result.get("logs", []),
    }
