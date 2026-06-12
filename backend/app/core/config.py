from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    env: str = "dev"
    database_url: str = "postgresql+asyncpg://civicpulse:civicpulse@localhost:5432/civicpulse"
    redis_url: str = "redis://localhost:6379/0"

    jwt_secret: str = "dev-secret-change-me"

    s3_endpoint_url: str = "http://localhost:9000"
    s3_access_key: str = "civicpulse"
    s3_secret_key: str = "civicpulse123"
    s3_bucket: str = "civicpulse-media"

    cors_origins: list[str] = ["http://localhost:3000"]

    mock_ai: bool = True
    gemini_api_key: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
