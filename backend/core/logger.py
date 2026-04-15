"""
Virtual Corp OS — AgentLogger
경량 에이전트 로그 유틸. 외부 라이브러리 의존 없음.
Jamie · Sam · Aria 동일 클래스 재사용.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Literal

from core.project_repository import insert_project_event

_stdlib_logger = logging.getLogger(__name__)

KST = timezone(timedelta(hours=9))
LogLevel = Literal["info", "success", "warn", "error"]


class AgentLogger:
    """
    사용법:
        log = AgentLogger("Alex", queue)
        await log.info("Analyzing market landscape...")
        await log.success("Business canvas complete ✓")
    """

    def __init__(self, agent_name: str, queue: asyncio.Queue, project_id: str | None = None) -> None:
        self.agent_name = agent_name
        self._queue = queue
        self.project_id = project_id

    # ── public API ──────────────────────────────────────────────────────────
    async def info(self, message: str) -> None:
        await self._emit("info", message)

    async def success(self, message: str) -> None:
        await self._emit("success", message)

    async def warn(self, message: str) -> None:
        await self._emit("warn", message)

    async def error(self, message: str) -> None:
        await self._emit("error", message)

    # ── internal ────────────────────────────────────────────────────────────
    async def _emit(self, level: LogLevel, message: str) -> None:
        ts = datetime.now(KST).strftime("%H:%M:%S")
        payload = {
            "type": "log",
            "agent": self.agent_name,
            "level": level,
            "message": message,
            "timestamp": ts,
        }
        try:
            self._queue.put_nowait(payload)
        except asyncio.QueueFull:
            # 큐가 꽉 찬 경우 조용히 스킵 (침묵보다 낫지 않음)
            _stdlib_logger.debug(
                "AgentLogger queue full — log skipped: %s", message
            )
        if self.project_id:
            try:
                insert_project_event(
                    self.project_id,
                    agent_name=self.agent_name,
                    event_type=f"log_{level}",
                    message=message,
                    payload_json={"level": level, "timestamp": ts},
                )
            except Exception:
                _stdlib_logger.exception("AgentLogger failed to persist project_event")
