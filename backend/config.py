from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables.

    All R2 and Anthropic credentials are required; the app refuses to start
    without them rather than failing on the first request.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Anthropic
    anthropic_api_key: str
    anthropic_model: str = "claude-haiku-4-5"

    # Cloudflare R2 (accessed via the S3-compatible API)
    r2_account_id: str
    r2_access_key_id: str
    r2_secret_access_key: str
    r2_bucket_name: str
    # Optional explicit endpoint; derived from the account id when omitted.
    r2_endpoint_url: str | None = None

    # Upload constraints
    max_file_size_bytes: int = 1_000_000  # 1 MB of plain text/markdown is plenty.
    # Characters of document text sent to the LLM for metadata inference.
    llm_input_char_limit: int = 12_000

    # CORS: comma-separated list of allowed origins for the frontend.
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    @property
    def endpoint_url(self) -> str:
        return self.r2_endpoint_url or f"https://{self.r2_account_id}.r2.cloudflarestorage.com"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor used as a FastAPI dependency."""
    return Settings()  # type: ignore[call-arg]  # values come from the environment
