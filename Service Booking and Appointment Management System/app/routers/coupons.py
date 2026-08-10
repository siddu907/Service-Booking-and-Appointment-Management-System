from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.oauth2 import get_current_user
from app.database import get_db
from app.schemas.coupon import CouponCreate, CouponOut
from app.services.coupon_service import CouponService
from app.models.user import User

router = APIRouter()


@router.post("", response_model=CouponOut)
def create_coupon(payload: CouponCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "Admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
    return CouponService(db).create_coupon(payload)


@router.get("", response_model=list[CouponOut])
def list_coupons(current_user: User = Depends(get_current_user), db: Session = Depends(get_db), skip: int = 0, limit: int = 100):
    if current_user.role not in {"Admin", "Customer", "Service Provider"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
    return CouponService(db).repo.list_all(skip=skip, limit=limit)
