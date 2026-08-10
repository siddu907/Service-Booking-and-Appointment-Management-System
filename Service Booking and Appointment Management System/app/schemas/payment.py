from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PaymentCreate(BaseModel):
    booking_id: int
    payment_method: str = "Cash"


class PaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    booking_id: int
    amount: float
    payment_method: str
    payment_date: datetime | None = None
    status: str
