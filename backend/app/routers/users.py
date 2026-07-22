from typing import List

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import require_admin

router = APIRouter(prefix="/api/users", tags=["users"])


def _admin_count(db: Session) -> int:
    return db.query(models.User).filter(models.User.role == "admin").count()


@router.get("", response_model=List[schemas.UserOut])
def list_users(
    db: Session = Depends(get_db),
    _admin: models.User = Depends(require_admin),
):
    """List dashboard accounts. Admin only."""
    return db.query(models.User).order_by(models.User.username).all()


@router.put("/{user_id}/role", response_model=schemas.UserOut)
def update_user_role(
    user_id: int,
    payload: schemas.UserRoleUpdate,
    db: Session = Depends(get_db),
    _admin: models.User = Depends(require_admin),
):
    """Change an account's role while ensuring at least one admin remains."""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if user.role == payload.role:
        return user
    if user.role == "admin" and _admin_count(db) <= 1:
        raise HTTPException(
            status_code=400,
            detail="At least one admin account is required",
        )

    user.role = payload.role
    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_admin),
):
    """Delete an account. Admins cannot delete themselves or the last admin."""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == admin.id:
        raise HTTPException(
            status_code=400,
            detail="You cannot delete your own account",
        )
    if user.role == "admin" and _admin_count(db) <= 1:
        raise HTTPException(
            status_code=400,
            detail="At least one admin account is required",
        )

    db.delete(user)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
