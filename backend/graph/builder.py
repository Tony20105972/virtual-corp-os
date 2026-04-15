import os
import logging
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from graph.state import ProjectState
from agents.intake import intake_node
from agents.strategy import strategy_node
from agents.build import build_node
from agents.deploy import deploy_node
from graph.nodes.approval_router import approval_decision_router

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────
# Checkpointer 추상화
# ENV=dev  → MemorySaver
# ENV=prod → PostgresSaver (Supabase), 실패 시 MemorySaver 폴백
# ──────────────────────────────────────────
def get_checkpointer():
    env = os.getenv("ENV", "dev")
    if env == "dev":
        return MemorySaver()

    try:
        from langgraph.checkpoint.postgres import PostgresSaver
        db_url = os.getenv("SUPABASE_DB_URL")
        if not db_url:
            raise ValueError("SUPABASE_DB_URL 환경변수가 설정되지 않았습니다.")
        checkpointer = PostgresSaver.from_conn_string(db_url)
        checkpointer.setup()   # checkpoints 테이블 자동 생성
        logger.info("[checkpointer] PostgresSaver 초기화 완료")
        return checkpointer
    except Exception as e:
        logger.error("[checkpointer] Postgres 연결 실패: %s", str(e))
        logger.warning("[checkpointer] MemorySaver로 폴백합니다.")
        return MemorySaver()


# ──────────────────────────────────────────
# 완료 / 에러 노드 (인라인 stub)
# ──────────────────────────────────────────
async def complete_node(state: ProjectState) -> dict:
    try:
        logger.info("[complete] project_id=%s", state.get("project_id"))
        return {
            "current_node": "live",
            "status": "live",
            "logs": [f"Sam: 배포 완료! 🚀 {state.get('deploy_url', '')}"],
        }
    except Exception as e:
        logger.error("[complete] project_id=%s error=%s", state.get("project_id"), str(e))
        return {
            "error_message": str(e),
            "error_node": "complete",
            "logs": ["Sam: 오류가 발생했습니다. 지원팀에 전달됩니다."],
        }


async def error_node(state: ProjectState) -> dict:
    try:
        msg = state.get("error_message", "알 수 없는 오류")
        node = state.get("error_node", "unknown")
        logger.error("[error] project_id=%s node=%s msg=%s", state.get("project_id"), node, msg)
        return {
            "current_node": "error",
            "logs": [f"System: '{node}' 노드에서 오류가 발생했습니다 — {msg}"],
        }
    except Exception as e:
        logger.error("[error_node] project_id=%s error=%s", state.get("project_id"), str(e))
        return {
            "error_message": str(e),
            "error_node": "error",
            "logs": ["System: 치명적인 오류가 발생했습니다."],
        }


async def approval_decision_node(_: ProjectState) -> dict:
    return {}


# ──────────────────────────────────────────
# route_after_build — 유일한 조건부 라우터
# ──────────────────────────────────────────
def route_after_build(state: ProjectState) -> str:
    errors = state.get("build_errors", [])
    retry = state.get("build_retry_count", 0)
    if errors and retry < 3:
        return "build"    # 재시도
    if errors and retry >= 3:
        return "error"    # 재시도 한계 초과
    return "deploy"       # 성공 → deploy 직전 대기


# ──────────────────────────────────────────
# 그래프 컴파일
# ──────────────────────────────────────────
def compile_graph():
    builder = StateGraph(ProjectState)

    # 노드 등록
    builder.add_node("intake", intake_node)
    builder.add_node("strategy", strategy_node)
    builder.add_node("approval_decision", approval_decision_node)
    builder.add_node("build", build_node)
    builder.add_node("deploy", deploy_node)
    builder.add_node("complete", complete_node)
    builder.add_node("error", error_node)

    # 엣지
    builder.add_edge(START, "intake")
    builder.add_edge("intake", "strategy")
    builder.add_edge("strategy", "approval_decision")
    builder.add_conditional_edges(
        "approval_decision",
        approval_decision_router,
        {"build": "build", "strategy": "strategy"},
    )
    builder.add_conditional_edges(
        "build",
        route_after_build,
        {"build": "build", "error": "error", "deploy": "deploy"},
    )
    builder.add_edge("deploy", "complete")          # interrupt ②: deploy 직전 대기
    builder.add_edge("complete", END)
    builder.add_edge("error", END)

    return builder.compile(
        checkpointer=get_checkpointer(),
        interrupt_before=["approval_decision", "deploy"],
    )


# 싱글톤 — 모듈 로드 시 1회만 컴파일
_graph = None


def get_graph():
    global _graph
    if _graph is None:
        _graph = compile_graph()
        logger.info("[builder] graph compiled")
    return _graph
