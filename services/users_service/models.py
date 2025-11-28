"""SQLAlchemy models for the Users service."""

from datetime import datetime
from enum import Enum

from sqlalchemy import Column, DateTime, Enum as SQLEnum, Integer, String, func

from common.db import Base


class UserRole(str, Enum):
    """Supported roles in the smart meeting room platform."""

    ADMIN = "ADMIN"
    REGULAR = "REGULAR"
    FACILITY_MANAGER = "FACILITY_MANAGER"


class User(Base):
    """User account stored in PostgreSQL.

    Username and email columns are indexed to accelerate login checks,
    uniqueness validation, and search endpoints used by admins.
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255))
    password_hash = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole, name="user_role"), nullable=False, default=UserRole.REGULAR)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
