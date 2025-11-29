"""Users API router."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from common.auth import get_current_user
from common.db import get_db
from services.users_service import SERVICE_NAME
from services.users_service.models import User
from services.users_service.schemas import Token, UserCreate, UserLogin, UserOut
from services.users_service.service import login_user, register_user

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register_user_endpoint(user_in: UserCreate, db: Session = Depends(get_db)) -> UserOut:
    """Register a new user with REGULAR role by default."""

    return register_user(db, user_in)


@router.post("/login", response_model=Token)
def login_endpoint(credentials: UserLogin, db: Session = Depends(get_db)) -> Token:
    """Authenticate a user and issue a JWT bearer token."""

    return login_user(db, credentials)


@router.get("/me", response_model=UserOut)
def read_current_user_endpoint(current_user: User = Depends(get_current_user)) -> User:
    """Return the authenticated user's profile."""

    return current_user


@router.get("/health", include_in_schema=False)
async def health_check() -> dict[str, str]:
    """Health probe used by orchestrators and tests."""

    return {"status": "ok", "service": SERVICE_NAME}
