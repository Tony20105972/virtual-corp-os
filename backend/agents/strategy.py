"""
Virtual Corp OS — strategy_node
Day 8: DeepSeek V3.2 실제 호출 + 단계별 SSE 로그 + Supabase prd_json 저장

교체 이력:
  Day 2: 더미(stub) 구현 → 하드코딩된 PRD JSON 반환
  Day 8: DeepSeek V3.2 실제 호출 (ENV=dev, 비용 $0)
  Day ??: Prod 성능 평가 후 모델 전환 예정
"""

import re
import json
import logging
from typing import Optional

from graph.state import ProjectState
from core.llm_client import get_client, get_model, get_max_tokens, OR_HEADERS
from core.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)

# PRD JSON 필수 키 (Day 10 React Flow 렌더링과 직결 — 변경 금지)
PRD_REQUIRED_KEYS = {"VP", "CS", "CH", "CR", "R$", "KR", "KA", "KP", "C$"}

# Alex 페르소나 로그 4단계 (영어 → TUI에 출력)
ALEX_LOGS = [
    "Alex: Analyzing market landscape...",
    "Alex: Competitor scan complete ✓",
    "Alex: Drafting business canvas...",
    "Alex: PRD complete ✓ Awaiting CEO approval.",
]

# LLM 시스템 프롬프트 (영어)
SYSTEM_PROMPT = """You are Alex, a sharp and concise business strategy consultant.
Analyze the given idea and interview answers to produce a Business Model Canvas with exactly 9 fields.

Output ONLY a single JSON object. No code fences, no explanation, no preamble.

Required format:
{"VP":"...","CS":"...","CH":"...","CR":"...","R$":"...","KR":"...","KA":"...","KP":"...","C$":"..."}

Rules:
- Write all values in Korean.
- Each value must be 2-3 sentences maximum.
- Be specific and actionable, not generic.
- VP must clearly state what pain it solves and for whom.
- R$ must name a concrete monetization mechanism (subscription, transaction fee, etc.)."""


# ── 헬퍼: interview_answers 포맷팅 ─────────────────────────────────────
def _format_answers(interview_answers: list[dict]) -> str:
    lines = []
    for i, item in enumerate(interview_answers, 1):
        lines.append(f"Q{i}: {item.get('q', '')}")
        lines.append(f"A{i}: {item.get('a', '')}")
    return "\n".join(lines)


# ── 헬퍼: 프롬프트 구성 (최초 / 피드백 재시도 분기) ──────────────────────
def _build_messages(
    raw_idea: str,
    interview_answers: list[dict],
    ceo_feedback: Optional[str],
) -> list[dict]:
    answers_text = _format_answers(interview_answers)

    if ceo_feedback:
        user_content = (
            f"Idea: {raw_idea}\n\n"
            f"Interview answers:\n{answers_text}\n\n"
            f"CEO feedback on the previous strategy:\n\"\"\"{ceo_feedback}\"\"\"\n\n"
            "Revise the Business Model Canvas based on the CEO's feedback above.\n"
            "Pay special attention to the areas the CEO criticized.\n"
            "Generate the revised JSON now."
        )
    else:
        user_content = (
            f"Idea: {raw_idea}\n\n"
            f"Interview answers:\n{answers_text}\n\n"
            "Generate the Business Model Canvas JSON now."
        )

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": user_content},
    ]


# ── 헬퍼: JSON 추출 + 9키 검증 ───────────────────────────────────────────
def _extract_prd_json(raw: str) -> dict:
    cleaned = re.sub(r"```(?:json)?\s*|\s*```", "", raw).strip()
    parsed  = json.loads(cleaned)                          # JSONDecodeError 가능
    missing = PRD_REQUIRED_KEYS - set(parsed.keys())
    if missing:
        raise ValueError(f"PRD keys missing: {missing}")  # ValueError
    return {k: str(v) for k, v in parsed.items()}


# ── 헬퍼: Supabase 저장 (실패해도 파이프라인 중단 안 함) ────────────────────
async def _save_prd(project_id: str, prd_json: dict) -> None:
    try:
        client = get_supabase_client()
        client.table("projects").update({
            "prd_json":     prd_json,
            "current_node": "build",
        }).eq("project_id", project_id).execute()
        logger.info("[strategy] Supabase 저장 완료 project_id=%s", project_id)
    except Exception as e:
        logger.error(
            "[strategy] Supabase 저장 실패 → 파이프라인 계속 진행 error=%s", str(e)
        )


# ── 메인 노드 ──────────────────────────────────────────────────────────
async def strategy_node(state: ProjectState) -> dict:
    project_id   = state.get("project_id", "")
    raw_idea     = state.get("raw_idea", "")
    ceo_feedback = state.get("ceo_feedback")
    retry_count  = state.get("strategy_retry_count", 0)

    logger.info(
        "[strategy] project_id=%s retry=%d feedback=%s",
        project_id, retry_count, bool(ceo_feedback),
    )

    # ── 재시도 횟수 초과 체크 (최상단) ───────────────────────────────────
    if retry_count >= 3:
        return {
            "error_message": "전략 수정 3회 초과. 새 아이디어를 다시 입력해주세요.",
            "error_node":    "strategy",
            "logs":          ["Alex: Strategy revision limit reached. Please start over with a new idea."],
        }

    try:
        # ── 로그 단계 1: LLM 호출 전 ────────────────────────────────────
        pre_log = (
            f"Alex: Revising strategy based on CEO feedback... (\"{ceo_feedback[:40]}\")"
            if ceo_feedback
            else ALEX_LOGS[0]
        )

        # ── LLM 호출 ────────────────────────────────────────────────────
        client   = get_client()
        model    = get_model("strategy")
        messages = _build_messages(raw_idea, state.get("interview_answers", []), ceo_feedback)

        logger.info("[strategy] LLM 호출 시작 model=%s project_id=%s", model, project_id)

        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=get_max_tokens("strategy"),
            extra_headers=OR_HEADERS,
        )

        raw_output = response.choices[0].message.content or ""
        logger.info("[strategy] LLM 응답 수신 len=%d project_id=%s", len(raw_output), project_id)

        # ── JSON 파싱 + 9키 검증 ─────────────────────────────────────────
        prd_json = _extract_prd_json(raw_output)

        # ── Supabase 저장 ────────────────────────────────────────────────
        await _save_prd(project_id, prd_json)

        return {
            "prd_json":             prd_json,
            "strategy_summary":     None,       # Day 9에서 생성
            "ceo_feedback":         None,        # 반드시 초기화
            "strategy_retry_count": retry_count + 1,
            "current_node":         "build",
            "logs": [
                pre_log,
                ALEX_LOGS[1],   # Competitor scan complete ✓
                ALEX_LOGS[2],   # Drafting business canvas...
                ALEX_LOGS[3],   # PRD complete ✓ Awaiting CEO approval.
            ],
        }

    except json.JSONDecodeError as e:
        logger.error("[strategy] JSON 파싱 실패 project_id=%s error=%s", project_id, str(e))
        return {
            "error_message": f"PRD JSON parse error: {str(e)}",
            "error_node":    "strategy",
            "ceo_feedback":  None,
            "logs":          ["Alex: Failed to parse strategy output. Retrying..."],
        }

    except ValueError as e:
        logger.error("[strategy] PRD 키 누락 project_id=%s error=%s", project_id, str(e))
        return {
            "error_message": str(e),
            "error_node":    "strategy",
            "ceo_feedback":  None,
            "logs":          ["Alex: Strategy output incomplete. Retrying..."],
        }

    except Exception as e:
        logger.error("[strategy] 예외 project_id=%s error=%s", project_id, str(e))
        return {
            "error_message": str(e),
            "error_node":    "strategy",
            "ceo_feedback":  None,
            "logs":          ["Alex: An error occurred. Escalating to support."],
        }
