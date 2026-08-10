from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.oauth2 import get_current_user
from app.database import get_db
from app.models.booking import Booking
from app.models.payment import Payment
from app.models.user import User
from app.repositories.booking_repository import BookingRepository
from app.repositories.payment_repository import PaymentRepository
from app.schemas.payment import PaymentCreate, PaymentOut
from app.services.payment_service import PaymentService

router = APIRouter()


@router.get("", response_model=list[PaymentOut])
def list_payments(
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    return PaymentRepository(db).get_all(user_id=current_user.id, role=current_user.role, skip=skip, limit=limit)


@router.post("", response_model=PaymentOut)
def create_payment(payload: PaymentCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.id == payload.booking_id, Booking.is_deleted.is_(False)).first()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    if current_user.role != "Admin" and booking.customer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    amount = getattr(payload, "amount", None)
    amount = amount if amount is not None else booking.total_amount
    return PaymentService(db).create_payment(payload.booking_id, amount, payload.payment_method)


@router.get("/{payment_id}", response_model=PaymentOut)
def get_payment(payment_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    payment = PaymentRepository(db).get_by_id(payment_id)
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    booking = db.query(Booking).filter(Booking.id == payment.booking_id).first()
    if current_user.role != "Admin" and booking and booking.customer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
    return payment


@router.post("/{payment_id}/refund", response_model=PaymentOut)
def refund_payment(payment_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    payment = PaymentRepository(db).get_by_id(payment_id)
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")

    booking = db.query(Booking).filter(Booking.id == payment.booking_id).first()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    if current_user.role != "Admin" and booking.provider_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    return PaymentService(db).refund_payment(payment)
