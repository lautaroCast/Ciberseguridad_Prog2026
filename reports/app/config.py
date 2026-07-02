"""Application settings, sourced entirely from environment variables.

Unlike the Backend's settings (Módulo 3/5/6), nothing here is
security-sensitive, so a sensible default is fine — an empty/missing
output dir would just mean "use the conventional path", not silently
break a safety guarantee.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    reports_output_dir: str = "/data/reports"


@lru_cache
def get_settings() -> Settings:
    return Settings()
