"""Application settings, sourced entirely from environment variables.

`reports_output_dir` isn't security-sensitive — an empty/missing value
would just mean "use the conventional path", not silently break a safety
guarantee. `internal_api_key` (Módulo 9) is different: this service no
longer publishes its port to the host, and every /reports call must carry
it as X-Internal-Token, so it follows the Backend's "fail fast if missing"
pattern instead.
"""

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    reports_output_dir: str = "/data/reports"
    internal_api_key: str

    @field_validator("internal_api_key")
    @classmethod
    def _require_internal_api_key(cls, value: str) -> str:
        if not value.strip():
            raise ValueError(
                "INTERNAL_API_KEY must not be empty — every /reports call would boot "
                "successfully and then reject the X-Internal-Token check with no "
                "valid value to ever match. Set it to the same secret configured on "
                "the Backend and Scanner Service (see .env.example)."
            )
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
