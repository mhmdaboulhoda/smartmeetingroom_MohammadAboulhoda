"""Configuration helpers shared across services."""

import os
from typing import Optional

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Load environment-driven settings for services."""

    environment: str = "development"
    default_database_url: str = Field(
        "postgresql+psycopg2://user:password@localhost:5432/smartmeetingroom",
        env="DEFAULT_DATABASE_URL",
    )

    def database_url_for(self, service_name: Optional[str] = None) -> str:
        """Return the configured DB URL for the requested service."""

        env_candidates = []
        if service_name:
            env_candidates.append(f"{service_name.upper()}_DATABASE_URL")
        env_candidates.append("DATABASE_URL")

        for env_name in env_candidates:
            value = os.getenv(env_name)
            if value:
                return value

        return self.default_database_url


settings = Settings()
