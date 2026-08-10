from sqlalchemy.orm import Session

from app.models.payment import Payment
from app.models.booking import Booking


class PaymentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, payment: Payment) -> Payment:
        self.db.add(payment)
        self.db.commit()
        self.db.refresh(payment)
        return payment

    def get_all(self, user_id: int | None = None, role: str | None = None, skip: int = 0, limit: int = 100):
        query = self.db.query(Payment)
        if role == "Customer" and user_id is not None:
            query = query.join(Booking).filter(Booking.customer_id == user_id)
        if role == "Service Provider" and user_id is not None:
            query = query.join(Booking).filter(Booking.provider_id == user_id)
        return query.offset(skip).limit(limit).all()

    def get_by_booking_id(self, booking_id: int) -> Payment | None:
        return self.db.query(Payment).filter(Payment.booking_id == booking_id).first()

    def get_by_id(self, payment_id: int) -> Payment | None:
        return self.db.query(Payment).filter(Payment.id == payment_id).first()

    def update(self, payment: Payment) -> Payment:
        self.db.commit()
        self.db.refresh(payment)
        return payment
