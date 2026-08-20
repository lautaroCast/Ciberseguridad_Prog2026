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
    n8n_webhook_base_url: str
    reports_base_url: str
    backend_api_key: str
    internal_api_key: str
    n8n_webhook_secret: str

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

    @field_validator("n8n_webhook_base_url")
    @classmethod
    def _require_n8n_webhook_base_url(cls, value: str) -> str:
        if not value.strip():
            raise ValueError(
                "N8N_WEBHOOK_BASE_URL must not be empty — POST /targets/{id}/pipeline "
                "would boot successfully and then fail every request with no clear "
                "cause. Set it to n8n's internal service URL, e.g. 'http://n8n:5678' "
                "(see .env.example)."
            )
        return value.rstrip("/")

    @field_validator("reports_base_url")
    @classmethod
    def _require_reports_base_url(cls, value: str) -> str:
        if not value.strip():
            raise ValueError(
                "REPORTS_BASE_URL must not be empty — POST /scans/{id}/reports would "
                "boot successfully and then fail every request with no clear cause. "
                "Set it to the Reports Service's internal URL, e.g. 'http://reports:8200' "
                "(see .env.example)."
            )
        return value.rstrip("/")

    @field_validator("backend_api_key")
    @classmethod
    def _require_backend_api_key(cls, value: str) -> str:
        if not value.strip():
            raise ValueError(
                "BACKEND_API_KEY must not be empty — every user-facing router would "
                "boot successfully and then reject the X-API-Key check with no valid "
                "value to ever match. Set it to a random secret (see .env.example)."
            )
        return value

    @field_validator("internal_api_key")
    @classmethod
    def _require_internal_api_key(cls, value: str) -> str:
        if not value.strip():
            raise ValueError(
                "INTERNAL_API_KEY must not be empty — calls to the Reports Service "
                "would boot successfully and then fail every request once Reports "
                "starts requiring X-Internal-Token. Set it to a random secret shared "
                "with scanner/reports (see .env.example)."
            )
        return value

    @field_validator("n8n_webhook_secret")
    @classmethod
    def _require_n8n_webhook_secret(cls, value: str) -> str:
        if not value.strip():
            raise ValueError(
                "N8N_WEBHOOK_SECRET must not be empty — the pipeline trigger would boot "
                "successfully and then have n8n's Webhook Trigger reject every call with "
                "no valid value to ever match. Set it to a random secret shared with n8n "
                "(see .env.example)."
            )
        return value

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.backend_cors_origins.split(",") if origin.strip()]

    @property
    def allowed_lab_hosts(self) -> set[str]:
        return {host.strip() for host in self.backend_allowed_lab_hosts.split(",") if host.strip()}

    @property
    def n8n_pipeline_webhook_url(self) -> str:
        # The path is fixed by our own workflow definition (see the Webhook
        # trigger node in n8n/workflows/vulnscan-pipeline.json), not
        # deployment-specific, so only the base URL is configurable.
        return f"{self.n8n_webhook_base_url}/webhook/vulnscan-pipeline"


@lru_cache
def get_settings() -> Settings:
    return Settings()
