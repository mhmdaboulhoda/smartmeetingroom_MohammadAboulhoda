"""Tests for the Reviews service API."""

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from common.auth import get_current_user
from common.db import Base, get_db
from services.bookings_service.models import Booking, BookingStatus
from services.reviews_service.app import app
from services.reviews_service.models import Review
from services.reviews_service.schemas import ReviewCreate
from services.rooms_service.models import Room, RoomStatus
from services.users_service.models import User, UserRole

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine, expire_on_commit=False
)


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


@pytest.fixture
def client():
    return TestClient(app)


def set_current_user(user):
    app.dependency_overrides[get_current_user] = lambda: user


def clear_current_user():
    app.dependency_overrides.pop(get_current_user, None)


def create_user(session: Session, username: str, role: UserRole) -> User:
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


def create_room(session: Session, name: str) -> Room:
    room = Room(
        name=name,
        capacity=5,
        location="HQ",
        equipment=None,
        status=RoomStatus.AVAILABLE,
    )
    session.add(room)
    session.commit()
    session.refresh(room)
    return room


def create_booking(session: Session, user_id: int, room_id: int) -> Booking:
    now = datetime.now(timezone.utc)
    booking = Booking(
        user_id=user_id,
        room_id=room_id,
        start_time=now,
        end_time=now + timedelta(hours=1),
        status=BookingStatus.CONFIRMED,
    )
    session.add(booking)
    session.commit()
    session.refresh(booking)
    return booking


def test_user_with_booking_can_create_review(client: TestClient, db_session: Session):
    user = create_user(db_session, "alice", UserRole.REGULAR)
    room = create_room(db_session, "Room-A")
    create_booking(db_session, user.id, room.id)

    set_current_user(user)
    response = client.post(
        f"/api/v1/reviews/rooms/{room.id}",
        json={"rating": 5, "comment": "Great room!"},
    )
    clear_current_user()
    assert response.status_code == 200
    body = response.json()
    assert body["rating"] == 5
    assert body["comment"] == "Great room!"
    assert body["room_id"] == room.id


def test_user_without_booking_cannot_review(client: TestClient, db_session: Session):
    user = create_user(db_session, "bob", UserRole.REGULAR)
    room = create_room(db_session, "Room-B")

    set_current_user(user)
    response = client.post(
        f"/api/v1/reviews/rooms/{room.id}",
        json={"rating": 4, "comment": "Nice"},
    )
    clear_current_user()
    assert response.status_code == 403
    assert response.json()["error_code"] == "REVIEW_REQUIRES_BOOKING"


def test_user_can_update_and_delete_own_review(client: TestClient, db_session: Session):
    user = create_user(db_session, "carol", UserRole.REGULAR)
    other = create_user(db_session, "dave", UserRole.REGULAR)
    admin = create_user(db_session, "admin", UserRole.ADMIN)
    room = create_room(db_session, "Room-C")
    create_booking(db_session, user.id, room.id)
    create_booking(db_session, admin.id, room.id)

    set_current_user(user)
    review = client.post(
        f"/api/v1/reviews/rooms/{room.id}",
        json={"rating": 3, "comment": "Average"},
    ).json()
    review_id = review["id"]

    update_resp = client.patch(
        f"/api/v1/reviews/{review_id}",
        json={"comment": "Updated comment"},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["comment"] == "Updated comment"

    clear_current_user()

    set_current_user(other)
    forbidden_resp = client.patch(
        f"/api/v1/reviews/{review_id}",
        json={"comment": "Should fail"},
    )
    assert forbidden_resp.status_code == 403
    clear_current_user()

    set_current_user(admin)
    admin_update = client.patch(
        f"/api/v1/reviews/{review_id}",
        json={"comment": "Admin edit"},
    )
    assert admin_update.status_code == 200

    delete_resp = client.delete(f"/api/v1/reviews/{review_id}")
    clear_current_user()
    assert delete_resp.status_code == 204


def test_regular_users_do_not_see_hidden_reviews(client: TestClient, db_session: Session):
    user = create_user(db_session, "erin", UserRole.REGULAR)
    admin = create_user(db_session, "eve", UserRole.ADMIN)
    room = create_room(db_session, "Room-D")
    create_booking(db_session, user.id, room.id)
    create_booking(db_session, admin.id, room.id)

    # create two reviews via ORM
    review_visible = Review(
        user_id=user.id,
        room_id=room.id,
        rating=5,
        comment="Visible",
        is_hidden=False,
    )
    review_hidden = Review(
        user_id=admin.id,
        room_id=room.id,
        rating=2,
        comment="Hidden",
        is_hidden=True,
    )
    db_session.add_all([review_visible, review_hidden])
    db_session.commit()

    set_current_user(user)
    response = client.get(f"/api/v1/reviews/rooms/{room.id}")
    clear_current_user()
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["comment"] == "Visible"
    assert response.json()[0]["is_hidden"] is None

    set_current_user(admin)
    admin_response = client.get(f"/api/v1/reviews/rooms/{room.id}")
    clear_current_user()
    assert admin_response.status_code == 200
    assert len(admin_response.json()) == 2
    hidden_comments = {item["comment"] for item in admin_response.json()}
    assert {"Visible", "Hidden"} == hidden_comments
    assert any(item["is_hidden"] is True for item in admin_response.json())


def test_flagging_and_moderation(client: TestClient, db_session: Session):
    user = create_user(db_session, "frank", UserRole.REGULAR)
    admin = create_user(db_session, "grace", UserRole.ADMIN)
    room = create_room(db_session, "Room-E")
    create_booking(db_session, user.id, room.id)
    create_booking(db_session, admin.id, room.id)

    set_current_user(user)
    review = client.post(
        f"/api/v1/reviews/rooms/{room.id}",
        json={"rating": 4, "comment": "Flag me"},
    ).json()
    review_id = review["id"]
    flag_resp = client.post(f"/api/v1/reviews/{review_id}/flag")
    clear_current_user()
    assert flag_resp.status_code == 200

    set_current_user(admin)
    hide_resp = client.post(
        f"/api/v1/reviews/{review_id}/moderate",
        json={"action": "hide"},
    )
    assert hide_resp.status_code == 200
    assert hide_resp.json()["is_hidden"] is True

    unhide_resp = client.post(
        f"/api/v1/reviews/{review_id}/moderate",
        json={"action": "unhide"},
    )
    assert unhide_resp.status_code == 200
    assert unhide_resp.json()["is_hidden"] is False

    clear_flags = client.post(
        f"/api/v1/reviews/{review_id}/moderate",
        json={"action": "clear_flags"},
    )
    clear_current_user()
    assert clear_flags.status_code == 200
    assert clear_flags.json()["is_flagged"] is False
