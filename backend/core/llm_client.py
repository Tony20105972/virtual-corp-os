"""
Virtual Corp OS — OpenRouter LLM 라우터

비용 절감 3개 레이어:
  1. 프롬프트 캐싱 (Anthropic cache_control) — prod Sonnet 적용, 시스템 프롬프트 90% 절감
  2. 노드별 max_tokens 엄격 제한 — 불필요한 토큰 낭비 방지
  3. 토큰 사용량 로깅 — Day 13 크레딧 차감 기반 데이터 확보

ENV=dev  → 저렴한 모델 (DeepSeek Free, MiniMax, Gemini Flash)
ENV=prod → Claude Sonnet 4.6 + 프롬프트 캐싱
"""

import logging
from dataclasses import dataclass
from openai import AsyncOpenAI
from core.settings import settings

logger = logging.getLogger(__name__)

DEFAULT_STRATEGY_MAX_TOKENS = 900
FALLBACK_STRATEGY_MAX_TOKENS = 600


# ── 노드별 모델 매핑 ─────────────────────────────────────────────────
MODELS: dict[str, str] = {
    "intake":   "anthropic/claude-haiku-4.5",
    "strategy": "anthropic/claude-haiku-4.5",
    "build":    "anthropic/claude-sonnet-4.6",
    "deploy":   "anthropic/claude-haiku-4.5",
}

# ── 노드별 max_tokens 상한 (절대 초과 금지) ──────────────────────────
MAX_TOKENS: dict[str, int] = {
    "intake":   1000,   # MiniMax M2: reasoning 모델이라 thinking tokens 포함
    "strategy": DEFAULT_STRATEGY_MAX_TOKENS,
    "build":    4000,
    "deploy":   300,
}

# ── 캐싱 지원 모델 (Anthropic 공식 지원 모델만) ────────────────────────
CACHE_SUPPORTED_MODELS = {
    "anthropic/claude-sonnet-4.6",
    "anthropic/claude-haiku-4.5",
}

# ── 모델별 단가 (per 1M tokens, USD) ──────────────────────────────────
PRICE_PER_1M: dict[str, dict] = {
    "anthropic/claude-sonnet-4-6": {
        "input": 3.00, "output": 15.00,
        "cache_read": 0.30, "cache_write": 3.75,
    },
    "minimax/minimax-m2": {
        "input": 0.10, "output": 0.10,
        "cache_read": 0.10, "cache_write": 0.10,
    },
    "deepseek/deepseek-v3.2:free": {
        "input": 0.00, "output": 0.00,
        "cache_read": 0.00, "cache_write": 0.00,
    },
    "google/gemini-flash-1.5": {
        "input": 0.075, "output": 0.30,
        "cache_read": 0.075, "cache_write": 0.075,
    },
}


@dataclass
class TokenUsage:
    node:               str
    model:              str
    input_tokens:       int
    output_tokens:      int
    cache_read_tokens:  int
    cache_write_tokens: int
    estimated_cost_usd: float


# ── 클라이언트 싱글턴 ────────────────────────────────────────────────
_client: AsyncOpenAI | None = None

def get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        api_key = settings.OPENROUTER_API_KEY
        if not api_key:
            raise ValueError(
                "OPENROUTER_API_KEY가 설정되지 않았습니다. "
                ".env에 OPENROUTER_API_KEY=sk-or-v1-... 를 추가하세요."
            )
        _client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
        logger.info("[llm_client] OpenRouter client initialized")
    return _client


def get_model(node: str) -> str:
    model = MODELS.get(node, MODELS["intake"])
    logger.info("[llm_client] node=%s model=%s", node, model)
    return model


def get_max_tokens(node: str) -> int:
    return MAX_TOKENS.get(node, 500)


def is_budget_limit_error(err: Exception) -> bool:
    status_code = getattr(err, "status_code", None)
    code = getattr(err, "code", None)
    message = str(err).lower()

    if status_code == 402 or code == 402:
        return True

    body = getattr(err, "body", None)
    if isinstance(body, dict):
        error_obj = body.get("error", {})
        message = f"{message} {str(error_obj.get('message', '')).lower()} {str(error_obj.get('code', '')).lower()}"

    return "requires more credits" in message or "fewer max_tokens" in message


# ── OpenRouter 필수 헤더 ──────────────────────────────────────────────
OR_HEADERS = {
    "HTTP-Referer": "https://virtualcorp.os",
    "X-Title":      "Virtual Corp OS",
}


def _apply_prompt_cache(messages: list[dict], model: str) -> list[dict]:
    """
    Anthropic 모델 전용 프롬프트 캐싱.
    시스템 프롬프트에 cache_control: ephemeral 삽입 → 반복 호출 시 90% 절감.
    """
    if model not in CACHE_SUPPORTED_MODELS:
        return messages

    cached = []
    for msg in messages:
        if msg.get("role") == "system":
            content = msg["content"]
            if isinstance(content, list):
                new_content = []
                for i, block in enumerate(content):
                    if i == len(content) - 1 and block.get("type") == "text":
                        new_content.append({**block, "cache_control": {"type": "ephemeral"}})
                    else:
                        new_content.append(block)
                cached.append({**msg, "content": new_content})
            else:
                cached.append({
                    "role": "system",
                    "content": [{
                        "type":          "text",
                        "text":          content,
                        "cache_control": {"type": "ephemeral"},
                    }],
                })
        else:
            cached.append(msg)
    return cached


def _estimate_cost(
    model: str,
    input_tokens: int,
    output_tokens: int,
    cache_read_tokens: int = 0,
    cache_write_tokens: int = 0,
) -> float:
    price = PRICE_PER_1M.get(
        model,
        {"input": 0.5, "output": 1.5, "cache_read": 0.0, "cache_write": 0.0},
    )
    return round(
        input_tokens         * price["input"]        / 1_000_000
        + output_tokens      * price["output"]       / 1_000_000
        + cache_read_tokens  * price["cache_read"]   / 1_000_000
        + cache_write_tokens * price["cache_write"]  / 1_000_000,
        8,
    )


def _log_usage(usage, node: str, model: str) -> TokenUsage:
    input_t  = getattr(usage, "prompt_tokens", 0)
    output_t = getattr(usage, "completion_tokens", 0)

    cache_read_t = 0
    if hasattr(usage, "prompt_tokens_details") and usage.prompt_tokens_details:
        cache_read_t = getattr(usage.prompt_tokens_details, "cached_tokens", 0)

    cost = _estimate_cost(model, input_t, output_t, cache_read_t)

    logger.info(
        "[llm_client] node=%s model=%s in=%d out=%d cache_read=%d cost=$%.6f",
        node, model, input_t, output_t, cache_read_t, cost,
    )

    # TODO Day 13: Supabase token_usage 테이블 저장
    return TokenUsage(
        node=node, model=model,
        input_tokens=input_t, output_tokens=output_t,
        cache_read_tokens=cache_read_t, cache_write_tokens=0,
        estimated_cost_usd=cost,
    )


# ── 공개 API ─────────────────────────────────────────────────────────

async def chat(
    node: str,
    messages: list[dict],
    max_tokens: int | None = None,
) -> str:
    """라스트리밍 호출 → 완성된 텍스트 반환"""
    client     = get_client()
    model      = get_model(node)
    max_tok    = max_tokens or get_max_tokens(node)
    cached_msg = _apply_prompt_cache(messages, model)

    response = await client.chat.completions.create(
        model=model,
        messages=cached_msg,
        max_tokens=max_tok,
        stream=False,
        extra_headers=OR_HEADERS,
    )

    if response.usage:
        _log_usage(response.usage, node, model)

    return response.choices[0].message.content or ""


async def chat_stream(
    node: str,
    messages: list[dict],
    max_tokens: int | None = None,
):
    """
    스트리밍 호출 → async generator로 청크 yield.
    Day 8 Strategy PRD, Day 15 Build 코드 생성에서 사용.
    """
    client     = get_client()
    model      = get_model(node)
    max_tok    = max_tokens or get_max_tokens(node)
    cached_msg = _apply_prompt_cache(messages, model)

    stream = await client.chat.completions.create(
        model=model,
        messages=cached_msg,
        max_tokens=max_tok,
        stream=True,
        stream_options={"include_usage": True},
        extra_headers=OR_HEADERS,
    )

    async for chunk in stream:
        if chunk.usage:
            _log_usage(chunk.usage, node, model)

        delta = chunk.choices[0].delta.content if chunk.choices else None
        if delta:
            yield delta
