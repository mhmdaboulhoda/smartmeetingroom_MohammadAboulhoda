"""Authentication helpers shared across services."""

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from common.config import settings
from common.db import get_db

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Return True when the provided password matches the stored hash."""

    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a plaintext password using bcrypt."""

    return pwd_context.hash(password)


def create_access_token(data: dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT with optional expiry override."""

    to_encode = data.copy()
    expire_delta = expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    expire = datetime.now(timezone.utc) + expire_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    """Decode the JWT and return the associated user."""

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        username: Optional[str] = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError as exc:
        raise credentials_exception from exc

    from services.users_service.models import User  # Local import to avoid circular dependency

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user


def require_roles(*roles: str):
    """Return a dependency enforcing RBAC based on the authenticated user."""

    normalized_roles = {role.upper() for role in roles if role}

    async def dependency(current_user=Depends(get_current_user)):
        role_value = getattr(current_user.role, "value", current_user.role)
        normalized_value = role_value.upper()
        if normalized_roles and normalized_value not in normalized_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return dependency
