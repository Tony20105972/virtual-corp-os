import json
import asyncio

from core.llm_client import FALLBACK_STRATEGY_MAX_TOKENS, is_budget_limit_error
from agents.strategy import (
    _extract_strategy_json,
    _build_prompt,
    _generate_strategy_output,
    extract_first_json_object,
    parse_or_repair_strategy_output,
    parse_strategy_response,
    strategy_node,
    strip_code_fences,
)


def test_strip_code_fences_removes_markdown_wrapper():
    raw = """```json
{"hello":"world"}
```"""
    assert strip_code_fences(raw) == '{"hello":"world"}'


def test_extract_first_json_object_ignores_surrounding_text():
    raw = 'preface {"a":{"nested":true},"b":"text"} trailing'
    assert extract_first_json_object(raw) == '{"a":{"nested":true},"b":"text"}'


def test_parse_strategy_response_normalizes_ceo_report_schema():
    payload = {
        "strategy_summary": "프리랜서를 위한 시간 기록 SaaS",
        "business_type": "saas",
        "category_tags": ["freelancer", "time-tracking"],
        "report": {
            "problem": {"title": "기록 누락", "body": "수작업으로 시간을 적다 보면 청구 누락이 잦다."},
            "customer": {"title": "프리랜서", "body": "프로젝트 단위로 청구하는 1인 프리랜서가 핵심 고객이다."},
            "solution": {"title": "자동 기록", "body": "작업 시작과 종료를 쉽게 기록하고 프로젝트별 시간을 자동 집계한다."},
            "why_now": {"title": "원격 계약 확대", "body": "원격 프로젝트와 외주 비중이 커지며 증빙 가능한 시간 관리 수요가 커졌다."},
            "business_model": {"title": "구독 모델", "body": "월 구독으로 고급 리포트와 인보이스 기능을 판매한다."},
            "mvp_scope": {"title": "추천 MVP 범위", "items": ["타이머", "프로젝트별 집계", "인보이스 초안"]},
            "differentiators": {"title": "핵심 차별점", "items": ["청구 흐름 연결", "간단한 입력 UX", "프리랜서 중심 리포트"]},
            "risks": {"title": "주요 리스크", "items": ["습관 형성 실패 가능성", "무료 대안 대비 차별화 필요"]},
            "go_to_market": {"title": "초기 진입 전략", "body": "프리랜서 커뮤니티와 뉴스레터 제휴로 첫 사용자를 모은다."},
        },
        "ceo_brief": {
            "headline": "청구 누락을 막는 프리랜서용 타임 트래킹",
            "approval_note": "핵심 루프가 명확해 MVP 착수 판단이 가능하다.",
        },
    }

    parsed = parse_strategy_response(json.dumps(payload, ensure_ascii=False))

    assert parsed["business_type"] == "saas"
    assert parsed["strategy_summary"] == "프리랜서를 위한 시간 기록 SaaS"
    assert parsed["report"]["mvp_scope"]["items"] == ["타이머", "프로젝트별 집계", "인보이스 초안"]
    assert parsed["report"]["risks"]["items"] == ["습관 형성 실패 가능성", "무료 대안 대비 차별화 필요"]
    assert parsed["ceo_brief"]["headline"] == "청구 누락을 막는 프리랜서용 타임 트래킹"


def test_extract_strategy_json_accepts_raw_json():
    payload = '{"strategy_summary":"요약","business_type":"saas","category_tags":[],"report":{"problem":{"title":"문제","body":"문제"},"customer":{"title":"고객","body":"고객"},"solution":{"title":"해결","body":"해결"},"why_now":{"title":"지금","body":"지금"},"business_model":{"title":"BM","body":"BM"},"mvp_scope":{"title":"MVP","items":["a","b","c"]},"differentiators":{"title":"차별점","items":["a","b","c"]},"risks":{"title":"리스크","items":["a","b"]},"go_to_market":{"title":"GTM","body":"GTM"}},"ceo_brief":{"headline":"헤드라인","approval_note":"노트"}}'
    _, extracted, method = _extract_strategy_json(payload)
    assert extracted == payload
    assert method == "raw"


def test_extract_strategy_json_accepts_json_code_block():
    payload = """```json
{"strategy_summary":"요약","business_type":"saas","category_tags":[],"report":{"problem":{"title":"문제","body":"문제"},"customer":{"title":"고객","body":"고객"},"solution":{"title":"해결","body":"해결"},"why_now":{"title":"지금","body":"지금"},"business_model":{"title":"BM","body":"BM"},"mvp_scope":{"title":"MVP","items":["a","b","c"]},"differentiators":{"title":"차별점","items":["a","b","c"]},"risks":{"title":"리스크","items":["a","b"]},"go_to_market":{"title":"GTM","body":"GTM"}},"ceo_brief":{"headline":"헤드라인","approval_note":"노트"}}
```"""
    _, _, method = _extract_strategy_json(payload)
    assert method == "code_block"


def test_extract_strategy_json_accepts_mixed_text_and_json():
    payload = '설명문이 먼저 옵니다.\n{"strategy_summary":"요약","business_type":"saas","category_tags":[],"report":{"problem":{"title":"문제","body":"문제"},"customer":{"title":"고객","body":"고객"},"solution":{"title":"해결","body":"해결"},"why_now":{"title":"지금","body":"지금"},"business_model":{"title":"BM","body":"BM"},"mvp_scope":{"title":"MVP","items":["a","b","c"]},"differentiators":{"title":"차별점","items":["a","b","c"]},"risks":{"title":"리스크","items":["a","b"]},"go_to_market":{"title":"GTM","body":"GTM"}},"ceo_brief":{"headline":"헤드라인","approval_note":"노트"}}\n감사합니다.'
    _, _, method = _extract_strategy_json(payload)
    assert method == "outer_braces"


def test_parse_strategy_response_rejects_extra_keys():
    payload = {
        "strategy_summary": "온라인 북클럽",
        "business_type": "community",
        "category_tags": ["books"],
        "report": {
            "problem": {"title": "문제", "body": "문제 설명"},
            "customer": {"title": "고객", "body": "고객 설명"},
            "solution": {"title": "해결", "body": "해결 설명"},
            "why_now": {"title": "타이밍", "body": "타이밍 설명"},
            "business_model": {"title": "수익", "body": "수익 설명"},
            "mvp_scope": {"title": "MVP", "items": ["a", "b", "c"]},
            "differentiators": {"title": "차별점", "items": ["a", "b", "c"]},
            "risks": {"title": "리스크", "items": ["a", "b"]},
            "go_to_market": {"title": "GTM", "body": "GTM 설명"},
        },
        "ceo_brief": {"headline": "헤드라인", "approval_note": "승인 메모"},
        "extra": "not allowed",
    }

    try:
        parse_strategy_response(json.dumps(payload, ensure_ascii=False))
        assert False, "Expected parse_strategy_response to reject extra keys"
    except ValueError as exc:
        assert "Unexpected top-level keys" in str(exc)


def test_build_prompt_diff_between_initial_and_revision():
    base_state = {
        "raw_idea": "Time tracking for freelancers",
        "business_type": "saas",
        "category_tags": ["freelancer", "time-tracking"],
        "interview_answers": [
            {"title": "누가 쓰나요?", "answer": "청구 누락이 잦은 프리랜서"},
        ],
    }

    initial_prompt = _build_prompt(base_state)
    revision_prompt = _build_prompt(
        {
            **base_state,
            "strategy_report_json": {
                "strategy_summary": "초안",
                "business_type": "saas",
                "category_tags": ["freelancer"],
                "report": {
                    "problem": {"title": "문제", "body": "문제"},
                    "customer": {"title": "고객", "body": "고객"},
                    "solution": {"title": "해결", "body": "해결"},
                    "why_now": {"title": "지금", "body": "지금"},
                    "business_model": {"title": "BM", "body": "BM"},
                    "mvp_scope": {"title": "MVP", "items": ["a", "b", "c"]},
                    "differentiators": {"title": "차별점", "items": ["a", "b", "c"]},
                    "risks": {"title": "리스크", "items": ["a", "b"]},
                    "go_to_market": {"title": "GTM", "body": "GTM"},
                },
                "ceo_brief": {"headline": "초안", "approval_note": "초안"},
            },
            "ceo_feedback": "핵심 고객을 더 좁혀주세요.",
            "last_revised_items": ["customer", "business_model"],
        }
    )

    assert "Previous strategy report JSON" not in initial_prompt
    assert "CEO revision request:" not in initial_prompt
    assert "Previous strategy report JSON" in revision_prompt
    assert "CEO revision request:" in revision_prompt
    assert "Return the full final JSON object again from scratch." in revision_prompt


def test_parse_or_repair_strategy_output_repairs_once_then_succeeds(monkeypatch):
    valid_payload = {
        "strategy_summary": "프리랜서용 SaaS",
        "business_type": "saas",
        "category_tags": ["freelancer"],
        "report": {
            "problem": {"title": "문제", "body": "문제"},
            "customer": {"title": "고객", "body": "고객"},
            "solution": {"title": "해결", "body": "해결"},
            "why_now": {"title": "지금", "body": "지금"},
            "business_model": {"title": "BM", "body": "BM"},
            "mvp_scope": {"title": "MVP", "items": ["a", "b", "c"]},
            "differentiators": {"title": "차별점", "items": ["a", "b", "c"]},
            "risks": {"title": "리스크", "items": ["a", "b"]},
            "go_to_market": {"title": "GTM", "body": "GTM"},
        },
        "ceo_brief": {"headline": "헤드라인", "approval_note": "노트"},
    }

    class DummyLog:
        async def info(self, message: str):
            return None

        async def success(self, message: str):
            return None

    async def fake_repair(_: str, *, max_tokens: int = FALLBACK_STRATEGY_MAX_TOKENS) -> str:
        assert max_tokens == FALLBACK_STRATEGY_MAX_TOKENS
        return json.dumps(valid_payload, ensure_ascii=False)

    monkeypatch.setattr("agents.strategy.repair_json_with_llm", fake_repair)

    parsed, debug_payload = asyncio.run(
        parse_or_repair_strategy_output(
            '{"strategy_summary":"broken"',
            is_revision=True,
            project_id="project-1",
            run_index=2,
            log=DummyLog(),
        )
    )

    assert parsed["strategy_summary"] == "프리랜서용 SaaS"
    assert debug_payload["mode"] == "revision"
    assert debug_payload["repair_prompt_input"] is not None
    assert debug_payload["repair_output"] is not None


def test_parse_or_repair_strategy_output_recovers_truncated_json(monkeypatch):
    valid_payload = {
        "strategy_summary": "프리랜서용 SaaS",
        "business_type": "saas",
        "category_tags": ["freelancer"],
        "report": {
            "problem": {"title": "문제", "body": "문제"},
            "customer": {"title": "고객", "body": "고객"},
            "solution": {"title": "해결", "body": "해결"},
            "why_now": {"title": "지금", "body": "지금"},
            "business_model": {"title": "BM", "body": "BM"},
            "mvp_scope": {"title": "MVP", "items": ["a", "b", "c"]},
            "differentiators": {"title": "차별점", "items": ["a", "b", "c"]},
            "risks": {"title": "리스크", "items": ["a", "b"]},
            "go_to_market": {"title": "GTM", "body": "GTM"},
        },
        "ceo_brief": {"headline": "헤드라인", "approval_note": "노트"},
    }

    class DummyLog:
        async def info(self, message: str):
            return None

        async def success(self, message: str):
            return None

    async def fake_repair(_: str, *, max_tokens: int = FALLBACK_STRATEGY_MAX_TOKENS) -> str:
        return json.dumps(valid_payload, ensure_ascii=False)

    monkeypatch.setattr("agents.strategy.repair_json_with_llm", fake_repair)

    parsed, debug_payload = asyncio.run(
        parse_or_repair_strategy_output(
            '{"strategy_summary":"broken"',
            is_revision=False,
            project_id="project-1",
            run_index=1,
            log=DummyLog(),
        )
    )

    assert parsed["strategy_summary"] == "프리랜서용 SaaS"
    assert debug_payload["repair_output"] is not None


def test_is_budget_limit_error_detects_openrouter_402():
    class BudgetError(Exception):
        status_code = 402

    assert is_budget_limit_error(BudgetError("requires more credits and fewer max_tokens"))
    assert is_budget_limit_error(Exception("This request requires more credits, or fewer max_tokens."))
    assert not is_budget_limit_error(Exception("network timeout"))


def test_generate_strategy_output_retries_once_in_compact_mode(monkeypatch):
    calls: list[tuple[str, int]] = []

    async def fake_call(prompt_text: str, *, model: str, max_tokens: int) -> str:
        calls.append((prompt_text, max_tokens))
        if len(calls) == 1:
            err = Exception("This request requires more credits, or fewer max_tokens.")
            setattr(err, "status_code", 402)
            raise err
        return '{"strategy_summary":"ok","business_type":"saas","category_tags":["freelancer"],"report":{"problem":{"title":"문제","body":"문제"},"customer":{"title":"고객","body":"고객"},"solution":{"title":"해결","body":"해결"},"why_now":{"title":"지금","body":"지금"},"business_model":{"title":"BM","body":"BM"},"mvp_scope":{"title":"MVP","items":["a","b","c"]},"differentiators":{"title":"차별점","items":["a","b","c"]},"risks":{"title":"리스크","items":["a","b"]},"go_to_market":{"title":"GTM","body":"GTM"}},"ceo_brief":{"headline":"헤드라인","approval_note":"노트"}}'

    class DummyLog:
        async def warn(self, message: str):
            return None

        async def success(self, message: str):
            return None

    monkeypatch.setattr("agents.strategy._call_strategy_llm", fake_call)

    raw_output, prompt_debug = asyncio.run(
        _generate_strategy_output(
            {
                "raw_idea": "Idea",
                "business_type": "saas",
                "category_tags": ["freelancer"],
                "interview_answers": [],
                "ceo_feedback": None,
                "last_revised_items": [],
            },
            project_id="project-1",
            run_index=1,
            model="anthropic/claude-haiku-4.5",
            prompt_version="test",
            log=DummyLog(),
        )
    )

    assert raw_output
    assert len(calls) == 2
    assert calls[0][1] > calls[1][1]
    assert prompt_debug["mode"] == "compact"


def test_generate_strategy_output_raises_after_second_budget_failure(monkeypatch):
    async def fake_call(prompt_text: str, *, model: str, max_tokens: int) -> str:
        err = Exception("This request requires more credits, or fewer max_tokens.")
        setattr(err, "status_code", 402)
        raise err

    class DummyLog:
        async def warn(self, message: str):
            return None

        async def success(self, message: str):
            return None

    monkeypatch.setattr("agents.strategy._call_strategy_llm", fake_call)

    try:
        asyncio.run(
            _generate_strategy_output(
                {
                    "raw_idea": "Idea",
                    "business_type": "saas",
                    "category_tags": ["freelancer"],
                    "interview_answers": [],
                    "ceo_feedback": None,
                    "last_revised_items": [],
                },
                project_id="project-1",
                run_index=1,
                model="anthropic/claude-haiku-4.5",
                prompt_version="test",
                log=DummyLog(),
            )
        )
        assert False, "Expected second budget failure to bubble up"
    except Exception as exc:
        assert is_budget_limit_error(exc)


def test_strategy_node_returns_graceful_budget_failure(monkeypatch):
    async def fake_generate(*args, **kwargs):
        err = Exception("This request requires more credits, or fewer max_tokens.")
        setattr(err, "status_code", 402)
        raise err

    monkeypatch.setattr("agents.strategy._generate_strategy_output", fake_generate)
    monkeypatch.setattr("agents.strategy.update_project", lambda *args, **kwargs: None)
    monkeypatch.setattr("agents.strategy.insert_project_event", lambda *args, **kwargs: None)
    monkeypatch.setattr("agents.strategy.insert_strategy_run", lambda *args, **kwargs: None)
    monkeypatch.setattr("agents.strategy.get_next_strategy_run_index", lambda project_id: 1)

    result = asyncio.run(
        strategy_node(
            {
                "project_id": "project-1",
                "strategy_retry_count": 0,
                "revision_count": 0,
                "raw_idea": "Idea",
                "business_type": "saas",
                "category_tags": ["freelancer"],
                "interview_answers": [],
                "ceo_feedback": None,
                "last_revised_items": [],
            },
            {"configurable": {"log_queue": asyncio.Queue()}},
        )
    )

    assert result["status"] == "strategy_error"
    assert result["error_code"] == "OPENROUTER_BUDGET_LIMIT"
    assert "예산 한도" in result["user_message"]


def test_strategy_node_returns_graceful_parse_failure(monkeypatch):
    async def fake_generate(*args, **kwargs):
        return '{"strategy_summary":"broken"', {"mode": "default"}

    async def fake_parse(*args, **kwargs):
        raise ValueError("No complete JSON object found")

    monkeypatch.setattr("agents.strategy._generate_strategy_output", fake_generate)
    monkeypatch.setattr("agents.strategy.parse_or_repair_strategy_output", fake_parse)
    monkeypatch.setattr("agents.strategy.update_project", lambda *args, **kwargs: None)
    monkeypatch.setattr("agents.strategy.insert_project_event", lambda *args, **kwargs: None)
    monkeypatch.setattr("agents.strategy.insert_strategy_run", lambda *args, **kwargs: None)
    monkeypatch.setattr("agents.strategy.get_next_strategy_run_index", lambda project_id: 1)

    result = asyncio.run(
        strategy_node(
            {
                "project_id": "project-1",
                "strategy_retry_count": 0,
                "revision_count": 0,
                "raw_idea": "Idea",
                "business_type": "saas",
                "category_tags": ["freelancer"],
                "interview_answers": [],
                "ceo_feedback": None,
                "last_revised_items": [],
            },
            {"configurable": {"log_queue": asyncio.Queue()}},
        )
    )

    assert result["status"] == "strategy_error"
    assert result["current_node"] == "strategy"
    assert result["error_code"] == "STRATEGY_JSON_PARSE_ERROR"
    assert "복구하지 못했습니다" in result["user_message"]
