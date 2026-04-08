"""
Virtual Corp OS — 프로젝트 레벨 asyncio.Queue 저장소
main.py (쓰기) 와 api/stream.py (읽기) 가 동일 dict를 참조하도록
순환 import 없이 공유하는 단순 모듈.
"""
import asyncio

# { project_id: asyncio.Queue }
project_queues: dict[str, asyncio.Queue] = {}
