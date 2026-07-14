from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..config import settings
from ..database import get_db
from ..deps import SESSION_COOKIE, get_current_user
from ..security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    """Create an account. The first account ever becomes the admin."""
    existing = (
        db.query(models.User)
        .filter(models.User.username == payload.username)
        .first()
    )
    if existing is not None:
        raise HTTPException(status_code=409, detail="Username is already taken")

    role = "admin" if db.query(models.User).count() == 0 else "technician"
    user = models.User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=schemas.UserOut)
def login(payload: schemas.LoginIn, response: Response, db: Session = Depends(get_db)):
    user = (
        db.query(models.User)
        .filter(models.User.username == payload.username)
        .first()
    )
    if user is None or not verify_password(payload.password, user.password_hash):
        # Same message for both cases so usernames can't be probed.
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_access_token(user.id)
    # HttpOnly keeps the token away from JS; SameSite=Lax is the CSRF defense.
    # No `secure` flag until HTTPS exists — it would break login on LAN HTTP.
    response.set_cookie(
        key=SESSION_COOKIE,
        value=token,
        httponly=True,
        samesite="lax",
        max_age=settings.access_token_expire_minutes * 60,
    )
    return user


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(SESSION_COOKIE)
    return {"status": "logged out"}


@router.get("/me", response_model=schemas.UserOut)
def me(user: models.User = Depends(get_current_user)):
    """Used by the frontend to check the session and get the user's role."""
    return user
