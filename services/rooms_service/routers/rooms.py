"""Rooms API router."""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from common.auth import get_current_user, require_roles
from common.db import get_db
from services.rooms_service import SERVICE_NAME
from services.rooms_service.models import RoomStatus
from services.rooms_service.schemas import RoomCreate, RoomOut, RoomUpdate
from services.rooms_service.service import (
    create_room as create_room_service,
    delete_room as delete_room_service,
    get_room as get_room_service,
    list_rooms as list_rooms_service,
    update_room as update_room_service,
)

router = APIRouter(prefix="/api/v1/rooms", tags=["rooms"])


@router.post(
    "/",
    response_model=RoomOut,
    status_code=status.HTTP_201_CREATED,
)
def create_room(
    room_in: RoomCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("ADMIN", "FACILITY_MANAGER")),
):
    """Create a new room."""

    return create_room_service(db, room_in)


@router.get("/", response_model=List[RoomOut])
def list_rooms(
    *,
    location: Optional[str] = Query(None, description="Filter by building/wing"),
    min_capacity: Optional[int] = Query(None, ge=1, description="Minimum seat count"),
    status_filter: Optional[RoomStatus] = Query(
        None,
        alias="status",
        description="Filter by room status",
    ),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List rooms with optional filters."""

    return list_rooms_service(
        db,
        location=location,
        min_capacity=min_capacity,
        status=status_filter,
    )


@router.get("/{room_id}", response_model=RoomOut)
def get_room(
    room_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Return a single room."""

    return get_room_service(db, room_id)


@router.patch("/{room_id}", response_model=RoomOut)
def update_room(
    room_id: int,
    room_update: RoomUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("ADMIN", "FACILITY_MANAGER")),
):
    """Update fields on an existing room."""

    return update_room_service(db, room_id, room_update)


@router.delete("/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_room(
    room_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("ADMIN", "FACILITY_MANAGER")),
):
    """Delete a room."""

    delete_room_service(db, room_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/health", include_in_schema=False)
async def health_check() -> dict[str, str]:
    """Health probe for orchestrators."""

    return {"status": "ok", "service": SERVICE_NAME}
