"""SQLAlchemy models for the Rooms service."""

from datetime import datetime
from enum import Enum

from sqlalchemy import JSON, Column, DateTime, Enum as SQLEnum, Index, Integer, String, func

from common.db import Base


class RoomStatus(str, Enum):
    """Lifecycle states for a meeting room."""

    AVAILABLE = "AVAILABLE"
    BOOKED = "BOOKED"
    OUT_OF_SERVICE = "OUT_OF_SERVICE"


class Room(Base):
    """Room entity stored in the shared database.

    Indexes on name/location/status keep search and availability filters fast when
    users browse rooms and when the booking service validates availability.
    """

    __tablename__ = "rooms"
    __table_args__ = (
        Index("idx_rooms_name", "name"),
        Index("idx_rooms_location", "location"),
        Index("idx_rooms_status", "status"),
    )

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    capacity = Column(Integer, nullable=False)
    location = Column(String(255), nullable=False)
    equipment = Column(JSON, nullable=True)
    status = Column(
        SQLEnum(RoomStatus, name="room_status"),
        nullable=False,
        default=RoomStatus.AVAILABLE,
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
