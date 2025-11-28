"""Database connection helpers shared across services."""

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from common.config import settings

DATABASE_URL = settings.database_url

engine = create_engine(
    DATABASE_URL,
    future=True,
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


@contextmanager
def db_session() -> Generator[Session, None, None]:
    """Context manager used by services and scripts."""

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a DB session."""

    with db_session() as session:
        yield session
