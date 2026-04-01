import logging
from graph.state import ProjectState

logger = logging.getLogger(__name__)

# Day 8: Claude Sonnet으로 PRD JSON 실제 생성으로 교체

# prd_json 고정 스키마 — 변경 금지 (Day 10 React Flow 렌더링과 직결)
_PRD_KEYS = ("VP", "CS", "CH", "CR", "R$", "KR", "KA", "KP", "C$")


async def strategy_node(state: ProjectState) -> dict:
    # ── 최상단: 재시도 횟수 초과 체크 ─────────────────────────────
    if state.get("strategy_retry_count", 0) >= 3:
        return {
            "error_message": "전략 수정 3회 초과. 새 아이디어를 다시 입력해주세요.",
            "error_node": "strategy",
            "logs": ["Alex: 수정 횟수를 초과했습니다. 새 아이디어로 시작해주세요."],
        }
    # ────────────────────────────────────────────────────────────

    try:
        project_id = state.get("project_id", "")
        raw_idea = state.get("raw_idea", "")
        ceo_feedback = state.get("ceo_feedback")

        logger.info(
            "[strategy] project_id=%s retry=%d feedback=%s",
            project_id,
            state.get("strategy_retry_count", 0),
            bool(ceo_feedback),
        )

        if ceo_feedback:
            logger.info("[strategy] CEO 피드백 반영 → 재시도")
            log_msg = f"Alex: CEO 피드백 반영 → PRD 재작성 중... ('{ceo_feedback[:40]}')"
        else:
            logger.info("[strategy] 최초 PRD 생성")
            log_msg = "Alex: 시장 분석 중... 비즈니스 캔버스를 작성합니다."

        # ── Day 2 stub: 더미 PRD JSON (9개 키 고정) ───────────────
        dummy_prd: dict = {
            "VP": f"AI 기반 자동 일정 최적화 — {raw_idea[:30]}",
            "CS": "20~30대 바쁜 직장인 / 여행 계획 초보자",
            "CH": "앱스토어, SNS 광고, 입소문",
            "CR": "개인화 추천 + 커뮤니티 리뷰 시스템",
            "R$": "구독 월 9,900원 + 프리미엄 플랜 29,900원",
            "KR": "AI 모델, 지도 API, 숙박/항공 파트너 DB",
            "KA": "AI 일정 생성, 실시간 가격 비교, 고객 지원",
            "KP": "항공사, 호텔 체인, 현지 투어 업체",
            "C$": "AI 인프라 비용, 마케팅비, 파트너 수수료",
        }
        dummy_summary = (
            f"'{raw_idea[:50]}' 아이디어를 바탕으로 "
            "구독형 AI 여행 일정 최적화 서비스를 제안합니다. "
            "핵심 가치는 시간 절약과 최적 가격 보장입니다."
        )
        # ───────────────────────────────────────────────────────────

        return {
            "prd_json": dummy_prd,
            "strategy_summary": dummy_summary,
            "ceo_feedback": None,                              # 승인 후 반드시 초기화
            "strategy_retry_count": state.get("strategy_retry_count", 0) + 1,
            "current_node": "build",
            "logs": [
                log_msg,
                "Alex: PRD 작성 완료 ✓ CEO 승인을 기다립니다.",
            ],
        }

    except Exception as e:
        logger.error("[strategy] project_id=%s error=%s", state.get("project_id"), str(e))
        return {
            "error_message": str(e),
            "error_node": "strategy",
            "logs": ["Alex: 오류가 발생했습니다. 지원팀에 전달됩니다."],
        }
