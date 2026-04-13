import logging
from graph.state import ProjectState
from core.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)

async def intake_node(state: ProjectState) -> dict:
    try:
        project_id = state.get("project_id", "")
        raw_idea = state.get("raw_idea", "")
        interview_answers = state.get("interview_answers", [])

        logger.info("[intake] project_id=%s idea=%s", project_id, raw_idea[:50])

        try:
            get_supabase_client().table("projects").update({
                "status": "strategy_running",
                "current_node": "strategy",
            }).eq("project_id", project_id).execute()
        except Exception as exc:
            logger.warning("[intake] status sync failed project_id=%s error=%s", project_id, exc)

        return {
            "current_node": "strategy",
            "status": "strategy_running",
            "interview_answers": interview_answers,
            "logs": [
                "Alex: 사업 아이디어와 인터뷰 답변을 접수했습니다.",
                f"Alex: 인터뷰 완료 — {len(interview_answers)}개 답변을 바탕으로 전략 보고서를 작성합니다.",
            ],
        }

    except Exception as e:
        logger.error("[intake] project_id=%s error=%s", state.get("project_id"), str(e))
        return {
            "error_message": str(e),
            "error_node": "intake",
            "logs": ["Alex: 오류가 발생했습니다. 지원팀에 전달됩니다."],
        }
