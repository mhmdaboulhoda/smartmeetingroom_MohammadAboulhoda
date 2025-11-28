"""Integration-style tests for the Users service FastAPI app."""

from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from common.db import Base, get_db
from services.users_service.app import app

SQLALCHEMY_DATABASE_URL = "sqlite+pysqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def setup_test_db() -> Generator[None, None, None]:
    """Create a clean in-memory DB and override the dependency."""

    Base.metadata.create_all(bind=engine)

    def _get_test_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _get_test_db
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_db, None)
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def register_user(client: TestClient, username: str = "alice") -> dict:
    payload = {
        "username": username,
        "email": f"{username}@example.com",
        "full_name": "Alice Example",
        "password": "StrongPassw0rd!",
    }
    response = client.post("/api/v1/users/register", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def login_user(client: TestClient, username: str, password: str):
    response = client.post(
        "/api/v1/users/login",
        json={"username": username, "password": password},
    )
    return response


def test_register_user_creates_account(client: TestClient):
    data = register_user(client)
    assert data["username"] == "alice"
    assert data["email"] == "alice@example.com"
    assert "password_hash" not in data


def test_login_returns_token(client: TestClient):
    register_user(client, username="bob")
    response = login_user(client, "bob", "StrongPassw0rd!")
    assert response.status_code == 200
    payload = response.json()
    assert payload["token_type"] == "bearer"
    assert payload["access_token"]


def test_login_fails_with_wrong_password(client: TestClient):
    register_user(client, username="carol")
    response = login_user(client, "carol", "BadPassword!")
    assert response.status_code == 401
    payload = response.json()
    assert payload["error_code"] == "AUTHENTICATION_ERROR"


def test_me_endpoint_with_token(client: TestClient):
    register_user(client, username="dave")
    login_response = login_user(client, "dave", "StrongPassw0rd!")
    token = login_response.json()["access_token"]
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["username"] == "dave"


def test_me_endpoint_without_token(client: TestClient):
    register_user(client, username="erin")
    response = client.get("/api/v1/users/me")
    assert response.status_code == 401
    payload = response.json()
    assert payload["error_code"] == "HTTP_EXCEPTION"
