"""Users service FastAPI application."""

import logging
from typing import Any

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy import or_
from sqlalchemy.orm import Session

from common.auth import (
    create_access_token,
    get_current_user,
    get_password_hash,
    verify_password,
)
from common.db import get_db
from common.exceptions import AppError, AuthenticationError, ConflictError
from services.users_service import SERVICE_NAME
from services.users_service.models import User, UserRole
from services.users_service.schemas import Token, UserCreate, UserLogin, UserOut

logger = logging.getLogger(__name__)
app = FastAPI(title="Users Service")
router = APIRouter(prefix="/api/v1/users", tags=["users"])


@app.exception_handler(AppError)
async def handle_app_error(request: Request, exc: AppError):
    """Normalize AppError responses."""

    logger.warning("AppError on %s: %s", request.url.path, exc.message)
    return JSONResponse(status_code=exc.status_code, content=exc.to_dict())


@app.exception_handler(HTTPException)
async def handle_http_exception(request: Request, exc: HTTPException):
    """Return consistent payload for FastAPI HTTPException usage."""

    logger.warning(
        "HTTPException on %s: %s (status=%s)", request.url.path, exc.detail, exc.status_code
    )
    content = {"error_code": "HTTP_EXCEPTION", "message": exc.detail, "details": None}
    return JSONResponse(status_code=exc.status_code, content=content)


@app.exception_handler(Exception)
async def handle_generic_exception(request: Request, exc: Exception):
    """Catch-all handler to keep responses predictable."""

    logger.exception("Unhandled exception on %s", request.url.path)
    content = {
        "error_code": "INTERNAL_SERVER_ERROR",
        "message": "An unexpected error occurred",
        "details": None,
    }
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=content)


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register_user(
    user_in: UserCreate,
    db: Session = Depends(get_db),
):
    """Register a new user with the REGULAR role by default."""

    existing_user = (
        db.query(User)
        .filter(or_(User.username == user_in.username, User.email == user_in.email))
        .first()
    )
    if existing_user:
        raise ConflictError("Username or email already registered")

    user = User(
        username=user_in.username,
        email=user_in.email,
        full_name=user_in.full_name,
        password_hash=get_password_hash(user_in.password),
        role=UserRole.REGULAR,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(
    login_data: UserLogin,
    db: Session = Depends(get_db),
):
    """Authenticate a user and return a JWT bearer token."""

    user = db.query(User).filter(User.username == login_data.username).first()
    if not user or not verify_password(login_data.password, user.password_hash):
        raise AuthenticationError("Incorrect username or password")

    token_payload: dict[str, Any] = {
        "sub": user.username,
        "role": getattr(user.role, "value", user.role),
    }
    access_token = create_access_token(data=token_payload)
    return Token(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=UserOut)
async def read_current_user(current_user=Depends(get_current_user)):
    """Return the authenticated user's profile."""

    return current_user


@router.get("/health", include_in_schema=False)
async def health_check() -> dict[str, str]:
    """Health probe used by orchestrators and tests."""

    return {"status": "ok", "service": SERVICE_NAME}


app.include_router(router)
