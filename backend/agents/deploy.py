import logging
from graph.state import ProjectState
from core.project_repository import insert_deployment, insert_project_event, update_project

logger = logging.getLogger(__name__)

# Day 17: Vercel API 자동 배포 연동으로 교체


async def deploy_node(state: ProjectState) -> dict:
    try:
        project_id = state.get("project_id", "")
        github_repo = state.get("github_repo", "")

        logger.info("[deploy] project_id=%s repo=%s", project_id, github_repo)

        # ── Day 2 stub: 더미 Vercel 배포 결과 ─────────────────────
        dummy_deploy_url = f"https://{project_id[:8]}.vercel.app"
        # ───────────────────────────────────────────────────────────

        try:
            update_project(
                project_id,
                {
                    "status": "deploying",
                    "current_node": "deploy",
                    "error_message": None,
                },
            )
            insert_project_event(
                project_id,
                agent_name="Sam",
                event_type="deploy_started",
                message="Vercel 배포를 시작합니다.",
                payload_json={"github_repo": github_repo},
            )
            update_project(
                project_id,
                {
                    "status": "live",
                    "current_node": "live",
                    "deploy_url": dummy_deploy_url,
                },
            )
            insert_deployment(
                project_id,
                provider="vercel",
                deployment_url=dummy_deploy_url,
                status="live",
                build_log_json={"github_repo": github_repo},
            )
            insert_project_event(
                project_id,
                agent_name="Sam",
                event_type="deploy_completed",
                message="배포가 완료되어 서비스가 라이브 상태가 되었습니다.",
                payload_json={"deployment_url": dummy_deploy_url},
            )
        except Exception as exc:
            logger.warning("[deploy] status sync failed project_id=%s error=%s", project_id, exc)

        return {
            "deploy_url": dummy_deploy_url,
            "status": "live",
            "current_node": "live",
            "logs": [
                "Sam: Vercel 배포를 시작합니다...",
                f"Sam: 빌드 완료 ✓ → {dummy_deploy_url}",
                f"Sam: 라이브 URL → {dummy_deploy_url}",
            ],
        }

    except Exception as e:
        logger.error("[deploy] project_id=%s error=%s", state.get("project_id"), str(e))
        if state.get("project_id"):
            try:
                update_project(
                    state["project_id"],
                    {
                        "status": "deploy_error",
                        "current_node": "deploy",
                        "error_message": str(e),
                    },
                )
                insert_project_event(
                    state["project_id"],
                    agent_name="Sam",
                    event_type="deploy_failed",
                    message="배포에 실패했습니다.",
                    payload_json={"error_message": str(e)},
                )
            except Exception:
                logger.exception("[deploy] failed to persist deploy_error state")
        return {
            "error_message": str(e),
            "error_node": "deploy",
            "status": "deploy_error",
            "logs": ["Sam: 오류가 발생했습니다. 지원팀에 전달됩니다."],
        }
