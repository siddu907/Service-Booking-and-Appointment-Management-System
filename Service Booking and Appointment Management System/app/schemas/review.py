from pydantic import BaseModel, ConfigDict


class ReviewCreate(BaseModel):
    booking_id: int
    rating: int
    review: str | None = None


class ReviewUpdate(BaseModel):
    rating: int | None = None
    review: str | None = None


class ReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    booking_id: int
    customer_id: int
    provider_id: int
    rating: int
    review: str | None = None
