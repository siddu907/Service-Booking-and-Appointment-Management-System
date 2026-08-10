from datetime import date, time

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.utils.validators import parse_time


class BookingCreate(BaseModel):
    appointment_date: date = Field(..., example="2026-08-10")
    start_time: time = Field(..., example="9:00AM")
    end_time: time = Field(..., example="11:00AM")
    service_id: int = Field(..., example=1)
    coupon_code: str | None = Field(None, example="SUMMER10")

    @field_validator("start_time", "end_time", mode="before")
    def parse_times(cls, value: str | time) -> time:
        return parse_time(value)


class BookingUpdate(BaseModel):
    appointment_date: date | None = Field(None, example="2026-08-10")
    start_time: time | None = Field(None, example="9:00AM")
    end_time: time | None = Field(None, example="11:00AM")
    status: str | None = Field(None, example="rescheduled")

    @field_validator("start_time", "end_time", mode="before")
    def parse_times(cls, value: str | time | None) -> time | None:
        if value is None:
            return None
        return parse_time(value)


class BookingOut(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            time: lambda value: value.strftime("%I:%M%p").lstrip("0"),
        },
    )

    id: int
    customer_id: int
    service_id: int
    provider_id: int
    customer_name: str | None = None
    service_name: str | None = None
    provider_name: str | None = None
    appointment_date: date
    start_time: time
    end_time: time
    original_amount: float
    discount_amount: float
    coupon_code: str | None = None
    total_amount: float
    status: str
