"""SQLAlchemy models for the Reviews service."""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, Text, func
from sqlalchemy.orm import relationship

from common.db import Base


class Review(Base):
    """Feedback left by users for rooms.

    Indexes help the rooms API fetch reviews quickly and let moderators scan
    flagged/hidden content without table scans.
    """

    __tablename__ = "reviews"
    __table_args__ = (
        Index("idx_reviews_room_id", "room_id"),
        Index("idx_reviews_user_id", "user_id"),
        Index("idx_reviews_hidden", "is_hidden"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    room_id = Column(Integer, ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False)
    rating = Column(Integer, nullable=False)
    comment = Column(Text, nullable=False)
    is_flagged = Column(Boolean, nullable=False, default=False)
    is_hidden = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user = relationship("User", lazy="joined", viewonly=True)
    room = relationship("Room", lazy="joined", viewonly=True)
