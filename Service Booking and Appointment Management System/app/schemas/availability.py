from datetime import date, time

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

from app.utils.validators import format_duration, parse_duration, parse_time


class AvailabilityCreate(BaseModel):
    availability_date: date = Field(..., example="2026-08-10")
    start_time: time = Field(..., example="9:00AM")
    end_time: time = Field(..., example="4:00PM")
    service_id: int | None = Field(None, example=1)
    slot_duration: int = Field(30, example="30min")
    slot_duration_minutes: int | None = Field(None, example=30)
    status: str = Field("available", example="available")

    @field_validator("start_time", "end_time", mode="before")
    def parse_times(cls, value: str | time) -> time:
        return parse_time(value)

    @field_validator("slot_duration", mode="before")
    def parse_slot_duration(cls, value: str | int) -> int:
        return parse_duration(value)


class AvailabilityUpdate(BaseModel):
    availability_date: date | None = Field(None, example="2026-08-10")
    start_time: time | None = Field(None, example="9:00AM")
    end_time: time | None = Field(None, example="4:00PM")
    service_id: int | None = Field(None, example=1)
    slot_duration: int | None = Field(None, example="30min")
    slot_duration_minutes: int | None = Field(None, example=30)
    status: str | None = Field(None, example="available")

    @field_validator("start_time", "end_time", mode="before")
    def parse_times(cls, value: str | time | None) -> time | None:
        if value is None:
            return None
        return parse_time(value)

    @field_validator("slot_duration", mode="before")
    def parse_slot_duration(cls, value: str | int | None) -> int | None:
        if value is None:
            return None
        return parse_duration(value)


class SlotOut(BaseModel):
    model_config = ConfigDict(
        json_encoders={
            time: lambda value: value.strftime("%I:%M%p").lstrip("0"),
        }
    )

    provider_id: int
    provider_name: str | None = None
    service_id: int | None = None
    service_name: str | None = None
    availability_date: date
    start_time: time
    end_time: time
    slot_duration: str

    @field_validator("slot_duration", mode="before")
    def format_slot_duration(cls, value: int | str) -> str:
        if isinstance(value, int):
            return format_duration(value)
        return str(value)


class AvailabilityOut(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            time: lambda value: value.strftime("%I:%M%p").lstrip("0"),
        },
    )

    id: int
    provider_id: int
    service_id: int | None = None
    service_name: str | None = None
    availability_date: date
    start_time: time
    end_time: time
    slot_duration: str
    status: str

    @field_validator("slot_duration", mode="before")
    def format_slot_duration(cls, value: int | str) -> str:
        if isinstance(value, int):
            return format_duration(value)
        return str(value)
