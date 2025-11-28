"""Tests for the bookings service API."""

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from common.auth import get_current_user, require_roles
from common.db import Base, get_db
from services.bookings_service.app import app
from services.bookings_service.models import BookingStatus
from services.rooms_service.models import Room, RoomStatus
from services.users_service.models import User, UserRole

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)


def override_get_db() -> Generator[Session, None, None]:
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.pop(get_db, None)
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    with TestingSessionLocal() as session:
        yield session


def make_user(session: Session, username: str, role: UserRole) -> User:
    user = User(
        username=username,
        email=f"{username}@example.com",
        full_name=f"{username.title()} Tester",
        password_hash="hashed",
        role=role,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def make_room(session: Session, name: str, status: RoomStatus = RoomStatus.AVAILABLE) -> Room:
    room = Room(
        name=name,
        capacity=10,
        location="HQ",
        equipment=None,
        status=status,
    )
    session.add(room)
    session.commit()
    session.refresh(room)
    return room


@pytest.fixture
def users_and_room(db_session: Session):
    admin = make_user(db_session, "admin", UserRole.ADMIN)
    regular = make_user(db_session, "alice", UserRole.REGULAR)
    bob = make_user(db_session, "bob", UserRole.REGULAR)
    facility = make_user(db_session, "frank", UserRole.FACILITY_MANAGER)
    room = make_room(db_session, "Room 101")
    return {"admin": admin, "regular": regular, "bob": bob, "facility": facility, "room": room}


@pytest.fixture
def client():
    return TestClient(app)


def set_current_user(user_obj):
    app.dependency_overrides[get_current_user] = lambda: user_obj
    app.dependency_overrides[require_roles("ADMIN", "FACILITY_MANAGER", "REGULAR")] = lambda: user_obj
    app.dependency_overrides[require_roles("ADMIN", "FACILITY_MANAGER")] = lambda: user_obj


def clear_current_user():
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(require_roles("ADMIN", "FACILITY_MANAGER", "REGULAR"), None)
    app.dependency_overrides.pop(require_roles("ADMIN", "FACILITY_MANAGER"), None)


def make_booking_payload(room_id: int, offset_hours: int = 0):
    start = datetime.now(timezone.utc) + timedelta(hours=offset_hours)
    end = start + timedelta(hours=1)
    return {"room_id": room_id, "start_time": start.isoformat(), "end_time": end.isoformat()}


def test_create_booking_succeeds(client: TestClient, users_and_room):
    user = users_and_room["regular"]
    set_current_user(SimpleNamespace(id=user.id, role=user.role))
    payload = make_booking_payload(users_and_room["room"].id)
    response = client.post("/api/v1/bookings/", json=payload)
    clear_current_user()
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["room"]["id"] == users_and_room["room"].id
    assert data["user"]["id"] == user.id
    assert data["status"] == BookingStatus.CONFIRMED.value


def test_create_booking_conflict(client: TestClient, db_session, users_and_room):
    user = users_and_room["regular"]
    other_user = users_and_room["bob"]
    set_current_user(SimpleNamespace(id=user.id, role=user.role))
    payload = make_booking_payload(users_and_room["room"].id)
    client.post("/api/v1/bookings/", json=payload)
    clear_current_user()

    set_current_user(SimpleNamespace(id=other_user.id, role=other_user.role))
    response = client.post("/api/v1/bookings/", json=payload)
    clear_current_user()
    assert response.status_code == 409
    assert response.json()["error_code"] == "BOOKING_CONFLICT"


def test_regular_user_cancel_own_booking(client: TestClient, users_and_room):
    user = users_and_room["regular"]
    set_current_user(SimpleNamespace(id=user.id, role=user.role))
    payload = make_booking_payload(users_and_room["room"].id)
    booking = client.post("/api/v1/bookings/", json=payload).json()
    response = client.post(f"/api/v1/bookings/{booking['id']}/cancel")
    clear_current_user()
    assert response.status_code == 200
    assert response.json()["status"] == BookingStatus.CANCELED.value


def test_regular_user_cannot_cancel_others_booking(client: TestClient, users_and_room):
    owner = users_and_room["regular"]
    other = users_and_room["bob"]
    set_current_user(SimpleNamespace(id=owner.id, role=owner.role))
    payload = make_booking_payload(users_and_room["room"].id)
    booking = client.post("/api/v1/bookings/", json=payload).json()
    clear_current_user()

    set_current_user(SimpleNamespace(id=other.id, role=other.role))
    response = client.post(f"/api/v1/bookings/{booking['id']}/cancel")
    clear_current_user()
    assert response.status_code == 403
    assert response.json()["error_code"] == "BOOKING_FORBIDDEN"


def test_admin_lists_and_overrides_booking(client: TestClient, users_and_room):
    regular = users_and_room["regular"]
    admin = users_and_room["admin"]

    set_current_user(SimpleNamespace(id=regular.id, role=regular.role))
    payload = make_booking_payload(users_and_room["room"].id)
    booking = client.post("/api/v1/bookings/", json=payload).json()
    clear_current_user()

    set_current_user(SimpleNamespace(id=admin.id, role=admin.role))
    list_response = client.get("/api/v1/bookings/")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    cancel_response = client.post(f"/api/v1/bookings/{booking['id']}/cancel")
    clear_current_user()
    assert cancel_response.status_code == 200
    assert cancel_response.json()["status"] == BookingStatus.OVERRIDDEN.value
