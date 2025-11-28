"""Users service FastAPI application."""

from typing import Any

from fastapi import APIRouter, Depends, FastAPI, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from common.auth import (
    create_access_token,
    get_current_user,
    get_password_hash,
    verify_password,
)
from common.db import get_db
from services.users_service import SERVICE_NAME
from services.users_service.models import User, UserRole
from services.users_service.schemas import Token, UserCreate, UserLogin, UserOut

app = FastAPI(title="Users Service")
router = APIRouter(prefix="/api/v1/users", tags=["users"])


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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered",
        )

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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

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


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health probe used by orchestrators and tests."""

    return {"status": "ok", "service": SERVICE_NAME}


app.include_router(router)
