"""Business logic for managing rooms."""

from typing import List, Optional

from sqlalchemy.orm import Session

from common.exceptions import ConflictError, NotFoundError
from services.rooms_service.cache import rooms_cache
from services.rooms_service.models import Room, RoomStatus
from services.rooms_service.schemas import RoomCreate, RoomUpdate


def create_room(db: Session, room_in: RoomCreate) -> Room:
    """Persist a new room ensuring uniqueness."""

    existing = db.query(Room).filter(Room.name == room_in.name).first()
    if existing:
        raise ConflictError("Room name already exists")

    room = Room(
        name=room_in.name,
        capacity=room_in.capacity,
        location=room_in.location,
        equipment=room_in.equipment,
        status=room_in.status,
    )
    db.add(room)
    db.commit()
    db.refresh(room)
    invalidate_rooms_cache_for_room(room.id)
    return room


def get_room(db: Session, room_id: int) -> Room:
    """Return a single room or raise if missing."""

    room = db.get(Room, room_id)
    if not room:
        raise NotFoundError("Room not found")
    return room


def list_rooms(
    db: Session,
    *,
    location: Optional[str] = None,
    min_capacity: Optional[int] = None,
    status: Optional[RoomStatus] = None,
) -> List[Room]:
    """Return rooms filtered by optional criteria with a small in-memory cache."""

    cache_key = rooms_cache.make_key(
        location,
        min_capacity,
        status.value if isinstance(status, RoomStatus) else status,
    )
    cached_value = rooms_cache.get(cache_key)
    if cached_value is not None:
        return cached_value

    query = db.query(Room)
    if location:
        query = query.filter(Room.location == location)
    if min_capacity:
        query = query.filter(Room.capacity >= min_capacity)
    if status:
        query = query.filter(Room.status == status)
    result = query.order_by(Room.name).all()
    rooms_cache.set(cache_key, result)
    return result


def update_room(db: Session, room_id: int, room_update: RoomUpdate) -> Room:
    """Apply partial updates to a room."""

    room = get_room(db, room_id)
    update_data = room_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(room, field, value)
    db.add(room)
    db.commit()
    db.refresh(room)
    invalidate_rooms_cache_for_room(room.id)
    return room


def delete_room(db: Session, room_id: int) -> None:
    """Delete a room."""

    room = get_room(db, room_id)
    db.delete(room)
    db.commit()
    invalidate_rooms_cache_for_room(room.id)


def invalidate_rooms_cache_for_room(room_id: Optional[int] = None) -> None:
    """Invalidate cache after changing room records."""

    # Simple strategy: flush entire cache when any write occurs.
    rooms_cache.invalidate()
