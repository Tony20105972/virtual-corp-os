from graph.state import ProjectState


def payment_decision_router(state: ProjectState) -> str:
    """결제 확인이 끝났는지 여부에 따라 build 또는 승인 대기로 분기한다."""
    if state.get("payment_done"):
        return "deploy"
    return "error"
