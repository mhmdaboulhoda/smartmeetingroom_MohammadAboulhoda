"""Business logic for the reviews service."""

import logging
from typing import Any, List

from fastapi import status
from sqlalchemy.orm import Session

from common.exceptions import AppError, NotFoundError
from services.bookings_service.models import Booking, BookingStatus
from services.reviews_service.models import Review
from services.reviews_service.schemas import ReviewCreate, ReviewOut, ReviewUpdate
from services.rooms_service.models import Room

logger = logging.getLogger(__name__)


def _role_value(user: Any) -> str:
    value = getattr(user.role, "value", user.role)
    if isinstance(value, str):
        return value.upper()
    return str(value).upper()


def _is_moderator(user: Any) -> bool:
    return _role_value(user) in {"ADMIN", "FACILITY_MANAGER"}


def _is_admin(user: Any) -> bool:
    return _role_value(user) == "ADMIN"


def _serialize_review(review: Review, include_flags: bool) -> ReviewOut:
    data = ReviewOut.model_validate(review)
    if not include_flags:
        data.is_flagged = None
        data.is_hidden = None
    return data


def _ensure_room_exists(db: Session, room_id: int) -> Room:
    room = db.get(Room, room_id)
    if not room:
        raise NotFoundError("Room not found")
    return room


def _ensure_user_has_booking(db: Session, user_id: int, room_id: int) -> None:
    booking_exists = (
        db.query(Booking)
        .filter(
            Booking.user_id == user_id,
            Booking.room_id == room_id,
            Booking.status == BookingStatus.CONFIRMED,
        )
        .first()
    )
    if not booking_exists:
        raise AppError(
            "You must have a confirmed booking for this room before leaving a review",
            error_code="REVIEW_REQUIRES_BOOKING",
            status_code=status.HTTP_403_FORBIDDEN,
        )


def create_review(db: Session, current_user: Any, room_id: int, payload: ReviewCreate) -> ReviewOut:
    """Persist a review when the user has an active booking."""

    _ensure_room_exists(db, room_id)
    _ensure_user_has_booking(db, current_user.id, room_id)
    logger.info("User %s creating review for room %s", current_user.id, room_id)

    review = Review(
        user_id=current_user.id,
        room_id=room_id,
        rating=payload.rating,
        comment=payload.comment,
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return _serialize_review(review, include_flags=_is_moderator(current_user))


def update_review(
    db: Session,
    current_user: Any,
    review_id: int,
    review_update: ReviewUpdate,
) -> ReviewOut:
    """Update an existing review; moderators may edit any review."""

    review = db.get(Review, review_id)
    if not review:
        raise NotFoundError("Review not found")
    if review.user_id != current_user.id and not _is_admin(current_user):
        raise AppError(
            "You do not have permission to modify this review",
            error_code="REVIEW_FORBIDDEN",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    update_data = review_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(review, field, value)
    db.add(review)
    db.commit()
    db.refresh(review)
    logger.debug("Review %s updated", review_id)
    return _serialize_review(review, include_flags=_is_moderator(current_user))


def delete_review(db: Session, current_user: Any, review_id: int) -> None:
    """Soft-delete a review by hiding it from public listings."""

    review = db.get(Review, review_id)
    if not review:
        raise NotFoundError("Review not found")
    if review.user_id != current_user.id and not _is_admin(current_user):
        raise AppError(
            "You do not have permission to delete this review",
            error_code="REVIEW_FORBIDDEN",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    review.is_hidden = True
    db.add(review)
    db.commit()
    logger.info("Review %s marked as hidden", review_id)


def list_reviews_for_room(db: Session, room_id: int, current_user: Any) -> List[ReviewOut]:
    """Return reviews for a room, optionally including moderation flags."""

    _ensure_room_exists(db, room_id)
    include_flags = _is_moderator(current_user)
    query = db.query(Review).filter(Review.room_id == room_id)
    if not include_flags:
        query = query.filter(Review.is_hidden.is_(False))
    reviews = query.order_by(Review.created_at.desc()).all()
    return [_serialize_review(review, include_flags) for review in reviews]


def flag_review(db: Session, current_user: Any, review_id: int) -> ReviewOut:
    """Flag a review for moderator attention."""

    review = db.get(Review, review_id)
    if not review:
        raise NotFoundError("Review not found")
    review.is_flagged = True
    db.add(review)
    db.commit()
    db.refresh(review)
    logger.info("Review %s flagged by user %s", review_id, current_user.id)
    return _serialize_review(review, include_flags=_is_moderator(current_user))


def moderate_review(db: Session, current_user: Any, review_id: int, action: str) -> ReviewOut:
    """Allow admins to hide/unhide or clear flags on reviews."""

    if not _is_admin(current_user):
        raise AppError(
            "Only admins can moderate reviews",
            error_code="REVIEW_FORBIDDEN",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    review = db.get(Review, review_id)
    if not review:
        raise NotFoundError("Review not found")

    normalized_action = action.lower()
    if normalized_action == "hide":
        review.is_hidden = True
    elif normalized_action == "unhide":
        review.is_hidden = False
    elif normalized_action == "clear_flags":
        review.is_flagged = False
    else:
        raise AppError(
            "Unsupported moderation action",
            error_code="REVIEW_INVALID_ACTION",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    db.add(review)
    db.commit()
    db.refresh(review)
    logger.info("Review %s moderated with action %s", review_id, normalized_action)
    return _serialize_review(review, include_flags=True)
