from datetime import datetime
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.coupon import Coupon


class CouponRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, coupon: Coupon) -> Coupon:
        coupon.code = (coupon.code or "").strip().upper()
        self.db.add(coupon)
        self.db.commit()
        self.db.refresh(coupon)
        return coupon

    def get_by_code(self, code: str) -> Coupon | None:
        normalized_code = (code or "").strip().upper()
        return self.db.query(Coupon).filter(func.upper(func.trim(Coupon.code)) == normalized_code).first()

    def get_by_id(self, coupon_id: int) -> Coupon | None:
        return self.db.query(Coupon).filter(Coupon.id == coupon_id).first()

    def list_all(self, skip: int = 0, limit: int = 100):
        return self.db.query(Coupon).offset(skip).limit(limit).all()

    def update(self, coupon: Coupon) -> Coupon:
        self.db.commit()
        self.db.refresh(coupon)
        return coupon

    def deactivate(self, coupon: Coupon) -> Coupon:
        coupon.is_active = False
        return self.update(coupon)

    def increment_usage(self, coupon: Coupon) -> Coupon:
        coupon.used_count += 1
        if coupon.usage_limit is not None and coupon.used_count >= coupon.usage_limit:
            coupon.is_active = False
        return self.update(coupon)
