"""Database connection helpers shared across services."""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from common.config import settings


def _active_service_name() -> str | None:
    for env_var in ("SMARTMEETINGROOM_SERVICE", "SERVICE_NAME"):
        value = os.getenv(env_var)
        if value:
            return value
    return None


DATABASE_URL = settings.database_url_for(_active_service_name())

engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db():
    """Yield a DB session, closing it afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
