from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.oauth2 import get_current_user
from app.core.permissions import require_roles
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserOut, UserOutNoImage, UserUpdate

router = APIRouter()


@router.get("", response_model=list[UserOutNoImage])
def list_users(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_roles(current_user, {"Admin"})
    return db.query(User).filter(User.is_deleted.is_(False)).all()


@router.get("/{user_id}", response_model=UserOutNoImage)
def get_user(user_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_roles(current_user, {"Admin"})
    user = db.query(User).filter(User.id == user_id, User.is_deleted.is_(False)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user
