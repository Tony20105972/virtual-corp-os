import logging
from graph.state import ProjectState

logger = logging.getLogger(__name__)

# Day 17: Vercel API 자동 배포 연동으로 교체


async def deploy_node(state: ProjectState) -> dict:
    try:
        project_id = state.get("project_id", "")
        github_repo = state.get("github_repo", "")

        logger.info("[deploy] project_id=%s repo=%s", project_id, github_repo)

        # ── Day 2 stub: 더미 Vercel 배포 결과 ─────────────────────
        dummy_deploy_url = f"https://{project_id[:8]}.vercel.app"
        dummy_preview_url = f"https://{project_id[:8]}-preview.vercel.app"
        dummy_vercel_project_id = f"prj_{project_id[:12]}"
        # ───────────────────────────────────────────────────────────

        return {
            "deploy_url": dummy_deploy_url,
            "preview_url": dummy_preview_url,
            "vercel_project_id": dummy_vercel_project_id,
            "current_node": "complete",
            "logs": [
                "Sam: Vercel 배포를 시작합니다...",
                f"Sam: 빌드 완료 ✓ → {dummy_deploy_url}",
                f"Sam: 프리뷰 URL → {dummy_preview_url}",
            ],
        }

    except Exception as e:
        logger.error("[deploy] project_id=%s error=%s", state.get("project_id"), str(e))
        return {
            "error_message": str(e),
            "error_node": "deploy",
            "logs": ["Sam: 오류가 발생했습니다. 지원팀에 전달됩니다."],
        }
