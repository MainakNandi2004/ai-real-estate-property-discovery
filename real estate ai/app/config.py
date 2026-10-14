from functools import lru_cache

from dotenv import load_dotenv
from pydantic import Field, field_validator

load_dotenv()
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = Field(default="development", alias="APP_ENV")
    debug: bool = Field(default=False, alias="DEBUG")

    @field_validator("debug", mode="before")
    @classmethod
    def normalize_debug(cls, value):
        # Some launch environments expose DEBUG as the environment label
        # (for example, "release") rather than a boolean. Treat release-like
        # labels as disabled instead of preventing the application from loading.
        if isinstance(value, str) and value.strip().lower() in {
            "release", "production", "prod", "development", "dev"
        }:
            return value.strip().lower() in {"development", "dev"}
        return value

    database_url: str = Field(..., alias="DATABASE_URL")

    test_database_url: str | None = Field(default=None, alias="TEST_DATABASE_URL")

    gemini_api_key: str | None = Field(default=None, alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-2.0-flash", alias="GEMINI_MODEL")


@lru_cache
def get_settings() -> Settings:
    return Settings()
