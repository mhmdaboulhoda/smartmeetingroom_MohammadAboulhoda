"""Bookings API router."""

from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from common.auth import get_current_user, require_roles
from common.db import get_db
from services.bookings_service import SERVICE_NAME
from services.bookings_service.schemas import BookingCreate, BookingOut
from services.bookings_service.service import (
    cancel_booking,
    create_booking,
    list_all_bookings,
    list_bookings_for_user,
)

router = APIRouter(prefix="/api/v1/bookings", tags=["bookings"])


@router.post(
    "/",
    response_model=BookingOut,
    status_code=status.HTTP_201_CREATED,
)
def create_booking_endpoint(
    booking_in: BookingCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("ADMIN", "FACILITY_MANAGER", "REGULAR")),
):
    """Create a booking for the authenticated user (regulars, facility managers, admins)."""

    return create_booking(db, current_user, booking_in)


@router.get("/me", response_model=List[BookingOut])
def list_my_bookings(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Return bookings for the current user."""

    return list_bookings_for_user(db, current_user)


@router.get("/", response_model=List[BookingOut])
def list_all_bookings_endpoint(
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("ADMIN", "FACILITY_MANAGER")),
):
    """Admins and facility managers can list all bookings."""

    return list_all_bookings(db, current_user)


@router.post("/{booking_id}/cancel", response_model=BookingOut)
def cancel_booking_endpoint(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Cancel a booking based on the RBAC rules."""

    return cancel_booking(db, current_user, booking_id)


@router.get("/health", include_in_schema=False)
def health_check() -> dict[str, str]:
    """Health probe for orchestrators."""

    return {"status": "ok", "service": SERVICE_NAME}
