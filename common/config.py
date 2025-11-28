"""Configuration helpers shared across services."""

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parent.parent
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Load `.env` when running locally so developers have a lightweight setup.
if ENVIRONMENT == "development":
    load_dotenv(dotenv_path=ROOT_DIR / ".env", override=False)


class Settings(BaseSettings):
    """Load environment-driven settings for services."""

    model_config = SettingsConfigDict(extra="ignore", env_prefix="")

    environment: str = ENVIRONMENT
    database_url: str = "postgresql+psycopg2://user:password@localhost:5432/smartmeetingroom"
    jwt_secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance to avoid redundant env parsing."""

    return Settings()


settings = get_settings()
