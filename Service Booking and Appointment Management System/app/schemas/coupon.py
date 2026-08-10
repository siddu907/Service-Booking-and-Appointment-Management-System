from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class CouponCreate(BaseModel):
    code: str
    description: str | None = None
    discount_percent: float | None = Field(default=None, ge=0.0, le=100.0)
    expires_at: datetime | None = None
    usage_limit: int | None = Field(default=None, ge=1)

    @field_validator("code")
    def normalize_code(cls, value: str) -> str:
        code = value.strip()
        if not code:
            raise ValueError("Coupon code must not be blank")
        return code.upper()

    @model_validator(mode="after")
    def validate_discount(cls, values):
        if values.discount_percent is None or values.discount_percent <= 0:
            raise ValueError("Coupon must include a positive discount_percent")
        return values


class CouponOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    description: str | None = None
    discount_percent: float
    expires_at: datetime | None = None
    is_active: bool
    usage_limit: int | None = None
    used_count: int


class ApplyCouponRequest(BaseModel):
    coupon_code: str
