"""Pydantic schemas for the Rooms service."""

from datetime import datetime
from typing import Any, Optional, Union

from pydantic import BaseModel, Field, ConfigDict

from services.rooms_service.models import RoomStatus

EquipmentType = Optional[Union[dict[str, Any], list[Any]]]


class RoomBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    capacity: int = Field(..., ge=1)
    location: str = Field(..., min_length=1, max_length=255)
    equipment: EquipmentType = None
    status: RoomStatus = RoomStatus.AVAILABLE


class RoomCreate(RoomBase):
    pass


class RoomUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    capacity: Optional[int] = Field(None, ge=1)
    location: Optional[str] = Field(None, min_length=1, max_length=255)
    equipment: EquipmentType = None
    status: Optional[RoomStatus] = None


class RoomOut(RoomBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
