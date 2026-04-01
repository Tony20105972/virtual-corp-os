import logging
from graph.state import ProjectState

logger = logging.getLogger(__name__)

# Day 6: LLM AI Interviewer 3문 3답으로 교체


async def intake_node(state: ProjectState) -> dict:
    try:
        project_id = state.get("project_id", "")
        raw_idea = state.get("raw_idea", "")

        logger.info("[intake] project_id=%s idea=%s", project_id, raw_idea[:50])

        # ── Day 2 stub: 더미 인터뷰 응답 ──────────────────────────
        dummy_answers = [
            {"q": "주요 고객은 누구인가요?",         "a": "20~30대 직장인"},
            {"q": "핵심 문제는 무엇인가요?",         "a": "여행 일정 조율 시간 낭비"},
            {"q": "기존 대안과 차별점은 무엇인가요?", "a": "AI 자동 최적화 일정 생성"},
        ]
        # ─────────────────────────────────────────────────────────

        return {
            "current_node": "strategy",
            "interview_answers": dummy_answers,
            "logs": [
                "Alex: 아이디어를 접수했습니다. 시장 분석을 시작합니다...",
                f"Alex: 인터뷰 완료 — {len(dummy_answers)}개 답변 수집",
            ],
        }

    except Exception as e:
        logger.error("[intake] project_id=%s error=%s", state.get("project_id"), str(e))
        return {
            "error_message": str(e),
            "error_node": "intake",
            "logs": ["Alex: 오류가 발생했습니다. 지원팀에 전달됩니다."],
        }
