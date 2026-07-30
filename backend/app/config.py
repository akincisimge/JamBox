from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "JamBox API"
    app_env: str = "development"
    api_prefix: str = "/api"
    database_url: str = "postgresql+asyncpg://jambox:jambox@localhost:5432/jambox"
    cors_origins: str = "http://localhost:3000"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_database_url(cls, value: object) -> object:
        if not isinstance(value, str):
            return value

        normalized = value
        if normalized.startswith("postgresql://"):
            normalized = normalized.replace("postgresql://", "postgresql+asyncpg://", 1)

        normalized = normalized.replace("sslmode=require", "ssl=require")
        normalized = normalized.replace("&channel_binding=require", "")
        normalized = normalized.replace("channel_binding=require&", "")
        normalized = normalized.replace("?channel_binding=require", "")
        return normalized

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
