from datetime import date, time
from sqlalchemy.orm import Session, joinedload

from app.models.booking import Booking


class BookingRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, booking: Booking) -> Booking:
        self.db.add(booking)
        self.db.commit()
        self.db.refresh(booking)
        return booking

    def get_all(self, user_id: int | None = None, role: str | None = None, skip: int = 0, limit: int = 100):
        query = self.db.query(Booking).options(
            joinedload(Booking.customer),
            joinedload(Booking.service),
            joinedload(Booking.provider),
        ).filter(Booking.is_deleted.is_(False))
        if role == "Customer" and user_id is not None:
            query = query.filter(Booking.customer_id == user_id)
        if role == "Service Provider" and user_id is not None:
            query = query.filter(Booking.provider_id == user_id)
        return query.offset(skip).limit(limit).all()

    def get_by_id(self, booking_id: int) -> Booking | None:
        return self.db.query(Booking).options(
            joinedload(Booking.customer),
            joinedload(Booking.service),
            joinedload(Booking.provider),
        ).filter(Booking.id == booking_id, Booking.is_deleted.is_(False)).first()

    def update(self, booking: Booking) -> Booking:
        self.db.commit()
        self.db.refresh(booking)
        return booking

    def delete(self, booking: Booking) -> None:
        booking.is_deleted = True
        self.db.commit()

    def exists_for_slot(self, provider_id: int, appointment_date: date, start_time: time, end_time: time, exclude_booking_id: int | None = None) -> bool:
        query = self.db.query(Booking).filter(
            Booking.provider_id == provider_id,
            Booking.appointment_date == appointment_date,
            Booking.status != "Cancelled",
            Booking.start_time < end_time,
            Booking.end_time > start_time,
        )
        if exclude_booking_id is not None:
            query = query.filter(Booking.id != exclude_booking_id)
        return query.first() is not None

    def exists_for_customer_slot(self, customer_id: int, provider_id: int, appointment_date: date, start_time: time, end_time: time) -> bool:
        return self.db.query(Booking).filter(
            Booking.customer_id == customer_id,
            Booking.provider_id == provider_id,
            Booking.appointment_date == appointment_date,
            Booking.status != "Cancelled",
            Booking.start_time < end_time,
            Booking.end_time > start_time,
        ).first() is not None
