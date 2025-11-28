"""Shared helpers for local profiling scripts."""

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from common.db import Base
from services.bookings_service.schemas import BookingCreate
from services.rooms_service.models import Room, RoomStatus
from services.users_service.models import User, UserRole

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
Base.metadata.create_all(bind=engine)

_SEED_CACHE: dict[str, int] = {}
_BOOKING_OFFSET = 0


def get_session():
    return SessionLocal()


def ensure_seed(session) -> dict[str, int]:
    global _SEED_CACHE
    if _SEED_CACHE:
        return _SEED_CACHE

    user = User(
        username="profiler-user",
        email="profiler@example.com",
        full_name="Profiler User",
        password_hash="hashed",
        role=UserRole.REGULAR,
    )
    room = Room(
        name="Profiler Room",
        capacity=12,
        location="HQ",
        equipment={},
        status=RoomStatus.AVAILABLE,
    )
    session.add_all([user, room])
    session.commit()
    session.refresh(user)
    session.refresh(room)
    _SEED_CACHE = {"user_id": user.id, "room_id": room.id}
    return _SEED_CACHE


def get_regular_user(session):
    seed = ensure_seed(session)
    return SimpleNamespace(id=seed["user_id"], role=UserRole.REGULAR.value)


def get_room_id(session) -> int:
    seed = ensure_seed(session)
    return seed["room_id"]


def build_booking_payload(room_id: int) -> BookingCreate:
    global _BOOKING_OFFSET
    start = datetime.now(timezone.utc) + timedelta(hours=_BOOKING_OFFSET)
    _BOOKING_OFFSET += 2
    end = start + timedelta(hours=1)
    return BookingCreate(room_id=room_id, start_time=start, end_time=end)
