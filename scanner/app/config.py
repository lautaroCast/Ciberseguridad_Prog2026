"""Scanner Service settings, sourced from environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Hard upper bound on any single tool execution, regardless of what a
    # caller's ScanRequest.timeout_seconds asks for — this is what keeps a
    # misbehaving scan from hanging a pipeline run indefinitely.
    scanner_max_timeout_seconds: int = 900


@lru_cache
def get_settings() -> Settings:
    return Settings()
