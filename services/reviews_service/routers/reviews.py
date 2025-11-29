"""Reviews API router."""

from typing import List

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from common.auth import get_current_user, require_roles
from common.db import get_db
from services.reviews_service import SERVICE_NAME
from services.reviews_service.schemas import (
    ReviewCreate,
    ReviewModerationAction,
    ReviewOut,
    ReviewUpdate,
)
from services.reviews_service.service import (
    create_review,
    delete_review,
    flag_review,
    list_reviews_for_room,
    moderate_review,
    update_review,
)

router = APIRouter(prefix="/api/v1/reviews", tags=["reviews"])


@router.post("/rooms/{room_id}", response_model=ReviewOut)
def create_review_endpoint(
    room_id: int,
    review_in: ReviewCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("ADMIN", "FACILITY_MANAGER", "REGULAR")),
):
    """Create a review for a room."""

    return create_review(db, current_user, room_id, review_in)


@router.get("/rooms/{room_id}", response_model=List[ReviewOut])
def list_reviews_endpoint(
    room_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List reviews for a room respecting moderation visibility."""

    return list_reviews_for_room(db, room_id, current_user)


@router.patch("/{review_id}", response_model=ReviewOut)
def update_review_endpoint(
    review_id: int,
    review_update: ReviewUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update a review (author or admins)."""

    return update_review(db, current_user, review_id, review_update)


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review_endpoint(
    review_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Soft-delete a review."""

    delete_review(db, current_user, review_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{review_id}/flag", response_model=ReviewOut)
def flag_review_endpoint(
    review_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Flag a review for moderator attention."""

    return flag_review(db, current_user, review_id)


@router.post("/{review_id}/moderate", response_model=ReviewOut)
def moderate_review_endpoint(
    review_id: int,
    action: ReviewModerationAction,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("ADMIN")),
):
    """Moderate a review (hide/unhide/clear flags)."""

    return moderate_review(db, current_user, review_id, action.action)


@router.get("/health", include_in_schema=False)
async def health_check() -> dict[str, str]:
    """Health probe for orchestrators."""

    return {"status": "ok", "service": SERVICE_NAME}
