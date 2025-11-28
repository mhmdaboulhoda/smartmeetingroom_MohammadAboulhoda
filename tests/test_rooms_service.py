"""Tests for the Rooms service API and caching layer."""

from types import SimpleNamespace
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from common.auth import get_current_user
from common.db import Base, get_db
from services.rooms_service.app import app
from services.rooms_service.cache import rooms_cache
from services.rooms_service.models import RoomStatus

QUERY_COUNTER = {"count": 0}


class CountingSession(Session):
    def query(self, *args, **kwargs):  # type: ignore[override]
        QUERY_COUNTER["count"] += 1
        return super().query(*args, **kwargs)


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=CountingSession,
    expire_on_commit=False,
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
    rooms_cache.invalidate()
    app.dependency_overrides[get_db] = override_get_db
    yield
    rooms_cache.invalidate()
    app.dependency_overrides.pop(get_db, None)
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def set_current_user():
    def _set(role: str = "ADMIN"):
        app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
            id=1,
            role=role,
        )

    _set("ADMIN")
    yield _set
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def query_counter():
    QUERY_COUNTER["count"] = 0
    yield QUERY_COUNTER
    QUERY_COUNTER["count"] = 0


def create_room_payload(name="Room A", capacity=10, location="HQ", status="AVAILABLE"):
    return {
        "name": name,
        "capacity": capacity,
        "location": location,
        "equipment": {"projector": True},
        "status": status,
    }


def create_room_via_api(client: TestClient, payload=None):
    data = payload or create_room_payload()
    response = client.post("/api/v1/rooms/", json=data)
    assert response.status_code == 201, response.text
    return response.json()


def test_admin_can_create_room(client: TestClient, set_current_user):
    response = client.post("/api/v1/rooms/", json=create_room_payload())
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Room A"
    assert body["status"] == RoomStatus.AVAILABLE.value


def test_regular_user_cannot_create_room(client: TestClient, set_current_user):
    set_current_user("REGULAR")
    response = client.post("/api/v1/rooms/", json=create_room_payload("Room B"))
    assert response.status_code == 403
    assert response.json()["error_code"] == "HTTP_EXCEPTION"


def test_list_rooms_with_filters(client: TestClient, set_current_user):
    create_room_via_api(client, create_room_payload("Room A", capacity=4, location="HQ1"))
    create_room_via_api(client, create_room_payload("Room B", capacity=12, location="HQ2"))

    set_current_user("REGULAR")
    response = client.get("/api/v1/rooms")
    assert response.status_code == 200
    assert len(response.json()) == 2

    response = client.get("/api/v1/rooms", params={"location": "HQ1"})
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "Room A"

    response = client.get("/api/v1/rooms", params={"min_capacity": 10})
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "Room B"


def test_facility_manager_can_update_status(client: TestClient, set_current_user):
    room = create_room_via_api(client, create_room_payload("Room C"))
    set_current_user("FACILITY_MANAGER")
    response = client.patch(
        f"/api/v1/rooms/{room['id']}",
        json={"status": RoomStatus.OUT_OF_SERVICE.value},
    )
    assert response.status_code == 200
    assert response.json()["status"] == RoomStatus.OUT_OF_SERVICE.value


def test_admin_can_delete_room(client: TestClient, set_current_user):
    room = create_room_via_api(client, create_room_payload("Room D"))
    response = client.delete(f"/api/v1/rooms/{room['id']}")
    assert response.status_code == 204

    set_current_user("REGULAR")
    response = client.get(f"/api/v1/rooms/{room['id']}")
    assert response.status_code == 404
    assert response.json()["error_code"] == "NOT_FOUND_ERROR"


def test_list_rooms_uses_cache(client: TestClient, set_current_user, query_counter):
    create_room_via_api(client, create_room_payload("Room E", location="HQ-C"))
    QUERY_COUNTER["count"] = 0
    set_current_user("REGULAR")

    response = client.get("/api/v1/rooms", params={"location": "HQ-C"})
    assert response.status_code == 200
    first_count = query_counter["count"]
    assert first_count >= 1

    response = client.get("/api/v1/rooms", params={"location": "HQ-C"})
    assert response.status_code == 200
    assert query_counter["count"] == first_count
