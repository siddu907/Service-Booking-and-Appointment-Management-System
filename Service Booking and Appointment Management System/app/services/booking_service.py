from datetime import datetime, date, time

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.booking import Booking
from app.models.coupon import Coupon
from app.models.payment import Payment
from app.models.notification import Notification
from app.models.service import Service
from app.models.user import User
from app.repositories.availability_repository import AvailabilityRepository
from app.repositories.booking_repository import BookingRepository
from app.repositories.notification_repository import NotificationRepository
from app.repositories.payment_repository import PaymentRepository
from app.schemas.booking import BookingCreate
from app.services.coupon_service import CouponService


class BookingService:
    def __init__(self, db: Session):
        self.db = db
        self.booking_repo = BookingRepository(db)
        self.payment_repo = PaymentRepository(db)
        self.notification_repo = NotificationRepository(db)
        self.availability_repo = AvailabilityRepository(db)

    def create_booking(self, user: User, booking_in: BookingCreate) -> Booking:
        if booking_in.start_time >= booking_in.end_time:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Start time must be before end time")
        if booking_in.appointment_date < date.today():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Appointment date cannot be in the past")

        if booking_in.appointment_date == date.today():
            now = datetime.now()
            appointment_start = datetime.combine(booking_in.appointment_date, booking_in.start_time)
            if appointment_start <= now:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Time completed. Please select a future time slot.")

        service = self.db.query(Service).filter(Service.id == booking_in.service_id, Service.is_deleted.is_(False)).first()
        if not service or service.status.lower() != "active":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found or inactive")

        coupon_service = CouponService(self.db)
        original_amount = service.price
        discount_amount = 0.0
        coupon_code = None
        total_amount = original_amount

        if booking_in.coupon_code:
            coupon, total_amount = coupon_service.apply_coupon(booking_in.coupon_code, original_amount)
            discount_amount = original_amount - total_amount
            coupon_code = coupon.code

        if self.booking_repo.exists_for_slot(service.provider_id, booking_in.appointment_date, booking_in.start_time, booking_in.end_time):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Slot already booked")

        if self.booking_repo.exists_for_customer_slot(user.id, service.provider_id, booking_in.appointment_date, booking_in.start_time, booking_in.end_time):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You already have a booking for this time slot")

        slots = self.availability_repo.get_available_slots(service.provider_id, booking_in.appointment_date, service_id=service.id)
        if not any(
            (slot.get("start_time") is not None and slot.get("end_time") is not None and
             slot.get("start_time").strftime("%H:%M:%S") == booking_in.start_time.strftime("%H:%M:%S") and
             slot.get("end_time").strftime("%H:%M:%S") == booking_in.end_time.strftime("%H:%M:%S"))
            for slot in slots
        ):
            # include available slot strings to aid debugging in tests/logs
            available_strs = [f"{s.get('start_time')} - {s.get('end_time')}" for s in slots]
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Requested timeslot is not an exact available slot. Available: {available_strs}")

        booking = Booking(
            customer_id=user.id,
            service_id=service.id,
            provider_id=service.provider_id,
            appointment_date=booking_in.appointment_date,
            start_time=booking_in.start_time,
            end_time=booking_in.end_time,
            original_amount=original_amount,
            discount_amount=discount_amount,
            coupon_code=coupon_code,
            total_amount=total_amount,
            status="Pending",
            reminder_sent=False,
        )
        try:
            booking = self.booking_repo.create(booking)
            payment = Payment(booking_id=booking.id, amount=booking.total_amount, payment_method="Cash", status="Pending")
            self.payment_repo.create(payment)
            self.notification_repo.create(Notification(user_id=service.provider_id, title="New Booking", message=f"New booking request #{booking.id} was received.", booking_id=booking.id, service_name=service.name, created_at=datetime.utcnow()))
            self.notification_repo.create(Notification(user_id=user.id, title="Booking Requested", message=f"Your booking request #{booking.id} is pending provider confirmation.", booking_id=booking.id, service_name=service.name, created_at=datetime.utcnow()))
        except IntegrityError as exc:
            self.db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Requested timeslot is already booked") from exc

        if booking.coupon_code:
            coupon = self.db.query(Coupon).filter(Coupon.code == booking.coupon_code).first()
            if coupon:
                coupon_service.increment_usage(coupon)

        return booking

    def _ensure_not_cancelled(self, booking: Booking) -> None:
        if booking.status == "Cancelled":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot modify a cancelled booking")

    def _ensure_confirmable(self, booking: Booking) -> None:
        if booking.status != "Pending":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only pending bookings can be confirmed or rejected")

    def _ensure_completable(self, booking: Booking) -> None:
        if booking.status != "Confirmed":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only confirmed bookings can be completed")

    def _is_exact_slot_available(self, provider_id: int, appointment_date: date, start_time: time, end_time: time, service_id: int | None = None) -> bool:
        # compare using formatted time strings to avoid mismatches across time objects
        target_start = start_time.strftime("%H:%M:%S")
        target_end = end_time.strftime("%H:%M:%S")
        for slot in self.availability_repo.get_available_slots(provider_id, appointment_date, service_id=service_id):
            s = slot.get("start_time")
            e = slot.get("end_time")
            if s is None or e is None:
                continue
            try:
                if s.strftime("%H:%M:%S") == target_start and e.strftime("%H:%M:%S") == target_end:
                    return True
            except Exception:
                # fallback to string comparison
                if str(s) == str(start_time) and str(e) == str(end_time):
                    return True
        return False

    def cancel_booking(self, booking: Booking) -> Booking:
        if booking.status == "Cancelled":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Booking is already cancelled")
        booking.status = "Cancelled"
        updated = self.booking_repo.update(booking)
        svc_name = booking.service.name if booking.service is not None else None
        self.notification_repo.create(Notification(user_id=booking.customer_id, title="Booking Cancelled", message=f"Your booking #{booking.id} has been cancelled.", booking_id=booking.id, service_name=svc_name, created_at=datetime.utcnow()))
        self.notification_repo.create(Notification(user_id=booking.provider_id, title="Booking Cancelled", message=f"Booking #{booking.id} was cancelled.", booking_id=booking.id, service_name=svc_name, created_at=datetime.utcnow()))
        return updated

    def reject_booking(self, booking: Booking) -> Booking:
        self._ensure_confirmable(booking)
        booking.status = "Cancelled"
        updated = self.booking_repo.update(booking)
        svc_name = booking.service.name if booking.service is not None else None
        self.notification_repo.create(Notification(user_id=booking.customer_id, title="Booking Rejected", message=f"Your booking #{booking.id} has been rejected.", booking_id=booking.id, service_name=svc_name, created_at=datetime.utcnow()))
        self.notification_repo.create(Notification(user_id=booking.provider_id, title="Booking Rejected", message=f"You rejected booking #{booking.id}.", booking_id=booking.id, service_name=svc_name, created_at=datetime.utcnow()))
        return updated

    def confirm_booking(self, booking: Booking) -> Booking:
        self._ensure_confirmable(booking)
        booking.status = "Confirmed"
        updated = self.booking_repo.update(booking)
        svc_name = booking.service.name if booking.service is not None else None
        self.notification_repo.create(Notification(user_id=booking.customer_id, title="Booking Confirmed", message=f"Your booking #{booking.id} has been confirmed.", booking_id=booking.id, service_name=svc_name, created_at=datetime.utcnow()))
        self.notification_repo.create(Notification(user_id=booking.provider_id, title="Booking Confirmed", message=f"Booking #{booking.id} has been confirmed.", booking_id=booking.id, service_name=svc_name, created_at=datetime.utcnow()))
        return updated

    def reschedule_booking(self, booking: Booking, new_date, new_start, new_end) -> Booking:
        self._ensure_not_cancelled(booking)
        if booking.status == "Completed":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot reschedule a completed booking")
        if new_date is None or new_start is None or new_end is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New appointment date and time are required")
        if new_start >= new_end:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Start time must be before end time")
        if new_date < date.today():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Appointment date cannot be in the past")
        if self.booking_repo.exists_for_slot(booking.provider_id, new_date, new_start, new_end, exclude_booking_id=booking.id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Requested new timeslot is already booked")
        if not self._is_exact_slot_available(booking.provider_id, new_date, new_start, new_end):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Requested new timeslot is not an exact available slot")
        booking.appointment_date = new_date
        booking.start_time = new_start
        booking.end_time = new_end
        booking.status = "Pending"
        booking.reminder_sent = False
        updated = self.booking_repo.update(booking)
        svc_name = booking.service.name if booking.service is not None else None
        self.notification_repo.create(Notification(user_id=booking.customer_id, title="Booking Rescheduled", message=f"Your booking #{booking.id} has been rescheduled.", booking_id=booking.id, service_name=svc_name, created_at=datetime.utcnow()))
        self.notification_repo.create(Notification(user_id=booking.provider_id, title="Booking Rescheduled", message=f"Booking #{booking.id} has been rescheduled.", booking_id=booking.id, service_name=svc_name, created_at=datetime.utcnow()))
        return updated

    def complete_booking(self, booking: Booking) -> Booking:
        self._ensure_completable(booking)
        booking.status = "Completed"
        updated = self.booking_repo.update(booking)
        svc_name = booking.service.name if booking.service is not None else None
        self.notification_repo.create(Notification(user_id=booking.customer_id, title="Booking Completed", message=f"Your booking #{booking.id} is completed.", booking_id=booking.id, service_name=svc_name, created_at=datetime.utcnow()))
        self.notification_repo.create(Notification(user_id=booking.provider_id, title="Booking Completed", message=f"Booking #{booking.id} has been completed.", booking_id=booking.id, service_name=svc_name, created_at=datetime.utcnow()))
        return updated
