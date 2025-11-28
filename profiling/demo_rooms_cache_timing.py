"""Quick script to demonstrate rooms cache timing differences."""

import time

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from services.rooms_service import service as rooms_service
from services.rooms_service.models import Room, RoomStatus


def seed_rooms(session):
    existing = session.query(Room).count()
    if existing >= 5:
        return
    for idx in range(5):
        room = Room(
            name=f"CacheDemoRoom-{idx}",
            capacity=10 + idx,
            location="CacheHQ",
            status=RoomStatus.AVAILABLE,
            equipment={},
        )
        session.add(room)
    session.commit()


def measure(session):
    start = time.perf_counter()
    rooms_service.list_rooms(session, location="CacheHQ")
    first = time.perf_counter() - start

    start = time.perf_counter()
    rooms_service.list_rooms(session, location="CacheHQ")
    second = time.perf_counter() - start

    print(f"first call: {first * 1000:.2f} ms, second (cached): {second * 1000:.2f} ms")


if __name__ == "__main__":
    engine = create_engine("sqlite:///rooms_cache_demo.db", connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    from common.db import Base

    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        seed_rooms(session)
        measure(session)
