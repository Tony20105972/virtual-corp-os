"""
Virtual Corp OS — strategy_node
Day 9: AgentLogger 교체 + asyncio 백그라운드 더미 로그 추가

교체 이력:
  Day 2: 더미(stub) 구현 → 하드코딩된 PRD JSON 반환
  Day 8: DeepSeek V3.2 실제 호출 (ENV=dev, 비용 $0)
  Day 9: 직접 yield 방식 → AgentLogger + dummy_log_loop 병렬 실행
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import Any, Optional

from graph.state import ProjectState
from core.constants import ALEX_DUMMY_LOGS, DUMMY_LOG_INTERVAL
from core.llm_client import get_client, get_model, get_max_tokens, OR_HEADERS
from core.logger import AgentLogger
from core.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)

# PRD JSON 필수 키 (Day 10 React Flow 렌더링과 직결 — 변경 금지)
PRD_REQUIRED_KEYS = {"VP", "CS", "CH", "CR", "R$", "KR", "KA", "KP", "C$"}

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


# ── 더미 로그 루프 ────────────────────────────────────────────────────────────
async def _dummy_log_loop(
    log: AgentLogger,
    logs: list[str] = ALEX_DUMMY_LOGS,
    interval: float = DUMMY_LOG_INTERVAL,
) -> None:
    """LLM 대기 중 interval 초 간격으로 더미 로그를 SSE로 흘린다."""
    try:
        idx = 0
        while True:
            msg = logs[min(idx, len(logs) - 1)]  # 소진 시 마지막 항목 반복
            await log.info(msg)
            await asyncio.sleep(interval)
            idx += 1
    except asyncio.CancelledError:
        return  # 정상 취소 — 재raise 금지 (LangGraph 노드 전체 취소 방지)


# ── 헬퍼: interview_answers 포맷팅 ───────────────────────────────────────────
def _format_answers(interview_answers: list[dict]) -> str:
    lines = []
    for i, item in enumerate(interview_answers, 1):
        lines.append(f"Q{i}: {item.get('q', '')}")
        lines.append(f"A{i}: {item.get('a', '')}")
    return "\n".join(lines)


# ── 헬퍼: 프롬프트 구성 ───────────────────────────────────────────────────────
def _build_prompt(state: ProjectState) -> str:
    answers_text = _format_answers(state.get("interview_answers", []))
    base = (
        f"Idea: {state['raw_idea']}\n\n"
        f"Interview answers:\n{answers_text}\n\n"
    )
    ceo_feedback = state.get("ceo_feedback")
    if ceo_feedback:
        base += (
            f"CEO feedback on the previous strategy:\n\"\"\"{ceo_feedback}\"\"\"\n\n"
            "Revise the Business Model Canvas based on the CEO's feedback above.\n"
            "Pay special attention to the areas the CEO criticized.\n"
            "Generate the revised JSON now."
        )
    else:
        base += "Generate the Business Model Canvas JSON now."
    return base


# ── 헬퍼: JSON 추출 + 9키 검증 ───────────────────────────────────────────────
def _extract_prd_json(raw: str) -> dict:
    cleaned = re.sub(r"```(?:json)?\s*|\s*```", "", raw).strip()
    parsed = json.loads(cleaned)                         # JSONDecodeError 가능
    missing = PRD_REQUIRED_KEYS - set(parsed.keys())
    if missing:
        raise ValueError(f"PRD keys missing: {missing}")  # ValueError
    return {k: str(v) for k, v in parsed.items()}


# ── 헬퍼: Supabase 저장 (실패해도 파이프라인 중단 안 함) ──────────────────────
async def _save_prd(project_id: str, prd_json: dict) -> None:
    try:
        client = get_supabase_client()
        client.table("projects").update({
            "prd_json": prd_json,
            "current_node": "build",
        }).eq("project_id", project_id).execute()
        logger.info("[strategy] Supabase 저장 완료 project_id=%s", project_id)
    except Exception as e:
        logger.error(
            "[strategy] Supabase 저장 실패 → 파이프라인 계속 진행 error=%s", str(e)
        )


# ── 메인 노드 ─────────────────────────────────────────────────────────────────
async def strategy_node(state: ProjectState, config: dict[str, Any]) -> dict:
    """
    intake_node 완료 → PRD JSON 9항목 생성 → interrupt ① 대기.
    Day 9: 백그라운드 더미 로그 + AgentLogger 적용.
    """
    project_id = state.get("project_id", "")
    ceo_feedback = state.get("ceo_feedback")
    retry_count = state.get("strategy_retry_count", 0)

    logger.info(
        "[strategy] project_id=%s retry=%d feedback=%s",
        project_id, retry_count, bool(ceo_feedback),
    )

    # ── 재시도 횟수 초과 가드 (최상단) ──────────────────────────────────────
    if retry_count >= 3:
        return {
            "error_message": "전략 수정 3회 초과. 새 아이디어를 다시 입력해주세요.",
            "error_node": "strategy",
            "logs": ["Alex: Strategy revision limit reached. Please start over with a new idea."],
        }

    # Queue 주입 (app/main.py 에서 config["configurable"]["log_queue"] 로 전달)
    queue: asyncio.Queue = config["configurable"]["log_queue"]
    log = AgentLogger("Alex", queue)

    # 피드백 유무에 따른 초기 로그
    if ceo_feedback:
        await log.info(f"Revising strategy based on CEO feedback: {ceo_feedback[:60]}...")
    else:
        await log.info("Starting business strategy analysis...")

    dummy_task: asyncio.Task | None = None
    try:
        # 더미 로그 백그라운드 태스크 시작
        dummy_task = asyncio.create_task(_dummy_log_loop(log))

        # LLM 호출
        client = get_client()
        model = get_model("strategy")
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _build_prompt(state)},
        ]
        logger.info("[strategy] LLM 호출 시작 model=%s project_id=%s", model, project_id)

        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=get_max_tokens("strategy"),
            extra_headers=OR_HEADERS,
        )
        raw_output = response.choices[0].message.content or ""
        logger.info("[strategy] LLM 응답 수신 len=%d project_id=%s", len(raw_output), project_id)

    except Exception as exc:
        # LLM 호출 실패 — 더미 태스크 정리 후 에러 반환
        if dummy_task:
            dummy_task.cancel()
            try:
                await dummy_task
            except asyncio.CancelledError:
                pass
        await log.error(f"Strategy analysis failed: {exc}")
        logger.error("[strategy] LLM 예외 project_id=%s error=%s", project_id, str(exc))
        return {
            "error_message": str(exc),
            "error_node": "strategy",
            "ceo_feedback": None,
            "logs": [f"Alex: Analysis failed — {exc}"],
        }

    # 더미 로그 중단 (cancel → await 로 완전 종료 보장)
    dummy_task.cancel()
    try:
        await dummy_task
    except asyncio.CancelledError:
        pass

    # JSON 파싱 + 9키 검증
    try:
        prd_json = _extract_prd_json(raw_output)
    except (json.JSONDecodeError, ValueError) as exc:
        await log.warn(f"Failed to parse strategy output. Retrying... ({exc})")
        logger.error("[strategy] JSON 파싱 실패 project_id=%s error=%s", project_id, str(exc))
        return {
            "error_message": f"PRD JSON parse error: {str(exc)}",
            "error_node": "strategy",
            "ceo_feedback": None,
            "logs": ["Alex: Failed to parse strategy output. Retrying..."],
        }

    # Supabase 저장
    await _save_prd(project_id, prd_json)

    await log.success("Business canvas complete ✓ Awaiting CEO approval.")

    return {
        "prd_json": prd_json,
        "strategy_summary": None,           # Day 9 스코프 외
        "ceo_feedback": None,               # 반드시 초기화
        "strategy_retry_count": retry_count + 1,
        "current_node": "build",
        "logs": [],
    }
