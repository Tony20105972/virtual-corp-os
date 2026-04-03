import json
import asyncio
import logging
from datetime import datetime
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

router = APIRouter()
logger = logging.getLogger(__name__)


# ── 더미 로그 (Day 8 LLM 연동 전까지 사용) ──────────────────────────────────
DUMMY_LOGS: dict[str, list[dict]] = {
    "intake": [
        {"from": "Alex",  "to": "ALL",   "message": "Idea received. Starting market analysis."},
        {"from": "Alex",  "to": "Jamie", "message": "PRD draft incoming. Stand by."},
    ],
    "strategy": [
        {"from": "Alex",  "to": "ALL",   "message": "Scanning competitor landscape..."},
        {"from": "Alex",  "to": "ALL",   "message": "Business canvas complete. Awaiting CEO approval."},
    ],
    "build": [
        {"from": "Jamie", "to": "ALL",   "message": "PRD received. Starting code generation."},
        {"from": "Jamie", "to": "Sam",   "message": "Build complete. Handing off to QA."},
    ],
    "deploy": [
        {"from": "Sam",   "to": "ALL",   "message": "Running deployment checks..."},
        {"from": "Sam",   "to": "ALL",   "message": "Live URL incoming. Almost there."},
    ],
}

NODE_ORDER = ["intake", "strategy", "build", "deploy"]


def sse(data: dict) -> str:
    """SSE 포맷으로 직렬화"""
    return f"data: {json.dumps(data)}\n\n"


def now_str() -> str:
    return datetime.now().strftime("%H:%M")


async def event_generator(project_id: str):
    """
    더미 이벤트를 순서대로 yield.
    Day 8에서 graph.astream_events()로 교체 예정.
    """
    try:
        yield sse({"type": "ping", "project_id": project_id})

        for node in NODE_ORDER:
            yield sse({"type": "node_update", "node": node, "status": "processing"})
            await asyncio.sleep(0.3)

            for log in DUMMY_LOGS.get(node, []):
                yield sse({
                    "type":      "log",
                    "from":      log["from"],
                    "to":        log["to"],
                    "message":   log["message"],
                    "timestamp": now_str(),
                })
                await asyncio.sleep(0.8)

            if node == "strategy":
                yield sse({"type": "interrupt", "interrupt_type": "strategy"})
                await asyncio.sleep(3)

            yield sse({"type": "node_update", "node": node, "status": "done"})
            await asyncio.sleep(0.3)

        yield sse({"type": "complete", "payload": {"message": "All agents done."}})

    except asyncio.CancelledError:
        logger.info("[stream] client disconnected project_id=%s", project_id)


@router.get("/stream/{project_id}")
async def stream(project_id: str):
    return StreamingResponse(
        event_generator(project_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control":     "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
