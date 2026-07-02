"""Application settings, sourced entirely from environment variables.

No hardcoded defaults for anything security-sensitive: the container fails
fast at startup if DATABASE_URL or BACKEND_ALLOWED_LAB_HOSTS is missing or
empty, rather than silently falling back to something that looks local but
isn't (an empty whitelist would otherwise boot fine and just reject every
target registration with no indication the cause is misconfiguration).
"""

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    backend_allowed_lab_hosts: str
    backend_log_level: str = "info"
    backend_cors_origins: str = ""

    @field_validator("backend_allowed_lab_hosts")
    @classmethod
    def _require_at_least_one_lab_host(cls, value: str) -> str:
        if not value.strip():
            raise ValueError(
                "BACKEND_ALLOWED_LAB_HOSTS must not be empty — an empty whitelist "
                "would boot successfully and then silently reject every target "
                "registration. Set it to the lab's container hostnames, e.g. "
                "'juice-shop,dvwa' (see .env.example)."
            )
        return value

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.backend_cors_origins.split(",") if origin.strip()]

    @property
    def allowed_lab_hosts(self) -> set[str]:
        return {host.strip() for host in self.backend_allowed_lab_hosts.split(",") if host.strip()}


@lru_cache
def get_settings() -> Settings:
    return Settings()
