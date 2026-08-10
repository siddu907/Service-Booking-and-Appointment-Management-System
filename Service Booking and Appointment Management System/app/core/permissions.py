from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User


def require_roles(user: User, allowed_roles: set[str]):
    if user.role not in allowed_roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")


def require_owner_or_admin(user: User, owner_id: int):
    if user.role == "Admin" or user.id == owner_id:
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
