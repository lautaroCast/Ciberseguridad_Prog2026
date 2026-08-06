"""Scanner Service settings, sourced from environment variables."""

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Hard upper bound on any single tool execution, regardless of what a
    # caller's ScanRequest.timeout_seconds asks for — this is what keeps a
    # misbehaving scan from hanging a pipeline run indefinitely.
    scanner_max_timeout_seconds: int = 900

    # Required, no default: this service no longer publishes its port to
    # the host (Módulo 9) and every /scan/{tool} call must carry this as
    # X-Internal-Token — an empty/missing secret would boot successfully
    # and then reject every real call from n8n with no clear cause.
    internal_api_key: str

    # Required, no default: this is the Scanner's OWN copy of the lab-host
    # whitelist, checked independently of the Backend's check at target
    # registration time. The Scanner is the only component with a network
    # route to lab-network, so this is the last point that can actually
    # stop a scan from reaching an unauthorized host — a single point of
    # enforcement (Backend only) is not real defense in depth. Sourced from
    # the same BACKEND_ALLOWED_LAB_HOSTS value in docker-compose.yml, so
    # there's one policy maintained in .env, enforced at two independent
    # points in code.
    scanner_allowed_lab_hosts: str

    @field_validator("internal_api_key")
    @classmethod
    def _require_internal_api_key(cls, value: str) -> str:
        if not value.strip():
            raise ValueError(
                "INTERNAL_API_KEY must not be empty — every /scan/{tool} call would "
                "boot successfully and then reject the X-Internal-Token check with no "
                "valid value to ever match. Set it to the same secret configured on "
                "the Backend and n8n (see .env.example)."
            )
        return value

    @field_validator("scanner_allowed_lab_hosts")
    @classmethod
    def _require_at_least_one_lab_host(cls, value: str) -> str:
        if not value.strip():
            raise ValueError(
                "SCANNER_ALLOWED_LAB_HOSTS must not be empty — an empty whitelist "
                "would boot successfully and then silently reject every /scan/{tool} "
                "call. Set it to the same value as BACKEND_ALLOWED_LAB_HOSTS, e.g. "
                "'juice-shop,dvwa' (see .env.example)."
            )
        return value

    @property
    def allowed_lab_hosts(self) -> set[str]:
        return {host.strip() for host in self.scanner_allowed_lab_hosts.split(",") if host.strip()}


@lru_cache
def get_settings() -> Settings:
    return Settings()
