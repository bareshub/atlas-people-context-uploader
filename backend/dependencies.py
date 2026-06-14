from functools import lru_cache

from config import get_settings
from services.llm_service import LLMService
from services.r2_client import R2Client


@lru_cache
def _r2_client() -> R2Client:
    return R2Client(get_settings())


@lru_cache
def _llm_service() -> LLMService:
    return LLMService(get_settings())


def get_r2_client() -> R2Client:
    """Inject a singleton R2 client. Overridden with a mock in tests."""
    return _r2_client()


def get_llm_service() -> LLMService:
    """Inject a singleton LLM service. Overridden with a mock in tests."""
    return _llm_service()
