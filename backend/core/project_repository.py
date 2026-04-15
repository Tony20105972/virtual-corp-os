from __future__ import annotations

import logging
from typing import Any

from core.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


def _client():
    return get_supabase_client()


def get_project(project_id: str, columns: str = "*") -> dict | None:
    response = (
        _client()
        .table("projects")
        .select(columns)
        .eq("project_id", project_id)
        .limit(1)
        .execute()
    )
    rows = response.data or []
    return rows[0] if rows else None


def create_project(payload: dict[str, Any]) -> dict:
    response = _client().table("projects").insert(payload).execute()
    rows = response.data or []
    return rows[0] if rows else payload


def update_project(project_id: str, payload: dict[str, Any]) -> None:
    _client().table("projects").update(payload).eq("project_id", project_id).execute()


def insert_interview(
    project_id: str,
    *,
    business_type: str | None,
    category_tags: list[str] | None,
    question_set_json: Any,
    answers_json: Any,
) -> None:
    _client().table("project_interviews").insert(
        {
            "project_id": project_id,
            "business_type": business_type,
            "category_tags": category_tags or [],
            "question_set_json": question_set_json,
            "answers_json": answers_json,
        }
    ).execute()


def get_next_strategy_run_index(project_id: str) -> int:
    response = (
        _client()
        .table("project_strategy_runs")
        .select("run_index")
        .eq("project_id", project_id)
        .order("run_index", desc=True)
        .limit(1)
        .execute()
    )
    rows = response.data or []
    return int(rows[0]["run_index"]) + 1 if rows else 1


def insert_strategy_run(payload: dict[str, Any]) -> None:
    _client().table("project_strategy_runs").insert(payload).execute()


def insert_project_event(
    project_id: str,
    *,
    agent_name: str,
    event_type: str,
    message: str,
    payload_json: dict[str, Any] | None = None,
) -> None:
    _client().table("project_events").insert(
        {
            "project_id": project_id,
            "agent_name": agent_name,
            "event_type": event_type,
            "message": message,
            "payload_json": payload_json or {},
        }
    ).execute()


def insert_payment(
    project_id: str,
    *,
    provider: str,
    session_id: str,
    amount: float | None = None,
    currency: str = "USD",
    status: str,
    payload_json: dict[str, Any] | None = None,
) -> None:
    _client().table("project_payments").insert(
        {
            "project_id": project_id,
            "provider": provider,
            "session_id": session_id,
            "amount": amount,
            "currency": currency,
            "status": status,
            "payload_json": payload_json or {},
        }
    ).execute()


def insert_deployment(
    project_id: str,
    *,
    provider: str,
    deployment_url: str,
    status: str,
    build_log_json: dict[str, Any] | None = None,
) -> None:
    _client().table("project_deployments").insert(
        {
            "project_id": project_id,
            "provider": provider,
            "deployment_url": deployment_url,
            "status": status,
            "build_log_json": build_log_json or {},
        }
    ).execute()
