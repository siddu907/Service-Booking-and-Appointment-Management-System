from csv import writer
from io import StringIO

from fastapi import APIRouter, Body, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.oauth2 import get_current_user
from app.core.permissions import require_roles
from app.database import get_db
from app.models.booking import Booking
from app.models.user import User
from app.repositories.booking_repository import BookingRepository
from app.schemas.booking import BookingCreate, BookingOut, BookingUpdate
from app.services.booking_service import BookingService

router = APIRouter()


@router.post("", response_model=BookingOut)
def create_booking(
    payload: BookingCreate = Body(
        ...,
        example={
            "appointment_date": "2026-08-10",
            "start_time": "9:00AM",
            "end_time": "11:00AM",
            "service_id": 1,
            "coupon_code": "SUMMER10",
        },
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_roles(current_user, {"Customer", "Admin"})
    return BookingService(db).create_booking(current_user, payload)


@router.get("", response_model=list[BookingOut])
def list_bookings(
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    return BookingRepository(db).get_all(user_id=current_user.id, role=current_user.role, skip=skip, limit=limit)


@router.get("/export")
def export_bookings(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    bookings = BookingRepository(db).get_all(user_id=current_user.id, role=current_user.role, skip=0, limit=10000)
    output = StringIO()
    csv_writer = writer(output)
    csv_writer.writerow([
        "id",
        "customer_id",
        "service_id",
        "provider_id",
        "appointment_date",
        "start_time",
        "end_time",
        "total_amount",
        "status",
        "customer_name",
        "service_name",
        "provider_name",
    ])
    for booking in bookings:
        csv_writer.writerow([
            booking.id,
            booking.customer_id,
            booking.service_id,
            booking.provider_id,
            booking.appointment_date,
            booking.start_time,
            booking.end_time,
            booking.total_amount,
            booking.status,
            getattr(booking, "customer_name", None),
            getattr(booking, "service_name", None),
            getattr(booking, "provider_name", None),
        ])
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=bookings.csv"},
    )


@router.get("/{booking_id}", response_model=BookingOut)
def get_booking(booking_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    booking = BookingRepository(db).get_by_id(booking_id)
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    if current_user.role != "Admin" and booking.customer_id != current_user.id and booking.provider_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
    return booking


@router.put("/{booking_id}/confirm", response_model=BookingOut)
def confirm_booking(booking_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    booking = BookingRepository(db).get_by_id(booking_id)
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    if current_user.role != "Admin" and booking.provider_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
    return BookingService(db).confirm_booking(booking)


@router.put("/{booking_id}/reject", response_model=BookingOut)
def reject_booking(booking_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    booking = BookingRepository(db).get_by_id(booking_id)
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    if current_user.role != "Admin" and booking.provider_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
    return BookingService(db).reject_booking(booking)


@router.put("/{booking_id}/cancel", response_model=BookingOut)
def cancel_booking(booking_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    booking = BookingRepository(db).get_by_id(booking_id)
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    if current_user.role != "Admin" and booking.customer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
    return BookingService(db).cancel_booking(booking)


@router.put("/{booking_id}/reschedule", response_model=BookingOut)
def reschedule_booking(booking_id: int, payload: BookingUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    booking = BookingRepository(db).get_by_id(booking_id)
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    if current_user.role != "Admin" and booking.customer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
    return BookingService(db).reschedule_booking(booking, payload.appointment_date, payload.start_time, payload.end_time)


@router.put("/{booking_id}/complete", response_model=BookingOut)
def complete_booking(booking_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    booking = BookingRepository(db).get_by_id(booking_id)
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    if current_user.role != "Admin" and booking.provider_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
    return BookingService(db).complete_booking(booking)
