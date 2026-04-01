import logging
from graph.state import ProjectState

logger = logging.getLogger(__name__)

# Day 15: Claude Sonnet 코드 생성 + GitHub push로 교체


async def build_node(state: ProjectState) -> dict:
    try:
        project_id = state.get("project_id", "")
        prd_json = state.get("prd_json", {})

        logger.info(
            "[build] project_id=%s retry=%d",
            project_id,
            state.get("build_retry_count", 0),
        )

        # ── Day 2 stub: 더미 코드 파일 및 GitHub 레포 ─────────────
        dummy_code_files: dict = {
            "app/page.tsx": "// Day 15에서 실제 코드로 교체됩니다.\nexport default function Home() { return <div>Hello Ghost Founder</div>; }",
            "app/layout.tsx": "// Day 15에서 실제 코드로 교체됩니다.\nexport default function Layout({ children }) { return <html><body>{children}</body></html>; }",
            "package.json": '{"name": "ghost-founder-app", "version": "0.1.0"}',
        }
        dummy_github_repo = f"https://github.com/ghost-founder/{project_id[:8]}"
        # ───────────────────────────────────────────────────────────

        return {
            "code_files": dummy_code_files,
            "github_repo": dummy_github_repo,
            "build_errors": [],                                # 성공 시 반드시 빈 리스트
            "build_retry_count": state.get("build_retry_count", 0) + 1,
            "current_node": "deploy",
            "logs": [
                "Jamie: 코드 생성을 시작합니다...",
                f"Jamie: {len(dummy_code_files)}개 파일 생성 완료 ✓",
                f"Jamie: GitHub 레포 생성 완료 → {dummy_github_repo}",
            ],
        }

    except Exception as e:
        logger.error("[build] project_id=%s error=%s", state.get("project_id"), str(e))
        return {
            "error_message": str(e),
            "error_node": "build",
            "logs": ["Jamie: 오류가 발생했습니다. 지원팀에 전달됩니다."],
        }
