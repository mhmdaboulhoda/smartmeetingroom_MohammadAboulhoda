"""Pydantic schemas for booking operations."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from services.bookings_service.models import BookingStatus


class UserRef(BaseModel):
    id: int


class RoomRef(BaseModel):
    id: int


class BookingBase(BaseModel):
    start_time: datetime
    end_time: datetime


class BookingCreate(BookingBase):
    room_id: int


class BookingUpdate(BaseModel):
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: Optional[BookingStatus] = None


class BookingOut(BaseModel):
    id: int
    user: UserRef
    room: RoomRef
    start_time: datetime
    end_time: datetime
    status: BookingStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
