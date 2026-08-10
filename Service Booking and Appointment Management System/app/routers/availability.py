from datetime import date

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.oauth2 import get_current_user, get_current_user_optional
from app.core.permissions import require_roles
from app.database import get_db
from app.models.availability import Availability
from app.models.user import User
from app.repositories.availability_repository import AvailabilityRepository
from app.repositories.service_repository import ServiceRepository
from app.schemas.availability import AvailabilityCreate, AvailabilityOut, AvailabilityUpdate, SlotOut
from app.utils.validators import format_duration

router = APIRouter()


def _availability_to_response(availability: Availability) -> dict:
    duration_value = getattr(availability, "slot_duration_minutes", None)
    if duration_value is None:
        duration_value = 30
    try:
        slot_duration = format_duration(int(duration_value))
    except (TypeError, ValueError):
        try:
            slot_duration = format_duration(int(str(duration_value).split()[0]))
        except Exception:
            slot_duration = "30min"

    service_id = getattr(availability, "service_id", None)
    service_name = None
    if getattr(availability, "service", None) is not None:
        try:
            service_name = availability.service.name
            if service_id is None:
                service_id = availability.service.id
        except Exception:
            service_name = None

    return {
        "id": availability.id,
        "provider_id": availability.provider_id,
        "service_id": service_id,
        "service_name": service_name,
        "availability_date": availability.availability_date,
        "start_time": availability.start_time,
        "end_time": availability.end_time,
        "slot_duration": slot_duration,
        "status": availability.status,
    }


@router.post("", response_model=AvailabilityOut)
async def create_availability(
    request: Request,
    payload: AvailabilityCreate = Body(
        ...,
        example={
            "availability_date": "2026-08-10",
            "start_time": "9:00AM",
            "end_time": "4:00PM",
            "service_id": 1,
            "slot_duration": "30min",
            "status": "available",
        },
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_roles(current_user, {"Service Provider", "Admin"})

    if payload.availability_date < date.today():
        raise HTTPException(status_code=400, detail="Availability date cannot be in the past. Please select today or a future date.")

    try:
        if payload.start_time >= payload.end_time:
            raise HTTPException(status_code=400, detail="Availability start_time must be before end_time")
    except Exception:
        raise HTTPException(status_code=400, detail="Availability start_time and end_time must be valid times")

    if payload.service_id is not None:
        service = ServiceRepository(db).get_by_id(payload.service_id)
        if not service:
            raise HTTPException(status_code=404, detail="Service not found")
        if current_user.role == "Service Provider" and service.provider_id != current_user.id:
            raise HTTPException(status_code=403, detail="Service does not belong to the current provider")
    repo = AvailabilityRepository(db)
    if repo.exists_overlapping(current_user.id, payload.availability_date, payload.start_time, payload.end_time):
        raise HTTPException(status_code=400, detail="Availability overlaps with an existing slot")
    # prefer explicit numeric minutes if sent by the client
    data = payload.model_dump()
    raw = await request.json()
    if "slot_duration_minutes" in raw and raw["slot_duration_minutes"] is not None:
        data["slot_duration_minutes"] = int(raw["slot_duration_minutes"])
    elif "slot_duration" in data and data["slot_duration"] is not None:
        data["slot_duration_minutes"] = data.pop("slot_duration")
    elif "slot_duration_minutes" not in data:
        data["slot_duration_minutes"] = 30
    # ensure we don't pass a read-only `slot_duration` property to SQLAlchemy
    if "slot_duration" in data:
        data.pop("slot_duration", None)
    availability = Availability(provider_id=current_user.id, **data)
    created = repo.create(availability)
    return _availability_to_response(created)


@router.get("", response_model=list[AvailabilityOut])
def list_availability(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    availabilities = AvailabilityRepository(db).get_all(provider_id=current_user.id if current_user.role == "Service Provider" else None)
    return [_availability_to_response(item) for item in availabilities]



@router.put("/{availability_id}", response_model=AvailabilityOut)
def update_availability(availability_id: int, payload: AvailabilityUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    availability = AvailabilityRepository(db).get_by_id(availability_id)
    if not availability:
        raise HTTPException(status_code=404, detail="Availability not found")
    if current_user.role != "Admin" and availability.provider_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed")
    data = payload.model_dump(exclude_unset=True)
    try:
        if "start_time" in data and "end_time" in data and data["start_time"] >= data["end_time"]:
            raise HTTPException(status_code=400, detail="Availability start_time must be before end_time")
    except Exception:
        raise HTTPException(status_code=400, detail="Availability start_time and end_time must be valid times")
    if "availability_date" in data:
        availability.availability_date = data["availability_date"]
    if "service_id" in data and data["service_id"] is not None:
        service = ServiceRepository(db).get_by_id(data["service_id"])
        if not service:
            raise HTTPException(status_code=404, detail="Service not found")
        if current_user.role == "Service Provider" and service.provider_id != availability.provider_id:
            raise HTTPException(status_code=403, detail="Service does not belong to the current provider")
    if "start_time" in data:
        availability.start_time = data["start_time"]
    if "end_time" in data:
        availability.end_time = data["end_time"]
    if "start_time" in data or "end_time" in data or "availability_date" in data:
        start_time = availability.start_time
        end_time = availability.end_time
        if start_time >= end_time:
            raise HTTPException(status_code=400, detail="Availability start_time must be before end_time")
        if AvailabilityRepository(db).exists_overlapping(availability.provider_id, availability.availability_date, start_time, end_time, exclude_id=availability.id):
            raise HTTPException(status_code=400, detail="Availability overlaps with an existing slot")
    for key, value in data.items():
        if key == "slot_duration":
            setattr(availability, "slot_duration_minutes", value)
        elif key not in {"availability_date", "start_time", "end_time"}:
            setattr(availability, key, value)
    updated = AvailabilityRepository(db).update(availability)
    return _availability_to_response(updated)


@router.delete("/{availability_id}")
def delete_availability(availability_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    availability = AvailabilityRepository(db).get_by_id(availability_id)
    if not availability:
        raise HTTPException(status_code=404, detail="Availability not found")
    if current_user.role != "Admin" and availability.provider_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed")
    AvailabilityRepository(db).delete(availability)
    return {"message": "Availability deleted"}

@router.get("/providers/available-slots", response_model=list[SlotOut])
def provider_available_slots(
    provider_id: int | None = None,
    availability_date: date | None = None,
    service_id: int | None = None,
    current_user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    role_lower = current_user.role.strip().lower() if current_user and current_user.role else ""
    if role_lower == "customer" and availability_date is not None and availability_date < date.today():
        raise HTTPException(status_code=400, detail="Customers cannot search past dates")

    if role_lower == "service provider":
        if provider_id is not None and provider_id != current_user.id:
            raise HTTPException(status_code=403, detail="Service providers may only view their own available slots")
        if service_id is not None:
            service = ServiceRepository(db).get_by_id(service_id)
            if not service:
                raise HTTPException(status_code=404, detail="Service not found")
            if service.provider_id != current_user.id:
                raise HTTPException(status_code=403, detail="Service does not belong to the current provider")
        provider_id = current_user.id
    else:
        if service_id is not None:
            service = ServiceRepository(db).get_by_id(service_id)
            if not service:
                raise HTTPException(status_code=404, detail="Service not found")
            if provider_id is None:
                provider_id = service.provider_id
            elif provider_id != service.provider_id:
                raise HTTPException(status_code=403, detail="Service does not belong to the requested provider")
    # The public available-slots endpoint should behave like a customer-facing view for
    # customers, anonymous users, and admins, while providers can still see the raw availability list.
    customer_view = role_lower != "service provider"
    return AvailabilityRepository(db).get_available_slots(provider_id, availability_date, customer_view=customer_view, service_id=service_id)
