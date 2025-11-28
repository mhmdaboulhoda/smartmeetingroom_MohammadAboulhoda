"""Configuration helpers shared across services."""

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseSettings, Field


ROOT_DIR = Path(__file__).resolve().parent.parent
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Load `.env` when running locally so developers have a lightweight setup.
if ENVIRONMENT == "development":
    load_dotenv(dotenv_path=ROOT_DIR / ".env", override=False)


class Settings(BaseSettings):
    """Load environment-driven settings for services."""

    environment: str = Field(ENVIRONMENT, env="ENVIRONMENT")
    database_url: str = Field(
        "postgresql+psycopg2://user:password@localhost:5432/smartmeetingroom",
        env="DATABASE_URL",
    )
    jwt_secret_key: str = Field("change-me", env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field("HS256", env="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(30, env="ACCESS_TOKEN_EXPIRE_MINUTES")


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance to avoid redundant env parsing."""

    return Settings()


settings = get_settings()
