"""Authentication helpers shared across services."""

from typing import Optional

from fastapi import Depends, HTTPException, status

from common.config import settings


# TODO: replace with a real authentication provider or JWT validation logic.
def get_current_user(token: Optional[str] = None):
    """Very small placeholder used to sketch dependency injection."""
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")
    return {"token": token, "environment": settings.environment}
