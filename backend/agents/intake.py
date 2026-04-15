import logging
from graph.state import ProjectState
from core.project_repository import insert_project_event, update_project

logger = logging.getLogger(__name__)

async def intake_node(state: ProjectState) -> dict:
    try:
        project_id = state.get("project_id", "")
        raw_idea = state.get("raw_idea", "")
        interview_answers = state.get("interview_answers", [])

        logger.info("[intake] project_id=%s idea=%s", project_id, raw_idea[:50])

        try:
            update_project(
                project_id,
                {
                    "status": "strategy_processing",
                    "current_node": "strategy",
                    "error_message": None,
                },
            )
            insert_project_event(
                project_id,
                agent_name="Alex",
                event_type="intake_completed",
                message="인터뷰 입력을 바탕으로 전략 분석을 시작합니다.",
                payload_json={"answer_count": len(interview_answers)},
            )
        except Exception as exc:
            logger.warning("[intake] status sync failed project_id=%s error=%s", project_id, exc)

        return {
            "current_node": "strategy",
            "status": "strategy_processing",
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
