from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import BeforeValidator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[3]
CorsOrigins = Annotated[
    list[str],
    NoDecode,
    BeforeValidator(lambda value: value.split(",") if isinstance(value, str) else value),
]


class Settings(BaseSettings):
    app_env: str = "development"
    app_name: str = "distributed-job-processing-platform"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/job_processing"
    secret_key: str = "dev-secret-key-change-in-production"
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"
    celery_task_always_eager: bool = False
    enable_job_queue: bool = True
    cors_origins: CorsOrigins = ["http://localhost:5173", "http://127.0.0.1:5173"]

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
