from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.coupon import Coupon
from app.repositories.coupon_repository import CouponRepository


class CouponService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = CouponRepository(db)

    def create_coupon(self, coupon_data) -> Coupon:
        if coupon_data.discount_percent is None or coupon_data.discount_percent <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Coupon must include a positive discount_percent")

        normalized_code = coupon_data.code.strip().upper()
        if self.repo.get_by_code(normalized_code):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Coupon code already exists")

        coupon = Coupon(
            code=normalized_code,
            description=coupon_data.description,
            discount_percent=coupon_data.discount_percent,
            expires_at=coupon_data.expires_at,
            usage_limit=coupon_data.usage_limit,
            used_count=0,
            is_active=True,
        )
        try:
            return self.repo.create(coupon)
        except IntegrityError as exc:
            self.db.rollback()
            error_text = (str(exc.orig) if getattr(exc, "orig", None) is not None else str(exc)).lower()
            duplicate_markers = (
                "duplicate key",
                "duplicate",
                "already exists",
                "unique constraint",
                "violates unique",
                "key (code)",
            )
            if any(marker in error_text for marker in duplicate_markers):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Coupon code already exists") from exc
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to create coupon") from exc

    def apply_coupon(self, coupon_code: str, amount: float) -> tuple[Coupon, float]:
        coupon = self.repo.get_by_code(coupon_code)
        if not coupon:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Coupon not found")
        if not coupon.is_active:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Coupon is not active")
        if coupon.expires_at and coupon.expires_at < datetime.utcnow():
            coupon.is_active = False
            self.repo.update(coupon)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Coupon has expired")
        if coupon.usage_limit is not None and coupon.used_count >= coupon.usage_limit:
            coupon.is_active = False
            self.repo.update(coupon)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Coupon usage limit reached")

        discount = amount * (coupon.discount_percent / 100)
        discounted_total = max(amount - discount, 0.0)
        return coupon, discounted_total

    def increment_usage(self, coupon: Coupon) -> Coupon:
        return self.repo.increment_usage(coupon)
