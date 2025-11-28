"""Business logic for managing bookings."""

from datetime import datetime
from typing import List

from fastapi import status
from sqlalchemy.orm import Session

from common.exceptions import AppError, NotFoundError
from services.bookings_service.models import Booking, BookingStatus
from services.bookings_service.schemas import BookingCreate, BookingOut, BookingUpdate, RoomRef, UserRef
from services.rooms_service.models import Room, RoomStatus


def _role_value(user) -> str:
    value = getattr(user.role, "value", user.role)
    return value.upper() if isinstance(value, str) else str(value).upper()


def _validate_time_range(start_time: datetime, end_time: datetime) -> None:
    if start_time >= end_time:
        raise AppError(
            "End time must be after start time",
            error_code="INVALID_TIME_RANGE",
            status_code=status.HTTP_400_BAD_REQUEST,
        )


def _ensure_room_available(db: Session, room_id: int) -> Room:
    room = db.get(Room, room_id)
    if not room:
        raise NotFoundError("Room not found")
    if room.status == RoomStatus.OUT_OF_SERVICE:
        raise AppError(
            "Room is out of service",
            error_code="ROOM_OUT_OF_SERVICE",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    return room


def _check_overlap(db: Session, room_id: int, start_time: datetime, end_time: datetime) -> None:
    conflict = (
        db.query(Booking)
        .filter(
            Booking.room_id == room_id,
            Booking.status == BookingStatus.CONFIRMED,
            Booking.start_time < end_time,
            Booking.end_time > start_time,
        )
        .first()
    )
    if conflict:
        raise AppError(
            "Room already booked for the selected time range",
            error_code="BOOKING_CONFLICT",
            status_code=status.HTTP_409_CONFLICT,
        )


def _serialize(booking: Booking) -> BookingOut:
    return BookingOut(
        id=booking.id,
        user=UserRef(id=booking.user_id),
        room=RoomRef(id=booking.room_id),
        start_time=booking.start_time,
        end_time=booking.end_time,
        status=booking.status,
        created_at=booking.created_at,
    )


def create_booking(db: Session, current_user, booking_in: BookingCreate) -> BookingOut:
    """Create a confirmed booking for the requesting user."""

    _validate_time_range(booking_in.start_time, booking_in.end_time)
    _ensure_room_available(db, booking_in.room_id)
    _check_overlap(db, booking_in.room_id, booking_in.start_time, booking_in.end_time)

    booking = Booking(
        user_id=current_user.id,
        room_id=booking_in.room_id,
        start_time=booking_in.start_time,
        end_time=booking_in.end_time,
        status=BookingStatus.CONFIRMED,
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return _serialize(booking)


def list_bookings_for_user(db: Session, current_user) -> List[BookingOut]:
    bookings = (
        db.query(Booking)
        .filter(Booking.user_id == current_user.id)
        .order_by(Booking.start_time.asc())
        .all()
    )
    return [_serialize(b) for b in bookings]


def list_all_bookings(db: Session, current_user) -> List[BookingOut]:
    role = _role_value(current_user)
    if role not in {"ADMIN", "FACILITY_MANAGER"}:
        raise AppError(
            "Only Admins or Facility Managers can view all bookings",
            error_code="BOOKING_FORBIDDEN",
            status_code=status.HTTP_403_FORBIDDEN,
        )
    bookings = db.query(Booking).order_by(Booking.start_time.asc()).all()
    return [_serialize(b) for b in bookings]


def cancel_booking(db: Session, current_user, booking_id: int) -> BookingOut:
    booking = db.get(Booking, booking_id)
    if not booking:
        raise NotFoundError("Booking not found")

    role = _role_value(current_user)
    owns_booking = booking.user_id == current_user.id
    if not owns_booking and role not in {"ADMIN", "FACILITY_MANAGER"}:
        raise AppError(
            "You do not have permission to cancel this booking",
            error_code="BOOKING_FORBIDDEN",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    if not owns_booking and role == "ADMIN":
        # Documented behavior: Admins overriding someone else mark booking as OVERRIDDEN.
        booking.status = BookingStatus.OVERRIDDEN
    else:
        booking.status = BookingStatus.CANCELED

    db.add(booking)
    db.commit()
    db.refresh(booking)
    return _serialize(booking)
