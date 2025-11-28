"""SQLAlchemy models for the Bookings service."""

from datetime import datetime
from enum import Enum

from sqlalchemy import Column, DateTime, Enum as SQLEnum, ForeignKey, Index, Integer, func
from sqlalchemy.orm import relationship

from common.db import Base


class BookingStatus(str, Enum):
    """State transitions for bookings."""

    CONFIRMED = "CONFIRMED"
    CANCELED = "CANCELED"
    OVERRIDDEN = "OVERRIDDEN"


class Booking(Base):
    """Represents a room reservation.

    Indexes target the most common queries: listing bookings for a user,
    finding overlaps for a room, and sorting by start time.
    """

    __tablename__ = "bookings"
    __table_args__ = (
        Index("idx_booking_room_time", "room_id", "start_time"),
        Index("idx_booking_user_id", "user_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    room_id = Column(Integer, ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False, index=True)
    end_time = Column(DateTime(timezone=True), nullable=False)
    status = Column(
        SQLEnum(BookingStatus, name="booking_status"),
        nullable=False,
        default=BookingStatus.CONFIRMED,
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", lazy="joined", viewonly=True)
    room = relationship("Room", lazy="joined", viewonly=True)
