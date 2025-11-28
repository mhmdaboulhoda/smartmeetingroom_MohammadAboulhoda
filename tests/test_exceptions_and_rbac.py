"""Tests for global exception handling and RBAC responses."""

from types import SimpleNamespace
from typing import Generator

import pytest
from fastapi import APIRouter, Depends, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from common.auth import get_current_user
from common.db import Base, get_db
from services.rooms_service.app import app
from services.rooms_service.models import Room
from services.users_service.models import User, UserRole

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False)


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
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=1, role="ADMIN")
    router = APIRouter()

    @router.get("/api/v1/rooms/internal/bomb")
    def bomb_endpoint(current_user=Depends(get_current_user)):
        raise RuntimeError("Simulated failure")

    app.include_router(router)
    yield
    app.router.routes.pop()
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_user, None)
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app, raise_server_exceptions=False)


def test_not_found_returns_standard_error(client: TestClient):
    response = client.get("/api/v1/rooms/9999")
    assert response.status_code == 404
    body = response.json()
    assert set(body.keys()) == {"error_code", "message", "details"}
    assert body["error_code"] == "NOT_FOUND_ERROR"


def test_unauthorized_user_sees_consistent_error_shape(client: TestClient):
    app.dependency_overrides.pop(get_current_user, None)
    response = client.post(
        "/api/v1/rooms/",
        json={"name": "Test", "capacity": 5, "location": "HQ", "equipment": {}, "status": "AVAILABLE"},
    )
    assert response.status_code in {401, 403}
    body = response.json()
    assert set(body.keys()) == {"error_code", "message", "details"}
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=1, role="ADMIN")


def test_internal_server_error_wrapped(client: TestClient):
    response = client.get("/api/v1/rooms/internal/bomb")
    assert response.status_code == 500
    body = response.json()
    assert set(body.keys()) == {"error_code", "message", "details"}
    assert body["error_code"] == "INTERNAL_SERVER_ERROR"
