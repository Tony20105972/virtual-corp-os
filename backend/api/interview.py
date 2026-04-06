"""
POST /interview/questions — AI 인터뷰 질문 3개 생성 (MiniMax M2)
"""

import json
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.llm_client import chat

router = APIRouter()
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are Alex, a sharp strategy consultant at Virtual Corp OS.
Generate exactly 3 short, incisive interview questions to clarify a business idea.

Rules:
- Each question: max 15 words
- Cover 3 angles: customer, core problem, differentiation
- Return ONLY a valid JSON array of 3 strings
- No preamble, no explanation, no markdown

Example output:
["Who is your primary customer?", "What problem do they face daily?", "How are you different from existing solutions?"]"""

FALLBACK_QUESTIONS = [
    "Who is your primary target customer?",
    "What core problem are you solving for them?",
    "What makes your solution different from existing ones?",
]


class QuestionRequest(BaseModel):
    idea: str


class QuestionResponse(BaseModel):
    questions: list[str]


@router.post("/interview/questions", response_model=QuestionResponse)
async def generate_questions(body: QuestionRequest):
    if not body.idea.strip():
        raise HTTPException(status_code=400, detail="idea 필드가 비어있습니다.")

    logger.info("[interview] idea=%s", body.idea[:80])

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": f"Business idea: {body.idea}\n\nGenerate 3 questions."},
    ]

    raw = ""
    try:
        raw = await chat("intake", messages)

        if not raw:
            raise ValueError("LLM이 빈 응답을 반환했습니다.")

        # 마크다운 펜스 제거 후 JSON 파싱
        clean = raw.strip().replace("```json", "").replace("```", "").strip()
        questions = json.loads(clean)

        if not isinstance(questions, list) or len(questions) != 3:
            raise ValueError(f"질문 3개 필요, 받은 값: {questions}")

        return QuestionResponse(questions=questions)

    except (json.JSONDecodeError, ValueError) as e:
        logger.error("[interview] 파싱 실패: %s | raw=%s", str(e), raw[:200])
        # 500 절대 금지 — 폴백 반환
        return QuestionResponse(questions=FALLBACK_QUESTIONS)
