"""Shared FastAPI dependencies for authentication and authorization."""

from typing import Optional

from fastapi import Cookie, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from . import models
from .config import settings
from .database import get_db
from .security import decode_access_token

SESSION_COOKIE = "access_token"


def get_current_user(
    access_token: Optional[str] = Cookie(default=None),
    db: Session = Depends(get_db),
) -> models.User:
    """Resolve the logged-in user from the session cookie or raise 401."""
    if access_token is None:
        raise HTTPException(status_code=401, detail="Not logged in")

    user_id = decode_access_token(access_token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Session expired or invalid")

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User no longer exists")
    return user


def require_admin(
    user: models.User = Depends(get_current_user),
) -> models.User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


def require_agent_key(x_api_key: Optional[str] = Header(default=None)) -> None:
    """Agents authenticate with a shared key header, not a user session."""
    if not settings.agent_api_key or x_api_key != settings.agent_api_key:
        raise HTTPException(status_code=401, detail="Invalid or missing agent API key")
