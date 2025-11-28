"""Ensure SQLAlchemy models expose the required indexes."""

from services.bookings_service.models import Booking
from services.reviews_service.models import Review
from services.rooms_service.models import Room
from services.users_service.models import User


def _index_column_sets(table):
    return {tuple(index.columns.keys()) for index in table.indexes}


def test_user_indexes():
    columns = _index_column_sets(User.__table__)
    assert ("username",) in columns
    assert ("email",) in columns


def test_room_indexes():
    columns = _index_column_sets(Room.__table__)
    assert ("name",) in columns
    assert ("status",) in columns
    assert ("location",) in columns


def test_booking_indexes():
    columns = _index_column_sets(Booking.__table__)
    assert ("room_id", "start_time") in columns
    assert ("user_id",) in columns


def test_review_indexes():
    columns = _index_column_sets(Review.__table__)
    assert ("room_id",) in columns
    assert ("user_id",) in columns
