"""Strategy node for the CEO briefing workflow."""
from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import Any

from core.constants import ALEX_DUMMY_LOGS, DUMMY_LOG_INTERVAL
from core.llm_client import (
    DEFAULT_STRATEGY_MAX_TOKENS,
    FALLBACK_STRATEGY_MAX_TOKENS,
    OR_HEADERS,
    chat,
    get_client,
    get_model,
    is_budget_limit_error,
)
from core.logger import AgentLogger
from core.project_repository import (
    get_next_strategy_run_index,
    insert_project_event,
    insert_strategy_run,
    update_project,
)
from graph.state import ProjectState
from schemas.approval import StrategyReport

logger = logging.getLogger(__name__)

ALLOWED_BUSINESS_TYPES: set[str] = {
    "saas",
    "commerce",
    "marketplace",
    "service",
    "media",
    "community",
    "other",
}

SYSTEM_PROMPT = """You are Alex, the strategy lead inside Virtual Corp OS.
You write a CEO decision memo from a raw business idea and structured interview answers.

YOU MUST RETURN VALID JSON ONLY.
DO NOT WRITE ANY TEXT BEFORE OR AFTER THE JSON.
DO NOT USE MARKDOWN.
DO NOT EXPLAIN.
DO NOT ADD A PREFACE, INTRO, OUTRO, OR COMMENTS.
OUTPUT EXACTLY ONE JSON OBJECT.
YOUR RESPONSE MUST START WITH { AND END WITH }.
IF YOU FAIL TO RETURN JSON, THE SYSTEM WILL BREAK.
당신의 출력은 엄격한 JSON 파서에 의해 처리된다. JSON 외의 출력은 시스템을 실패시킨다.

Return Korean copy that is concrete, persuasive, and operator-level.
The JSON must match this exact shape:
{
  "strategy_summary": "한 줄 요약",
  "business_type": "saas | commerce | marketplace | service | media | community | other",
  "category_tags": ["string"],
  "report": {
    "problem": { "title": "핵심 문제", "body": "..." },
    "customer": { "title": "핵심 고객", "body": "..." },
    "solution": { "title": "해결 방식", "body": "..." },
    "why_now": { "title": "왜 지금인가", "body": "..." },
    "business_model": { "title": "수익 모델", "body": "..." },
    "mvp_scope": { "title": "추천 MVP 범위", "items": ["...", "...", "..."] },
    "differentiators": { "title": "핵심 차별점", "items": ["...", "...", "..."] },
    "risks": { "title": "주요 리스크", "items": ["...", "..."] },
    "go_to_market": { "title": "초기 진입 전략", "body": "..." }
  },
  "ceo_brief": {
    "headline": "CEO에게 보여줄 한 줄 헤드라인",
    "approval_note": "이 범위로 개발팀 착수 여부를 판단할 문장"
  }
}

Constraints:
- mvp_scope.items must contain exactly 3 strings.
- differentiators.items must contain exactly 3 strings.
- risks.items must contain exactly 2 strings.
- Use the provided business_type and category_tags unless they are obviously invalid, then normalize conservatively.
- Keep titles short and executive-friendly.
- The report should read like a real CEO briefing memo, not a classroom canvas.
- Do not add any extra keys anywhere.
"""

FEW_SHOT_EXAMPLE = """Example input:
{
  "raw_idea": "Online book club platform",
  "business_type": "community",
  "category_tags": ["books", "community", "subscription"],
  "interview_answers": [
    {
      "question": "가장 먼저 붙잡고 싶은 고객은 누구인가요?",
      "answer": "직접 독서모임을 운영하기 부담스럽지만 꾸준히 읽고 싶은 20~30대 직장인"
    },
    {
      "question": "초기 참여를 유지시키는 핵심 행동은 무엇인가요?",
      "answer": "월간 선정 도서를 읽고 토론방에 인증과 감상을 남기는 것"
    }
  ]
}

Example output:
{
  "strategy_summary": "바쁜 직장인이 가볍게 참여할 수 있는 월간 독서 습관형 북클럽 커뮤니티",
  "business_type": "community",
  "category_tags": ["books", "community", "subscription"],
  "report": {
    "problem": {
      "title": "독서 습관 유지의 어려움",
      "body": "혼자 책을 읽으면 완독 동기와 대화 자극이 약해 금방 이탈한다. 오프라인 모임은 일정 조율 부담이 커서 꾸준히 참여하기 어렵다."
    },
    "customer": {
      "title": "가벼운 루틴을 원하는 직장인 독자",
      "body": "정기적으로 책을 읽고 싶지만 직접 모임을 만들 시간은 없는 20~30대 직장인이 초기 핵심 고객이다."
    },
    "solution": {
      "title": "월간 도서 중심 참여 루프",
      "body": "월간 추천 도서, 가벼운 토론방, 인증 리마인드를 묶어 혼자 읽어도 커뮤니티의 추진력을 느끼게 만든다."
    },
    "why_now": {
      "title": "가벼운 취향 커뮤니티 수요 확대",
      "body": "텍스트 기반 커뮤니티와 구독형 취향 서비스에 익숙한 사용자가 늘면서, 오프라인 강제성이 낮은 독서 모임에 대한 수요가 커지고 있다."
    },
    "business_model": {
      "title": "구독형 멤버십",
      "body": "월 구독료를 받고 추천 도서 큐레이션, 토론방 참여, 멤버 전용 리포트를 제공한다."
    },
    "mvp_scope": {
      "title": "추천 MVP 범위",
      "items": ["월간 도서 선정과 공지", "토론방 및 인증 댓글", "구독 결제와 멤버십 관리"]
    },
    "differentiators": {
      "title": "핵심 차별점",
      "items": ["읽기 루틴을 만드는 운영 설계", "오프라인 부담 없는 참여 구조", "도서 선정부터 토론까지 한 흐름으로 연결"]
    },
    "risks": {
      "title": "주요 리스크",
      "items": ["초기 참여 밀도가 낮으면 토론 활력이 약해질 수 있다", "도서 큐레이션 품질이 낮으면 구독 유지율이 빠르게 떨어질 수 있다"]
    },
    "go_to_market": {
      "title": "초기 진입 전략",
      "body": "북 인플루언서 뉴스레터, 직장인 커뮤니티, SNS 리딩 챌린지와 제휴해 첫 달 체험 멤버를 모은다."
    }
  },
  "ceo_brief": {
    "headline": "운영 부담 없이 참여하는 월간 북클럽을 구독형 커뮤니티로 출시합니다.",
    "approval_note": "초기에는 월간 도서 운영 루프와 결제 흐름만 선명하게 만들면 개발팀이 MVP 착수 판단을 내릴 수 있습니다."
  }
}"""

REPAIR_PROMPT = """You repair malformed strategy outputs into the required CEO report JSON.
YOU MUST RETURN VALID JSON ONLY.
DO NOT WRITE ANY TEXT BEFORE OR AFTER THE JSON.
DO NOT USE MARKDOWN.
DO NOT EXPLAIN.
DO NOT ADD A PREFACE, INTRO, OUTRO, OR COMMENTS.
OUTPUT EXACTLY ONE JSON OBJECT.
YOUR RESPONSE MUST START WITH { AND END WITH }.
IF YOU FAIL TO RETURN JSON, THE SYSTEM WILL BREAK.
당신의 출력은 엄격한 JSON 파서에 의해 처리된다. JSON 외의 출력은 시스템을 실패시킨다.

방금 생성한 전략 내용을 유지하되, 유효한 JSON 객체만 다시 출력하라.
설명문 금지. 코드블록 금지. 주석 금지.
Return exactly one JSON object that matches the requested schema.

Malformed content:
{malformed_output}
"""

REVISION_PROMPT_RULES = """You are revising a previously generated CEO report.
Return the full final JSON object again from scratch.
Do not return a diff.
Do not explain what changed.
Do not wrap the JSON in markdown.
Do not summarize outside the JSON.
"""

COMPACT_PROMPT_RULES = """Compact strategy mode is enabled.
Keep every body field to one short sentence.
Keep every item concise and execution-focused.
Prefer concrete, compressed Korean copy over long explanation.
Return the same JSON schema with shorter content.
"""

REPORT_BODY_KEYS = (
    "problem",
    "customer",
    "solution",
    "why_now",
    "business_model",
    "go_to_market",
)

REPORT_ITEMS_KEYS = (
    ("mvp_scope", 3),
    ("differentiators", 3),
    ("risks", 2),
)

TOP_LEVEL_KEYS = {
    "strategy_summary",
    "business_type",
    "category_tags",
    "report",
    "ceo_brief",
}

REPORT_KEYS = {
    "problem",
    "customer",
    "solution",
    "why_now",
    "business_model",
    "mvp_scope",
    "differentiators",
    "risks",
    "go_to_market",
}

BODY_SECTION_KEYS = {"title", "body"}
ITEM_SECTION_KEYS = {"title", "items"}
CEO_BRIEF_KEYS = {"headline", "approval_note"}


async def _dummy_log_loop(
    log: AgentLogger,
    logs: list[str] = ALEX_DUMMY_LOGS,
    interval: float = DUMMY_LOG_INTERVAL,
) -> None:
    try:
        idx = 0
        while True:
            msg = logs[min(idx, len(logs) - 1)]
            await log.info(msg)
            await asyncio.sleep(interval)
            idx += 1
    except asyncio.CancelledError:
        return


def _format_answers(interview_answers: list[dict]) -> str:
    lines: list[str] = []
    for i, item in enumerate(interview_answers, 1):
        lines.append(f"{i}. 질문: {item.get('title') or item.get('q', '')}")
        lines.append(f"   답변: {item.get('answer') or item.get('a', '')}")
    return "\n".join(lines) if lines else "없음"


def _normalize_text(value: Any, fallback: str = "") -> str:
    if isinstance(value, str):
        return value.strip()
    return fallback


def _normalize_items(value: Any, expected_len: int) -> list[str]:
    if not isinstance(value, list):
        raise ValueError("items must be a list")
    items = [_normalize_text(item) for item in value if _normalize_text(item)]
    if len(items) < expected_len:
        raise ValueError(f"items must contain at least {expected_len} entries")
    return items[:expected_len]


def _build_prompt(state: ProjectState, *, compact: bool = False) -> str:
    is_revision = bool(state.get("ceo_feedback") or state.get("last_revised_items"))
    payload = {
        "raw_idea": state["raw_idea"],
        "business_type": state.get("business_type", "other"),
        "category_tags": state.get("category_tags", []),
        "interview_answers": [
            {
                "question": item.get("title") or item.get("q", ""),
                "answer": item.get("answer") or item.get("a", ""),
            }
            for item in state.get("interview_answers", [])
        ],
    }

    prompt_sections = [
        "Here is the working context.",
        "Actual input:",
        json.dumps(payload, ensure_ascii=False, indent=2),
        f"Dynamic interview answers:\n{_format_answers(state.get('interview_answers', []))}",
    ]

    if not compact:
        prompt_sections.insert(1, FEW_SHOT_EXAMPLE)
    else:
        prompt_sections.insert(1, COMPACT_PROMPT_RULES)

    if is_revision:
        previous_report = state.get("strategy_report_json")
        previous_report_context = (
            json.dumps(previous_report, ensure_ascii=False, indent=2)
            if not compact
            else json.dumps(
                {
                    "strategy_summary": previous_report.get("strategy_summary") if isinstance(previous_report, dict) else None,
                    "headline": (
                        previous_report.get("ceo_brief", {}).get("headline")
                        if isinstance(previous_report, dict)
                        else None
                    ),
                    "business_type": previous_report.get("business_type") if isinstance(previous_report, dict) else None,
                    "category_tags": previous_report.get("category_tags") if isinstance(previous_report, dict) else None,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        prompt_sections.extend(
            [
                REVISION_PROMPT_RULES,
                "Previous strategy report JSON:",
                previous_report_context,
                "CEO revision request:",
                f"- affected_items: {', '.join(state.get('last_revised_items', [])) or 'none'}",
                f"- custom_feedback: {state.get('ceo_feedback') or 'none'}",
                (
                    "Regenerate the full CEO report JSON with the same schema. "
                    "Reflect the revision request, but keep the answer as one complete JSON object only."
                ),
            ]
        )
    else:
        prompt_sections.append(
            "Generate the first CEO report JSON now using the exact schema and return valid JSON only."
        )

    prompt_sections.append(
        "Final reminder: return exactly one complete JSON object. No markdown. No explanation. No trailing text."
    )
    return "\n\n".join(prompt_sections)


async def _call_strategy_llm(prompt_text: str, *, model: str, max_tokens: int) -> str:
    client = get_client()
    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt_text},
        ],
        max_tokens=max_tokens,
        extra_headers=OR_HEADERS,
    )
    return response.choices[0].message.content or ""


async def _generate_strategy_output(
    state: ProjectState,
    *,
    project_id: str,
    run_index: int,
    model: str,
    prompt_version: str,
    log: AgentLogger,
) -> tuple[str, dict[str, Any]]:
    prompt_text = _build_prompt(state, compact=False)
    prompt_debug: dict[str, Any] = {
        "mode": "default",
        "run_index": run_index,
        "prompt_version": prompt_version,
        "max_tokens": DEFAULT_STRATEGY_MAX_TOKENS,
        "prompt_text": prompt_text,
        "retry_reason": None,
    }

    try:
        logger.info(
            "[strategy] LLM 호출 시작 model=%s project_id=%s mode=default prompt_len=%d max_tokens=%d",
            model,
            project_id,
            len(prompt_text),
            DEFAULT_STRATEGY_MAX_TOKENS,
        )
        raw_output = await _call_strategy_llm(
            prompt_text,
            model=model,
            max_tokens=DEFAULT_STRATEGY_MAX_TOKENS,
        )
        return raw_output, prompt_debug
    except Exception as exc:
        logger.exception("[strategy] default generation failed project_id=%s", project_id)
        if not is_budget_limit_error(exc):
            raise

        await log.warn("Alex: 토큰 예산 한도를 감지했습니다. 축약 전략 모드로 전환합니다.")
        compact_prompt = _build_prompt(state, compact=True)
        prompt_debug = {
            "mode": "compact",
            "run_index": run_index,
            "prompt_version": prompt_version,
            "max_tokens": FALLBACK_STRATEGY_MAX_TOKENS,
            "prompt_text": compact_prompt,
            "retry_reason": str(exc),
        }
        logger.warning(
            "[strategy] budget limit detected project_id=%s run_index=%s retrying_compact max_tokens=%d error=%s",
            project_id,
            run_index,
            FALLBACK_STRATEGY_MAX_TOKENS,
            exc,
        )
        raw_output = await _call_strategy_llm(
            compact_prompt,
            model=model,
            max_tokens=FALLBACK_STRATEGY_MAX_TOKENS,
        )
        await log.success("Alex: 축약 전략 생성이 완료되었습니다. CEO 검토를 기다립니다.")
        return raw_output, prompt_debug


def strip_code_fences(text: str) -> str:
    return re.sub(r"```(?:json)?\s*|\s*```", "", text).strip()


def _try_parse_json_object(candidate: str) -> dict:
    parsed = json.loads(candidate)
    if not isinstance(parsed, dict):
        raise ValueError("Top-level JSON must be an object")
    return parsed


def _extract_code_block_json(text: str) -> str:
    match = re.search(r"```json\s*(.*?)\s*```", text, re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(1).strip()
    match = re.search(r"```\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    raise ValueError("No JSON code block found")


def _extract_between_outer_braces(text: str) -> str:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object boundaries found")
    return text[start:end + 1].strip()


def _extract_strategy_json(text: str) -> tuple[dict, str, str]:
    attempts: list[tuple[str, str]] = [("raw", text.strip())]

    try:
        attempts.append(("code_block", _extract_code_block_json(text)))
    except Exception:
        pass

    try:
        attempts.append(("outer_braces", _extract_between_outer_braces(text)))
    except Exception:
        pass

    last_error: Exception | None = None
    for source, candidate in attempts:
        try:
            parsed = _try_parse_json_object(candidate)
            return parsed, candidate, source
        except Exception as exc:
            last_error = exc

    raise ValueError("No complete JSON object found") from last_error


def _prepare_json_candidate(text: str) -> tuple[str, str, str]:
    cleaned = text.strip()
    _, extracted, extraction_method = _extract_strategy_json(text)
    return cleaned, extracted, extraction_method


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


def parse_strategy_response(text: str) -> dict:
    parsed, _, _ = _extract_strategy_json(text)
    extra_top_level_keys = set(parsed.keys()) - TOP_LEVEL_KEYS
    if extra_top_level_keys:
        raise ValueError(f"Unexpected top-level keys: {sorted(extra_top_level_keys)}")

    business_type = _normalize_text(parsed.get("business_type"), "other").lower()
    if business_type not in ALLOWED_BUSINESS_TYPES:
        business_type = "other"

    category_tags_raw = parsed.get("category_tags")
    if not isinstance(category_tags_raw, list):
        raise ValueError("category_tags must be a list")
    category_tags = [_normalize_text(tag) for tag in category_tags_raw if _normalize_text(tag)]

    report = parsed.get("report")
    if not isinstance(report, dict):
        raise ValueError("report is required")
    extra_report_keys = set(report.keys()) - REPORT_KEYS
    if extra_report_keys:
        raise ValueError(f"Unexpected report keys: {sorted(extra_report_keys)}")

    normalized_report: dict[str, Any] = {}

    for key in REPORT_BODY_KEYS:
        section = report.get(key)
        if not isinstance(section, dict):
            raise ValueError(f"report.{key} is required")
        extra_section_keys = set(section.keys()) - BODY_SECTION_KEYS
        if extra_section_keys:
            raise ValueError(f"Unexpected keys in report.{key}: {sorted(extra_section_keys)}")
        normalized_report[key] = {
            "title": _normalize_text(section.get("title")),
            "body": _normalize_text(section.get("body")),
        }
        if not normalized_report[key]["title"] or not normalized_report[key]["body"]:
            raise ValueError(f"report.{key} must include title and body")

    for key, expected_len in REPORT_ITEMS_KEYS:
        section = report.get(key)
        if not isinstance(section, dict):
            raise ValueError(f"report.{key} is required")
        extra_section_keys = set(section.keys()) - ITEM_SECTION_KEYS
        if extra_section_keys:
            raise ValueError(f"Unexpected keys in report.{key}: {sorted(extra_section_keys)}")
        normalized_report[key] = {
            "title": _normalize_text(section.get("title")),
            "items": _normalize_items(section.get("items"), expected_len),
        }
        if not normalized_report[key]["title"]:
            raise ValueError(f"report.{key}.title is required")

    ceo_brief = parsed.get("ceo_brief")
    if not isinstance(ceo_brief, dict):
        raise ValueError("ceo_brief is required")
    extra_ceo_brief_keys = set(ceo_brief.keys()) - CEO_BRIEF_KEYS
    if extra_ceo_brief_keys:
        raise ValueError(f"Unexpected ceo_brief keys: {sorted(extra_ceo_brief_keys)}")

    normalized: StrategyReport = {
        "strategy_summary": _normalize_text(parsed.get("strategy_summary")),
        "business_type": business_type,  # type: ignore[typeddict-item]
        "category_tags": category_tags,
        "report": normalized_report,  # type: ignore[typeddict-item]
        "ceo_brief": {
            "headline": _normalize_text(ceo_brief.get("headline")),
            "approval_note": _normalize_text(ceo_brief.get("approval_note")),
        },
    }

    if not normalized["strategy_summary"]:
        raise ValueError("strategy_summary is required")
    if not normalized["ceo_brief"]["headline"] or not normalized["ceo_brief"]["approval_note"]:
        raise ValueError("ceo_brief fields are required")

    return normalized


async def repair_strategy_response(malformed_output: str, *, max_tokens: int = FALLBACK_STRATEGY_MAX_TOKENS) -> str:
    return await chat(
        "strategy",
        [
            {"role": "system", "content": "You repair malformed strategy JSON outputs."},
            {"role": "user", "content": REPAIR_PROMPT.format(malformed_output=malformed_output)},
        ],
        max_tokens=max_tokens,
    )


async def repair_json_with_llm(malformed_output: str, *, max_tokens: int = FALLBACK_STRATEGY_MAX_TOKENS) -> str:
    return await repair_strategy_response(malformed_output, max_tokens=max_tokens)


async def parse_or_repair_strategy_output(
    raw_output: str,
    *,
    is_revision: bool,
    project_id: str,
    run_index: int,
    log: AgentLogger,
    repair_max_tokens: int = FALLBACK_STRATEGY_MAX_TOKENS,
) -> tuple[dict, dict[str, Any]]:
    mode = "revision" if is_revision else "initial"
    debug_payload: dict[str, Any] = {
        "mode": mode,
        "run_index": run_index,
        "raw_llm_output": raw_output,
        "cleaned_output": None,
        "extracted_json_substring": None,
        "json_extraction_method": None,
        "repair_prompt_input": None,
        "repair_output": None,
    }

    try:
        cleaned_output, extracted_json, extraction_method = _prepare_json_candidate(raw_output)
        debug_payload["cleaned_output"] = cleaned_output
        debug_payload["extracted_json_substring"] = extracted_json
        debug_payload["json_extraction_method"] = extraction_method
        parsed = parse_strategy_response(raw_output)
        logger.info(
            "[strategy] %s parse success project_id=%s run_index=%s cleaned_len=%d extracted_len=%d method=%s",
            mode,
            project_id,
            run_index,
            len(cleaned_output),
            len(extracted_json),
            extraction_method,
        )
        return parsed, debug_payload
    except Exception as parse_exc:
        await log.info("Alex: 전략 보고서 형식을 정리하는 중입니다. JSON 구조를 복구합니다.")
        logger.error(
            "[strategy] %s parse failed project_id=%s run_index=%s error=%s raw_output=%s",
            mode,
            project_id,
            run_index,
            parse_exc,
            raw_output,
        )
        try:
            cleaned_output, extracted_json, extraction_method = _prepare_json_candidate(raw_output)
            debug_payload["cleaned_output"] = cleaned_output
            debug_payload["extracted_json_substring"] = extracted_json
            debug_payload["json_extraction_method"] = extraction_method
        except Exception as prep_exc:
            logger.warning(
                "[strategy] %s candidate prep failed project_id=%s run_index=%s error=%s",
                mode,
                project_id,
                run_index,
                prep_exc,
            )

        repair_prompt_input = REPAIR_PROMPT.format(malformed_output=raw_output)
        debug_payload["repair_prompt_input"] = repair_prompt_input
        logger.info(
            "[strategy] %s repair prompt input project_id=%s run_index=%s %s",
            mode,
            project_id,
            run_index,
            repair_prompt_input,
        )

        repair_output = await repair_json_with_llm(raw_output, max_tokens=repair_max_tokens)
        debug_payload["repair_output"] = repair_output
        logger.info(
            "[strategy] %s repair output project_id=%s run_index=%s %s",
            mode,
            project_id,
            run_index,
            repair_output,
        )

        cleaned_output, extracted_json, extraction_method = _prepare_json_candidate(repair_output)
        debug_payload["cleaned_output"] = cleaned_output
        debug_payload["extracted_json_substring"] = extracted_json
        debug_payload["json_extraction_method"] = extraction_method
        parsed = parse_strategy_response(repair_output)
        await log.success("Alex: 전략 보고서 JSON 복구가 완료되었습니다. CEO 검토를 기다립니다.")
        return parsed, debug_payload


async def _save_project(project_id: str, payload: dict) -> None:
    try:
        update_project(project_id, payload)
        logger.info("[strategy] Supabase 저장 완료 project_id=%s", project_id)
    except Exception as exc:
        logger.error("[strategy] Supabase 저장 실패 → 파이프라인 계속 진행 error=%s", str(exc))

async def strategy_node(state: ProjectState, config: dict[str, Any]) -> dict:
    project_id = state.get("project_id", "")
    retry_count = state.get("strategy_retry_count", 0)
    revision_count = state.get("revision_count", 0)
    run_index = get_next_strategy_run_index(project_id)
    model = get_model("strategy")
    prompt_version = "ceo_report_v3_revision_safe"
    raw_output = ""
    repair_attempted = False
    parser_debug: dict[str, Any] = {}
    prompt_debug: dict[str, Any] = {}
    is_revision = bool(state.get("ceo_feedback") or state.get("last_revised_items"))
    failure_context = "revision" if is_revision else "initial"

    logger.info(
        "[strategy] project_id=%s retry=%d revision_count=%d business_type=%s",
        project_id,
        retry_count,
        revision_count,
        state.get("business_type"),
    )

    if revision_count >= 3:
        await _save_project(
            project_id,
            {
                "status": "strategy_error",
                "error_message": "revision strategy failure: 전략 수정 3회 초과. 새 아이디어를 다시 입력해주세요.",
                "current_node": "strategy",
                "strategy_report_ready": False,
            },
        )
        insert_strategy_run(
            {
                "project_id": project_id,
                "run_index": run_index,
                "model_name": model,
                "prompt_version": prompt_version,
                "input_snapshot_json": {
                    "raw_idea": state.get("raw_idea"),
                    "business_type": state.get("business_type"),
                    "category_tags": state.get("category_tags", []),
                    "interview_answers": state.get("interview_answers", []),
                    "ceo_feedback": state.get("ceo_feedback"),
                    "last_revised_items": state.get("last_revised_items", []),
                },
                "raw_llm_output": raw_output,
                "parsed_output_json": None,
                "repair_attempted": False,
                "repair_raw_output": None,
                "success": False,
                "error_message": "revision strategy failure: 전략 수정 3회 초과. 새 아이디어를 다시 입력해주세요.",
            }
        )
        return {
            "error_message": "revision strategy failure: 전략 수정 3회 초과. 새 아이디어를 다시 입력해주세요.",
            "error_node": "strategy",
            "status": "strategy_error",
            "logs": ["Alex: Strategy revision limit reached. Please start over with a new idea."],
        }

    queue: asyncio.Queue = config["configurable"]["log_queue"]
    log = AgentLogger("Alex", queue, project_id=project_id)
    input_snapshot = {
        "raw_idea": state.get("raw_idea"),
        "business_type": state.get("business_type"),
        "category_tags": state.get("category_tags", []),
        "interview_answers": state.get("interview_answers", []),
        "ceo_feedback": state.get("ceo_feedback"),
        "last_revised_items": state.get("last_revised_items", []),
    }

    try:
        update_project(
            project_id,
            {
                "status": "strategy_processing",
                "current_node": "strategy",
                "strategy_report_ready": False,
                "error_message": None,
            },
        )
        insert_project_event(
            project_id,
            agent_name="Alex",
            event_type="strategy_started",
            message="전략 생성 작업을 시작합니다.",
            payload_json={"run_index": run_index, "revision_count": revision_count},
        )
    except Exception:
        logger.exception("[strategy] failed to persist strategy_started state")

    await log.info("Alex: 전략 분석을 시작합니다.")
    if is_revision:
        await log.info("CEO 수정 요청을 반영해 전략 보고서를 다시 정리하고 있습니다...")
    else:
        await log.info("인터뷰 답변을 바탕으로 전략 보고서를 작성하고 있습니다...")

    dummy_task: asyncio.Task | None = None
    try:
        dummy_task = asyncio.create_task(_dummy_log_loop(log))

        raw_output, prompt_debug = await _generate_strategy_output(
            state,
            project_id=project_id,
            run_index=run_index,
            model=model,
            prompt_version=prompt_version,
            log=log,
        )
        insert_project_event(
            project_id,
            agent_name="Alex",
            event_type="strategy_prompt_debug",
            message="전략 프롬프트 디버그 로그를 저장했습니다.",
            payload_json=prompt_debug,
        )
        logger.info("[strategy] LLM 응답 수신 len=%d project_id=%s", len(raw_output), project_id)

    except Exception as exc:
        if dummy_task:
            dummy_task.cancel()
            try:
                await dummy_task
            except asyncio.CancelledError:
                pass
        logger.error("[strategy] LLM 예외 project_id=%s error=%s", project_id, str(exc))
        error_code = "OPENROUTER_BUDGET_LIMIT" if is_budget_limit_error(exc) else "STRATEGY_LLM_ERROR"
        user_message = (
            "전략 생성이 현재 모델 예산 한도에 걸렸습니다. 다시 시도하거나 출력 길이를 줄여 주세요."
            if error_code == "OPENROUTER_BUDGET_LIMIT"
            else "전략 생성 중 일시적인 모델 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
        )
        if error_code == "OPENROUTER_BUDGET_LIMIT":
            await log.warn("Alex: 현재 모델 예산 한도로 인해 전략 생성이 일시 중단되었습니다.")
        else:
            await log.error("Alex: 전략 생성 중 일시적인 오류가 발생했습니다.")
        await _save_project(
            project_id,
            {
                "status": "strategy_error",
                "error_message": f"{failure_context} strategy failure [{error_code}]: {user_message}",
                "current_node": "strategy",
                "strategy_report_ready": False,
            },
        )
        insert_strategy_run(
            {
                "project_id": project_id,
                "run_index": run_index,
                "model_name": model,
                "prompt_version": prompt_version,
                "input_snapshot_json": {**input_snapshot, "prompt_debug": prompt_debug},
                "raw_llm_output": raw_output,
                "parsed_output_json": None,
                "repair_attempted": False,
                "repair_raw_output": None,
                "success": False,
                "error_message": f"{failure_context} strategy failure [{error_code}]: {exc}",
            }
        )
        insert_project_event(
            project_id,
            agent_name="Alex",
            event_type="strategy_failed",
            message="전략 생성 중 LLM 호출이 실패했습니다.",
            payload_json={
                "run_index": run_index,
                "error_message": str(exc),
                "mode": failure_context,
                "error_code": error_code,
                "user_message": user_message,
            },
        )
        return {
            "error_message": f"{failure_context} strategy failure [{error_code}]: {user_message}",
            "error_node": "strategy",
            "error_code": error_code,
            "user_message": user_message,
            "status": "strategy_error",
            "logs": ["Alex: 현재 전략 생성이 중단되었습니다. 설정 또는 예산 상태를 확인해주세요."],
        }

    if dummy_task:
        dummy_task.cancel()
        try:
            await dummy_task
        except asyncio.CancelledError:
            pass

    try:
        strategy_report, parser_debug = await parse_or_repair_strategy_output(
            raw_output,
            is_revision=is_revision,
            project_id=project_id,
            run_index=run_index,
            log=log,
            repair_max_tokens=FALLBACK_STRATEGY_MAX_TOKENS,
        )
        repair_attempted = parser_debug.get("repair_output") is not None
        last_revised_items = state.get("last_revised_items", []) or []
        insert_project_event(
            project_id,
            agent_name="Alex",
            event_type="strategy_parser_debug",
            message="전략 출력 파싱 디버그 로그를 저장했습니다.",
            payload_json=parser_debug,
        )
    except Exception as repair_exc:
        repair_attempted = True
        await log.error("전략 보고서 형식을 복구하지 못했습니다. 에러 상태로 전환합니다.")
        error_message = (
            f"revision strategy failure: Strategy report JSON parse error: {repair_exc}"
            if is_revision
            else f"initial strategy failure: Strategy report JSON parse error: {repair_exc}"
        )
        await _save_project(
            project_id,
            {
                "status": "strategy_error",
                "error_message": error_message,
                "current_node": "strategy",
                "strategy_report_ready": False,
            },
        )
        insert_strategy_run(
            {
                "project_id": project_id,
                "run_index": run_index,
                "model_name": model,
                "prompt_version": prompt_version,
                "input_snapshot_json": {**input_snapshot, "parser_debug": parser_debug, "prompt_debug": prompt_debug},
                "raw_llm_output": raw_output,
                "parsed_output_json": None,
                "repair_attempted": True,
                "repair_raw_output": parser_debug.get("repair_output"),
                "success": False,
                "error_message": error_message,
            }
        )
        insert_project_event(
            project_id,
            agent_name="Alex",
            event_type="strategy_parser_debug",
            message="전략 출력 파싱 디버그 로그를 저장했습니다.",
            payload_json=parser_debug,
        )
        insert_project_event(
            project_id,
            agent_name="Alex",
            event_type="strategy_failed",
            message="전략 보고서 JSON 파싱 및 복구에 실패했습니다.",
            payload_json={"run_index": run_index, "error_message": str(repair_exc), "mode": failure_context},
        )
        logger.error("[strategy] repair 실패 project_id=%s error=%s", project_id, str(repair_exc))
        return {
            "error_message": error_message,
            "error_node": "strategy",
            "error_code": "STRATEGY_JSON_PARSE_ERROR",
            "user_message": "전략 보고서 형식을 복구하지 못했습니다. 다시 시도해 주세요.",
            "status": "strategy_error",
            "current_node": "strategy",
            "logs": ["Alex: 전략 보고서 형식을 복구하지 못했습니다. 에러 상태로 전환합니다."],
        }

    await _save_project(
        project_id,
        {
            "strategy_summary": strategy_report["strategy_summary"],
            "business_type": strategy_report["business_type"],
            "category_tags": strategy_report["category_tags"],
            "strategy_report_json": strategy_report,
            "prd_json": strategy_report,
            "current_node": "strategy",
            "status": "awaiting_ceo_approval",
            "strategy_report_ready": True,
            "ceo_approval": "pending",
            "last_revised_items": last_revised_items,
            "revision_count": revision_count,
            "error_message": None,
        },
    )
    insert_strategy_run(
        {
            "project_id": project_id,
            "run_index": run_index,
            "model_name": model,
            "prompt_version": prompt_version,
            "input_snapshot_json": {**input_snapshot, "parser_debug": parser_debug, "prompt_debug": prompt_debug},
            "raw_llm_output": raw_output,
            "parsed_output_json": strategy_report,
            "repair_attempted": repair_attempted,
            "repair_raw_output": parser_debug.get("repair_output"),
            "success": True,
            "error_message": None,
        }
    )
    insert_project_event(
        project_id,
        agent_name="Alex",
        event_type="strategy_completed",
        message="CEO 브리핑용 전략 보고서가 준비되었습니다.",
        payload_json={"run_index": run_index, "business_type": strategy_report["business_type"]},
    )

    await log.success("전략 보고서가 준비되었습니다. 이제 CEO 브리핑을 검토할 수 있습니다.")

    return {
        "prd_json": strategy_report,
        "strategy_summary": strategy_report["strategy_summary"],
        "strategy_report_json": strategy_report,
        "business_type": strategy_report["business_type"],
        "category_tags": strategy_report["category_tags"],
        "ceo_feedback": None,
        "strategy_retry_count": retry_count + 1,
        "current_node": "approval_decision",
        "status": "awaiting_ceo_approval",
        "strategy_report_ready": True,
        "ceo_approval": "pending",
        "last_revised_items": last_revised_items,
        "revision_count": revision_count,
        "logs": [],
    }
