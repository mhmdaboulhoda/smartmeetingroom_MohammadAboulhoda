"""Unit tests for the rooms cache behavior."""

import time
from types import SimpleNamespace

import pytest

from services.rooms_service import service as rooms_service
from services.rooms_service.cache import RoomsCache
from services.rooms_service.schemas import RoomCreate, RoomUpdate


class DummySession:
    def __init__(self):
        self.calls = 0
        self.rooms = []

    def query(self, model):
        return self

    def filter(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def all(self):
        self.calls += 1
        return self.rooms

    def add(self, obj):
        self.obj = obj

    def commit(self):
        pass

    def refresh(self, obj):
        pass

    def get(self, model, id):
        for room in self.rooms:
            if getattr(room, "id", None) == id:
                return room
        return None

    def delete(self, obj):
        pass


@pytest.fixture(autouse=True)
def reset_cache(monkeypatch):
    cache = RoomsCache(ttl_seconds=60)
    monkeypatch.setattr(rooms_service, "rooms_cache", cache)
    yield
    cache.invalidate()


def test_cache_hit_vs_miss(monkeypatch):
    session = DummySession()

    def fake_query(model):
        return session

    monkeypatch.setattr(DummySession, "query", lambda self, model: session)
    rooms_service.list_rooms(session)
    assert session.calls == 1
    rooms_service.list_rooms(session)
    assert session.calls == 1


def test_cache_invalidation_on_write(monkeypatch):
    session = DummySession()

    def fake_query(model):
        return session

    monkeypatch.setattr(DummySession, "query", lambda self, model: session)
    rooms_service.list_rooms(session)
    assert session.calls == 1
    rooms_service.invalidate_rooms_cache_for_room(None)
    rooms_service.list_rooms(session)
    assert session.calls == 2


def test_cache_ttl_expiration(monkeypatch):
    cache = RoomsCache(ttl_seconds=1)
    monkeypatch.setattr(rooms_service, "rooms_cache", cache)
    session = DummySession()
    monkeypatch.setattr(DummySession, "query", lambda self, model: session)
    rooms_service.list_rooms(session)
    assert session.calls == 1
    time.sleep(1.1)
    rooms_service.list_rooms(session)
    assert session.calls == 2
