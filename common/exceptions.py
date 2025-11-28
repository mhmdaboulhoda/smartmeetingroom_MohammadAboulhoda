"""Application-specific exceptions for FastAPI services."""

from typing import Any, Optional

from fastapi import status


class AppError(Exception):
    """Base exception carrying HTTP-friendly metadata."""

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code: str = "APP_ERROR"

    def __init__(
        self,
        message: str,
        *,
        details: Optional[Any] = None,
        error_code: Optional[str] = None,
        status_code: Optional[int] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.details = details
        if error_code:
            self.error_code = error_code
        if status_code:
            self.status_code = status_code

    def to_dict(self) -> dict[str, Any]:
        return {"error_code": self.error_code, "message": self.message, "details": self.details}


class ConflictError(AppError):
    status_code = status.HTTP_409_CONFLICT
    error_code = "CONFLICT_ERROR"


class AuthenticationError(AppError):
    status_code = status.HTTP_401_UNAUTHORIZED
    error_code = "AUTHENTICATION_ERROR"


class AuthorizationError(AppError):
    status_code = status.HTTP_403_FORBIDDEN
    error_code = "AUTHORIZATION_ERROR"


class NotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    error_code = "NOT_FOUND_ERROR"
