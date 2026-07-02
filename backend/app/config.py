"""Application settings, sourced entirely from environment variables.

No hardcoded defaults for anything security-sensitive: the container fails
fast at startup if DATABASE_URL is missing rather than silently falling
back to something that looks local but isn't.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    backend_log_level: str = "info"
    backend_cors_origins: str = ""
    backend_allowed_lab_hosts: str = ""

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.backend_cors_origins.split(",") if origin.strip()]

    @property
    def allowed_lab_hosts(self) -> set[str]:
        return {host.strip() for host in self.backend_allowed_lab_hosts.split(",") if host.strip()}


@lru_cache
def get_settings() -> Settings:
    return Settings()
