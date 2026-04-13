"""Strategy node for the CEO briefing workflow."""
from __future__ import annotations

import asyncio
import json
import logging
import re
from datetime import datetime, timezone
from typing import Any, Optional

from graph.state import ProjectState
from core.constants import ALEX_DUMMY_LOGS, DUMMY_LOG_INTERVAL
from core.llm_client import chat, get_client, get_model, get_max_tokens, OR_HEADERS
from core.logger import AgentLogger
from core.supabase_client import get_supabase_client
from schemas.approval import StrategySummary

logger = logging.getLogger(__name__)

# PRD JSON 필수 키 (Day 10 React Flow 렌더링과 직결 — 변경 금지)
PRD_REQUIRED_KEYS = {"VP", "CS", "CH", "CR", "R$", "KR", "KA", "KP", "C$"}
ALL_PRD_KEYS_IN_ORDER = ["VP", "CS", "CH", "CR", "R$", "KR", "KA", "KP", "C$"]

# LLM 시스템 프롬프트 (영어)
SYSTEM_PROMPT = """You are Alex, the strategy lead inside Virtual Corp OS.
You create CEO-ready strategy briefs from a raw business idea and structured interview answers.

Return valid JSON only.
Do not wrap JSON in markdown fences.
Do not add any explanation before or after the JSON.
Output exactly one JSON object and nothing else.

Use this exact top-level shape:
{
  "summary": {
    "headline": "...",
    "narrative": "...",
    "target_customer": "...",
    "value_proposition": "...",
    "revenue_model": "...",
    "mvp_scope": ["...", "...", "..."]
  },
  "canvas": {
    "VP": "...",
    "CS": "...",
    "CH": "...",
    "CR": "...",
    "R$": "...",
    "KR": "...",
    "KA": "...",
    "KP": "...",
    "C$": "..."
  }
}

Rules:
- Write in Korean.
- Be concrete and operator-level, not generic.
- Narrative must read like a CEO briefing memo.
- MVP scope must be 3 to 5 short bullets.
- Canvas values must be concise but specific."""

REPAIR_PROMPT = """Convert the following model output into valid JSON only.
Do not add markdown.
Do not add commentary.
Return exactly one JSON object matching the requested schema.

Malformed content:
{malformed_output}
"""


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
        lines.append(f"Q{i}: {item.get('title') or item.get('q', '')}")
        lines.append(f"A{i}: {item.get('answer') or item.get('a', '')}")
    return "\n".join(lines)


# ── 헬퍼: 프롬프트 구성 ───────────────────────────────────────────────────────
def _build_prompt(state: ProjectState) -> str:
    answers_text = _format_answers(state.get("interview_answers", []))
    revision_history = state.get("revision_history", [])
    latest_revision = revision_history[-1] if revision_history else None

    prompt = (
        f"Raw idea:\n{state['raw_idea']}\n\n"
        f"Business type: {state.get('business_type', 'general')}\n"
        f"Category tags: {', '.join(state.get('category_tags', [])) or 'none'}\n\n"
        f"Structured interview answers:\n{answers_text}\n\n"
    )
    if state.get("prd_json"):
        prompt += f"Previous canvas:\n{json.dumps(state.get('prd_json'), ensure_ascii=False, indent=2)}\n\n"
    if latest_revision:
        prompt += (
            "CEO revision request:\n"
            f"- affected_items: {', '.join(latest_revision.get('items', []))}\n"
            f"- reason: {latest_revision.get('reason', '')}\n"
            f"- custom_feedback: {latest_revision.get('custom_feedback') or 'none'}\n\n"
        )
    prompt += (
        "Create a strategy report that explains why this business should be defined this way, "
        "then output the CEO summary and full 9-block canvas."
    )
    return prompt


# ── 헬퍼: JSON 추출 + 9키 검증 ───────────────────────────────────────────────
def strip_code_fences(text: str) -> str:
    return re.sub(r"```(?:json)?\s*|\s*```", "", text).strip()


def extract_first_json_object(text: str) -> str:
    start = text.find("{")
    if start == -1:
        raise ValueError("No JSON object start found")

    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start:index + 1]

    raise ValueError("No complete JSON object found")


def parse_strategy_response(text: str) -> tuple[StrategySummary, dict]:
    cleaned = strip_code_fences(text)
    json_text = extract_first_json_object(cleaned)
    parsed = json.loads(json_text)
    summary = parsed.get("summary")
    canvas = parsed.get("canvas")
    if not isinstance(summary, dict) or not isinstance(canvas, dict):
        raise ValueError("summary and canvas are required")

    missing = PRD_REQUIRED_KEYS - set(canvas.keys())
    if missing:
        raise ValueError(f"PRD keys missing: {missing}")

    normalized_summary: StrategySummary = {
        "headline": str(summary.get("headline", "")),
        "narrative": str(summary.get("narrative", "")),
        "target_customer": str(summary.get("target_customer", "")),
        "value_proposition": str(summary.get("value_proposition", "")),
        "revenue_model": str(summary.get("revenue_model", "")),
        "mvp_scope": [str(item) for item in summary.get("mvp_scope", [])][:5],
    }
    normalized_canvas = {k: str(v) for k, v in canvas.items() if k in PRD_REQUIRED_KEYS}
    return normalized_summary, normalized_canvas


async def repair_strategy_response(malformed_output: str) -> str:
    return await chat(
        "strategy",
        [
            {"role": "system", "content": "You repair malformed strategy JSON outputs."},
            {"role": "user", "content": REPAIR_PROMPT.format(malformed_output=malformed_output)},
        ],
        max_tokens=get_max_tokens("strategy"),
    )


# ── 헬퍼: Supabase 저장 (실패해도 파이프라인 중단 안 함) ──────────────────────
async def _save_prd(project_id: str, payload: dict) -> None:
    try:
        client = get_supabase_client()
        client.table("projects").update(payload).eq("project_id", project_id).execute()
        logger.info("[strategy] Supabase 저장 완료 project_id=%s", project_id)
    except Exception as e:
        logger.error(
            "[strategy] Supabase 저장 실패 → 파이프라인 계속 진행 error=%s", str(e)
        )


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── 메인 노드 ─────────────────────────────────────────────────────────────────
async def strategy_node(state: ProjectState, config: dict[str, Any]) -> dict:
    project_id = state.get("project_id", "")
    retry_count = state.get("strategy_retry_count", 0)
    revision_count = state.get("revision_count", 0)

    logger.info(
        "[strategy] project_id=%s retry=%d revision_count=%d business_type=%s",
        project_id, retry_count,
        revision_count,
        state.get("business_type"),
    )

    # ── 재시도 횟수 초과 가드 (최상단) ──────────────────────────────────────
    if revision_count >= 3:
        await _save_prd(
            project_id,
            {
                "status": "error",
                "current_node": "strategy",
            },
        )
        return {
            "error_message": "전략 수정 3회 초과. 새 아이디어를 다시 입력해주세요.",
            "error_node": "strategy",
            "status": "error",
            "logs": ["Alex: Strategy revision limit reached. Please start over with a new idea."],
        }

    # Queue 주입 (app/main.py 에서 config["configurable"]["log_queue"] 로 전달)
    queue: asyncio.Queue = config["configurable"]["log_queue"]
    log = AgentLogger("Alex", queue)

    # 피드백 유무에 따른 초기 로그
    if state.get("revision_history"):
        await log.info("CEO 수정 요청을 반영해 전략 보고서를 다시 정리하고 있습니다...")
    else:
        await log.info("인터뷰 답변을 바탕으로 전략 보고서를 작성하고 있습니다...")

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
            "status": "error",
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
        strategy_summary, prd_json = parse_strategy_response(raw_output)
        last_revised_items = (
            state.get("revision_history", [])[-1].get("items", [])
            if state.get("revision_history")
            else []
        )
    except (json.JSONDecodeError, ValueError) as exc:
        await log.warn(f"Strategy JSON parsing failed. Repairing once... ({exc})")
        logger.error("[strategy] JSON 파싱 실패 project_id=%s error=%s", project_id, str(exc))
        try:
            repaired_output = await repair_strategy_response(raw_output)
            strategy_summary, prd_json = parse_strategy_response(repaired_output)
            last_revised_items = (
                state.get("revision_history", [])[-1].get("items", [])
                if state.get("revision_history")
                else []
            )
            await log.info("Strategy JSON repair succeeded. Saving CEO briefing now.")
        except Exception as repair_exc:
            await log.error("전략 보고서 형식을 복구하지 못했습니다. 에러 상태로 전환합니다.")
            await _save_prd(
                project_id,
                {
                    "status": "error",
                    "current_node": "strategy",
                },
            )
            logger.error("[strategy] repair 실패 project_id=%s error=%s", project_id, str(repair_exc))
            return {
                "error_message": f"PRD JSON parse error: {repair_exc}",
                "error_node": "strategy",
                "status": "error",
                "logs": ["Alex: Strategy report formatting failed. Switching project to error state."],
            }

    # Supabase 저장
    approval_requested_at = _utc_now_iso()
    await _save_prd(
        project_id,
        {
            "prd_json": prd_json,
            "strategy_summary": strategy_summary,
            "current_node": "strategy",
            "status": "awaiting_ceo_approval",
            "strategy_report_ready": True,
            "ceo_approval": "pending",
            "approval_requested_at": approval_requested_at,
            "last_revised_items": last_revised_items,
            "revision_count": revision_count,
        },
    )

    await log.success("전략 보고서가 준비되었습니다. 이제 CEO 브리핑을 검토할 수 있습니다.")

    return {
        "prd_json": prd_json,
        "strategy_summary": strategy_summary,
        "ceo_feedback": None,               # 반드시 초기화
        "strategy_retry_count": retry_count + 1,
        "current_node": "approval_decision",
        "status": "awaiting_ceo_approval",
        "strategy_report_ready": True,
        "ceo_approval": "pending",
        "approval_requested_at": approval_requested_at,
        "last_revised_items": last_revised_items,
        "revision_count": revision_count,
        "logs": [],
    }
