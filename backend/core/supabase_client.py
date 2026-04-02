import logging
from supabase import create_client, Client
from core.settings import settings

logger = logging.getLogger(__name__)

_client: Client | None = None


def get_supabase_client() -> Client:
    global _client
    if _client is None:
        if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
            raise RuntimeError(
                "SUPABASE_URL 또는 SUPABASE_KEY가 설정되지 않았습니다."
            )
        _client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        logger.info("[supabase] 클라이언트 초기화 완료")
    return _client
