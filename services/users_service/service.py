"""Domain logic for the Users service."""

import logging
from typing import Any

from fastapi import status
from sqlalchemy.orm import Session

from common.auth import create_access_token, get_password_hash, verify_password
from common.exceptions import AuthenticationError, ConflictError
from services.users_service.models import User, UserRole
from services.users_service.schemas import Token, UserCreate, UserLogin

logger = logging.getLogger(__name__)


def register_user(db: Session, user_in: UserCreate) -> User:
    """Persist a new user with the requested role (default REGULAR)."""

    logger.info("Registering user %s", user_in.username)
    existing_user = (
        db.query(User)
        .filter((User.username == user_in.username) | (User.email == user_in.email))
        .first()
    )
    if existing_user:
        raise ConflictError("Username or email already registered")

    user = User(
        username=user_in.username,
        email=user_in.email,
        full_name=user_in.full_name,
        password_hash=get_password_hash(user_in.password),
        role=user_in.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def login_user(db: Session, credentials: UserLogin) -> Token:
    """Authenticate a user and return a JWT access token."""

    logger.debug("Authenticating user %s", credentials.username)
    user = db.query(User).filter(User.username == credentials.username).first()
    if not user or not verify_password(credentials.password, user.password_hash):
        raise AuthenticationError("Incorrect username or password")

    token_payload: dict[str, Any] = {
        "sub": user.username,
        "role": getattr(user.role, "value", user.role),
    }
    access_token = create_access_token(data=token_payload)
    logger.info("User %s logged in successfully", credentials.username)
    return Token(access_token=access_token, token_type="bearer")
