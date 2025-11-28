"""Pydantic schemas for the Reviews service."""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class ReviewBase(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: str = Field(..., min_length=1, max_length=2000)


class ReviewCreate(ReviewBase):
    pass


class ReviewUpdate(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5)
    comment: Optional[str] = Field(None, min_length=1, max_length=2000)


class ReviewOut(BaseModel):
    id: int
    user_id: int
    room_id: int
    rating: int
    comment: str
    created_at: datetime
    updated_at: datetime
    is_flagged: Optional[bool] = None
    is_hidden: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True)


class ReviewModerationAction(BaseModel):
    action: Literal["hide", "unhide", "clear_flags"]
