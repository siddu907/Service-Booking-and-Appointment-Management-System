from datetime import date, time, datetime, timedelta
from sqlalchemy.orm import Session

from app.models.availability import Availability
from app.models.booking import Booking
from app.models.service import Service
from app.utils.validators import parse_duration


class AvailabilityRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, availability: Availability) -> Availability:
        self.db.add(availability)
        self.db.commit()
        self.db.refresh(availability)
        if getattr(availability, "service_id", None) is None and getattr(availability, "service", None) is not None:
            try:
                availability.service_id = availability.service.id
                self.db.commit()
                self.db.refresh(availability)
            except Exception:
                pass
        return availability

    def get_all(self, provider_id: int | None = None, from_date: date | None = None):
        query = self.db.query(Availability).filter(Availability.is_deleted.is_(False))
        if provider_id is not None:
            query = query.filter(Availability.provider_id == provider_id)
        if from_date is not None:
            query = query.filter(Availability.availability_date >= from_date)
        return query.all()

    def get_by_id(self, availability_id: int) -> Availability | None:
        return self.db.query(Availability).filter(Availability.id == availability_id, Availability.is_deleted.is_(False)).first()

    def exists_overlapping(self, provider_id: int, availability_date, start_time, end_time, exclude_id: int | None = None) -> bool:
        query = self.db.query(Availability).filter(
            Availability.provider_id == provider_id,
            Availability.availability_date == availability_date,
            Availability.is_deleted.is_(False),
            Availability.start_time < end_time,
            Availability.end_time > start_time,
        )
        if exclude_id is not None:
            query = query.filter(Availability.id != exclude_id)
        return self.db.query(query.exists()).scalar()

    def is_available(self, provider_id: int, appointment_date, start_time, end_time) -> bool:
        return self.db.query(Availability).filter(
            Availability.provider_id == provider_id,
            Availability.availability_date == appointment_date,
            Availability.status == "available",
            Availability.is_deleted.is_(False),
            Availability.start_time <= start_time,
            Availability.end_time >= end_time,
        ).first() is not None

    def _generate_slots(self, start_time: time, end_time: time, duration_minutes: int) -> list[tuple[time, time]]:
        start_dt = datetime.combine(date.today(), start_time)
        end_dt = datetime.combine(date.today(), end_time)
        slots: list[tuple[time, time]] = []
        while start_dt + timedelta(minutes=duration_minutes) <= end_dt:
            next_dt = start_dt + timedelta(minutes=duration_minutes)
            slots.append((start_dt.time(), next_dt.time()))
            start_dt = next_dt
        return slots

    def _slot_is_free(self, slot_start: time, slot_end: time, bookings: list[Booking]) -> bool:
        return all(
            not (booking.start_time < slot_end and booking.end_time > slot_start)
            for booking in bookings
        )

    def _normalize_duration_minutes(self, value) -> int:
        if value is None:
            return 30
        if isinstance(value, str):
            try:
                return parse_duration(value)
            except ValueError:
                return 30
        if isinstance(value, int):
            return value if value > 0 else 30
        try:
            return int(value)
        except (TypeError, ValueError):
            return 30

    def get_available_slots(self, provider_id: int | None, appointment_date: date | None, customer_view: bool = True, service_id: int | None = None) -> list[dict]:
        # build base query for availabilities, optionally filter by provider, date, and service
        query = self.db.query(Availability).filter(
            Availability.status == "available",
            Availability.is_deleted.is_(False),
        )
        if appointment_date is not None:
            query = query.filter(Availability.availability_date == appointment_date)
        if provider_id is not None:
            query = query.filter(Availability.provider_id == provider_id)
        # deterministic ordering: by date then start_time
        query = query.order_by(Availability.availability_date, Availability.start_time)
        if service_id is not None:
            # include availabilities that are either specific to the service or general (service_id IS NULL)
            from sqlalchemy import or_

            query = query.filter(or_(Availability.service_id == service_id, Availability.service_id.is_(None)))
        availabilities = query.all()

        available_slots: list[dict] = []
        now = datetime.utcnow()
        today = now.date()
        now_time = now.time()

        bookings_by_provider_date: dict[tuple[int | None, date], list[Booking]] = {}

        for availability in availabilities:
            try:
                availability_date = availability.availability_date
                start_time = availability.start_time
                end_time = availability.end_time
                duration_minutes = self._normalize_duration_minutes(getattr(availability, 'slot_duration_minutes', None))
            except Exception:
                continue

            if customer_view and availability_date < today:
                continue

            provider_id = availability.provider_id
            provider_name = None
            if getattr(availability, "provider", None) is not None:
                try:
                    provider_name = availability.provider.full_name
                except Exception:
                    provider_name = None

            # prefer the availability's own service id; fall back to the related service or the request filter
            resolved_service_id = (
                availability.service_id
                if getattr(availability, "service_id", None) is not None
                else (
                    availability.service.id
                    if getattr(availability, "service", None) is not None and getattr(availability.service, "id", None) is not None
                    else service_id
                )
            )
            service_obj = None
            if getattr(availability, "service", None) is not None:
                service_obj = availability.service
            elif resolved_service_id is not None:
                service_obj = self.db.query(Service).filter(Service.id == resolved_service_id, Service.is_deleted.is_(False)).first()
            service_name = None
            if service_obj is not None:
                try:
                    service_name = service_obj.name
                except Exception:
                    service_name = None

            if customer_view:
                key = (provider_id, availability_date)
                if key not in bookings_by_provider_date:
                    bquery = self.db.query(Booking).filter(
                        Booking.provider_id == provider_id,
                        Booking.status != "Cancelled",
                        Booking.is_deleted.is_(False),
                        Booking.appointment_date == availability_date,
                    )
                    bookings_by_provider_date[key] = bquery.all()
                bookings = bookings_by_provider_date[key]
            else:
                bookings = []

            for slot_start, slot_end in self._generate_slots(
                start_time,
                end_time,
                duration_minutes,
            ):
                if customer_view and availability_date == today and slot_start < now_time:
                    continue
                if customer_view and not self._slot_is_free(slot_start, slot_end, bookings):
                    continue
                available_slots.append(
                    {
                        "provider_id": provider_id,
                        "provider_name": provider_name,
                        "service_id": resolved_service_id,
                        "service_name": service_name,
                        "availability_date": availability_date,
                        "start_time": slot_start,
                        "end_time": slot_end,
                        "slot_duration": duration_minutes,
                    }
                )
        return available_slots

    def update(self, availability: Availability) -> Availability:
        self.db.commit()
        self.db.refresh(availability)
        if getattr(availability, "service_id", None) is None and getattr(availability, "service", None) is not None:
            try:
                availability.service_id = availability.service.id
                self.db.commit()
                self.db.refresh(availability)
            except Exception:
                pass
        return availability

    def delete(self, availability: Availability) -> None:
        availability.is_deleted = True
        self.db.commit()
