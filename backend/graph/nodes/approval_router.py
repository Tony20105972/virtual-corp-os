from graph.state import ProjectState


def approval_decision_router(state: ProjectState) -> str:
    """CEO 승인 여부에 따라 다음 노드로 분기한다."""
    if state.get("ceo_approval") == "approved":
        return "build"
    if state.get("ceo_approval") == "revise":
        return "strategy"
    raise ValueError("ceo_approval must be approved or revise at this point")
