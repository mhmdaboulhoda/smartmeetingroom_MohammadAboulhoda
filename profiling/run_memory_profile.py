#!/usr/bin/env python
"""Memory profiler entrypoint for hot service code paths."""

from memory_profiler import profile

from services.bookings_service.service import create_booking
from services.rooms_service.service import list_rooms
from profiling.targets.profiling_utils import (
    build_booking_payload,
    get_regular_user,
    get_room_id,
    get_session,
)


@profile
def memory_profile_rooms_listing():
    session = get_session()
    try:
        get_room_id(session)
        list_rooms(session)
    finally:
        session.close()


@profile
def memory_profile_booking_creation():
    session = get_session()
    try:
        room_id = get_room_id(session)
        current_user = get_regular_user(session)
        payload = build_booking_payload(room_id)
        create_booking(session, current_user, payload)
    finally:
        session.close()


if __name__ == "__main__":
    memory_profile_rooms_listing()
    memory_profile_booking_creation()
