from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.booking import Booking
from app.models.payment import Payment
from app.repositories.payment_repository import PaymentRepository


class PaymentService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = PaymentRepository(db)

    def create_payment(self, booking_id: int, amount: float, payment_method: str) -> Payment:
        booking = self.db.query(Booking).filter(Booking.id == booking_id, Booking.is_deleted.is_(False)).first()
        if not booking:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
        if amount is None:
            amount = booking.total_amount
        if abs(float(amount) - float(booking.total_amount)) > 1e-9:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payment amount must match booking total")

        existing_payment = self.repo.get_by_booking_id(booking_id)
        normalized_method_key = payment_method.strip().lower()
        display_method_map = {
            "cash": "Cash",
            "card": "Card",
            "upi": "UPI",
            "online": "Online",
        }
        method_status_map = {
            "cash": "Paid",
            "card": "Paid",
            "upi": "Paid",
            "online": "Paid",
        }
        normalized_method = display_method_map.get(normalized_method_key, payment_method.strip().title())
        status_value = method_status_map.get(normalized_method_key, "Failed")

        if existing_payment:
            if existing_payment.status == "Paid":
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A payment is already in process for this booking")
            existing_payment.amount = amount
            existing_payment.payment_method = normalized_method
            existing_payment.status = status_value
            existing_payment.payment_date = datetime.utcnow() if status_value in {"Paid", "Failed"} else None
            payment = self.repo.update(existing_payment)
        else:
            payment = Payment(
                booking_id=booking_id,
                amount=amount,
                payment_method=normalized_method,
                status=status_value,
                payment_date=datetime.utcnow() if status_value in {"Paid", "Failed"} else None,
            )
            payment = self.repo.create(payment)

        if status_value == "Paid" and booking.status == "Pending":
            booking.status = "Confirmed"
            self.db.commit()
            self.db.refresh(booking)

        return payment

    def refund_payment(self, payment: Payment) -> Payment:
        if payment.status != "Paid":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only paid payments can be refunded")
        payment.status = "Refunded"
        payment.payment_date = datetime.utcnow()
        return self.repo.update(payment)
