import json
import asyncio
import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from core.queue_store import project_queues

router = APIRouter()
logger = logging.getLogger(__name__)


def sse(data: dict) -> str:
    """SSE 포맷으로 직렬화"""
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.get("/stream/{project_id}")
async def stream(project_id: str):
    """
    project_queues[project_id] 에서 이벤트를 꺼내 SSE로 전송.
    AgentLogger 가 put_nowait 한 로그를 실시간으로 클라이언트에 전달.
    """
    queue = project_queues.get(project_id)
    if not queue:
        raise HTTPException(status_code=404, detail="project not found")

    async def event_generator():
        try:
            while True:
                item = await queue.get()
                yield sse(item)
                if item.get("type") == "complete":
                    break
        except asyncio.CancelledError:
            logger.info("[stream] client disconnected project_id=%s", project_id)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
