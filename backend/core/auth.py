from __future__ import annotations

import logging
import uuid
from typing import Any

import jwt
from fastapi import HTTPException, Request

from core.settings import settings
from core.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)

_runtime_dev_user_id: str | None = None


def _is_valid_uuid(value: str | None) -> bool:
    if not value or not isinstance(value, str):
        return False
    try:
        uuid.UUID(value)
        return True
    except (ValueError, TypeError):
        return False


def _log_user_resolution(prefix: str, user_id: str, detail: str) -> None:
    message = f"{prefix} {detail}: {user_id}"
    print(message)
    logger.info(message)
    print(f"[RUN] using user_id: {user_id}")
    logger.info("[RUN] using user_id: %s", user_id)


def _extract_user_id_from_request(request: Request) -> str | None:
    state_user_id = getattr(request.state, "user_id", None)
    if _is_valid_uuid(state_user_id):
        return str(state_user_id)

    auth_user = getattr(request.state, "user", None)
    auth_user_id = getattr(auth_user, "id", None) if auth_user else None
    if _is_valid_uuid(auth_user_id):
        return str(auth_user_id)

    header_user_id = request.headers.get("x-user-id")
    if _is_valid_uuid(header_user_id):
        return header_user_id

    auth_header = request.headers.get("authorization", "")
    if auth_header.lower().startswith("bearer "):
        token = auth_header.split(" ", 1)[1].strip()
        if token:
            try:
                payload = jwt.decode(
                    token,
                    options={"verify_signature": False, "verify_aud": False},
                    algorithms=["HS256", "RS256"],
                )
                subject = payload.get("sub")
                if _is_valid_uuid(subject):
                    return str(subject)
            except Exception as exc:
                logger.warning("[AUTH] failed to decode bearer token: %s", exc)

    return None


def _ensure_auth_user_exists(user_id: str, source: str) -> str:
    client = get_supabase_client()
    try:
        client.auth.admin.get_user_by_id(user_id)
        return user_id
    except Exception as exc:
        logger.warning("[DEV] auth user lookup failed for %s (%s)", user_id, exc)

    email = settings.DEV_USER_EMAIL or f"dev-{user_id[:8]}@virtualcorp.local"
    password = f"{uuid.uuid4()}-DevOnly123!"
    try:
        client.auth.admin.create_user(
            {
                "id": user_id,
                "email": email,
                "password": password,
                "email_confirm": True,
                "user_metadata": {
                    "source": source,
                    "virtual_corp_os": True,
                },
            }
        )
        logger.info("[DEV] created development auth user email=%s id=%s", email, user_id)
        return user_id
    except Exception as create_exc:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "DEV_USER_CREATE_FAILED",
                "code": "DEV_USER_CREATE_FAILED",
                "detail": (
                    "DEV_USER_ID는 확인됐지만 auth.users에 개발 사용자를 준비하지 못했습니다. "
                    "service role 키 또는 유효한 DEV_USER_ID를 확인해주세요."
                ),
                "source": source,
            },
        ) from create_exc


def _resolve_dev_user_id() -> str | None:
    global _runtime_dev_user_id

    env_user_id = (settings.DEV_USER_ID or "").strip()
    if env_user_id:
        if not _is_valid_uuid(env_user_id):
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "INVALID_DEV_USER_ID",
                    "code": "INVALID_DEV_USER_ID",
                    "detail": "DEV_USER_ID는 유효한 UUID여야 합니다.",
                },
            )
        return _ensure_auth_user_exists(env_user_id, "env")

    if not settings.ALLOW_DEV_USER_FALLBACK:
        return None

    if _runtime_dev_user_id is None:
        _runtime_dev_user_id = str(uuid.uuid4())
        logger.info("[DEV] generated runtime DEV_USER_ID=%s", _runtime_dev_user_id)
        print(f"[DEV] generated runtime DEV_USER_ID: {_runtime_dev_user_id}")

    return _ensure_auth_user_exists(_runtime_dev_user_id, "runtime")


def prepare_dev_user_fallback() -> str | None:
    try:
        return _resolve_dev_user_id()
    except HTTPException as exc:
        logger.warning("[DEV] fallback preparation skipped: %s", exc.detail)
        return None
    except Exception as exc:
        logger.warning("[DEV] fallback preparation failed: %s", exc)
        return None


def resolve_user_id(request: Request, explicit_user_id: str | None = None) -> str:
    """
    우선순위:
    1. 인증된 사용자 (request state / bearer token)
    2. 명시적으로 전달된 user_id
    3. DEV_USER_ID (env or dev runtime fallback)
    4. 없으면 에러
    """

    request_user_id = _extract_user_id_from_request(request)
    if request_user_id:
        _log_user_resolution("[AUTH]", request_user_id, "using logged-in user_id")
        return request_user_id

    if _is_valid_uuid(explicit_user_id):
        user_id = str(explicit_user_id)
        _log_user_resolution("[AUTH]", user_id, "using client-provided user_id")
        return user_id

    dev_user_id = _resolve_dev_user_id()
    if dev_user_id:
        _log_user_resolution("[DEV]", dev_user_id, "using DEV_USER_ID")
        return dev_user_id

    raise HTTPException(
        status_code=401,
        detail={
            "error": "Authenticated user required",
            "code": "USER_ID_REQUIRED",
            "detail": "로그인 또는 개발 사용자 ID가 없어 프로젝트를 생성할 수 없습니다.",
        },
    )
