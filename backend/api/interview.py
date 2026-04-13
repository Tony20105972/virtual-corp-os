import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from agents.intake_question_generator import generate_interview_plan

router = APIRouter()
logger = logging.getLogger(__name__)


class QuestionRequest(BaseModel):
    idea: str


@router.post("/interview/questions")
async def generate_questions(body: QuestionRequest):
    if not body.idea.strip():
        raise HTTPException(status_code=400, detail="idea 필드가 비어있습니다.")

    logger.info("[interview] generate questions idea=%s", body.idea[:100])
    plan = generate_interview_plan(body.idea)
    return {
        "idea": body.idea,
        **plan,
    }
