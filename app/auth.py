"""Authentication utilities for the FastAPI service."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext

from .config import Settings, get_settings
from .models import Token, TokenData, User, UserInDB

# Demo user store; production systems should use a proper database
_FAKE_USERS_DB: Dict[str, UserInDB] = {
    "data.engineer": UserInDB(
        username="data.engineer",
        full_name="Data Engineer",
        hashed_password=CryptContext(schemes=["bcrypt"]).hash("changeme"),
    )
}

_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hashed password."""

    return _pwd_context.verify(plain_password, hashed_password)


def get_user(username: str) -> Optional[UserInDB]:
    """Retrieve a user from the in-memory store."""

    return _FAKE_USERS_DB.get(username)


def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    """Authenticate username/password and return the user if valid."""

    user = get_user(username)
    if user is None or not verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token(data: dict, settings: Settings) -> str:
    """Create a signed JWT access token."""

    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    settings: Settings = Depends(get_settings),
) -> Token:
    """OAuth2-compatible login endpoint."""

    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token({"sub": user.username}, settings=settings)
    return Token(access_token=access_token)


def get_current_user(
    token: str = Depends(_oauth2_scheme),
    settings: Settings = Depends(get_settings),
) -> User:
    """Resolve the user from a bearer token."""

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
    except JWTError as exc:  # pragma: no cover - error path
        raise credentials_exception from exc
    user = get_user(username)
    if user is None:
        raise credentials_exception
    if user.disabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return user
