from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.booking import Booking
from app.services.email_service import EmailService
from app.services.notification_service import NotificationService
from app.database import SessionLocal


def send_upcoming_reminders(db: Session | None = None):
    own_session = db is None
    if own_session:
        db = SessionLocal()
    try:
        service = NotificationService(db)
        upcoming_window = datetime.utcnow().date() + timedelta(days=1)
        bookings = db.query(Booking).filter(
            Booking.status == "Confirmed",
            Booking.reminder_sent.is_(False),
            Booking.appointment_date == upcoming_window,
            Booking.is_deleted.is_(False),
        ).all()
        for booking in bookings:
            message = f"Reminder: appointment for booking #{booking.id} is scheduled on {booking.appointment_date} at {booking.start_time}."
            service.create(
                booking.customer_id,
                "Appointment Reminder",
                message,
                booking_id=booking.id,
                service_name=booking.service.name if booking.service else None,
            )
            service.create(
                booking.provider_id,
                "Appointment Reminder",
                message,
                booking_id=booking.id,
                service_name=booking.service.name if booking.service else None,
            )
            if booking.customer and booking.customer.email:
                EmailService.send_email(booking.customer.email, "Appointment Reminder", message)
            if booking.provider and booking.provider.email:
                EmailService.send_email(booking.provider.email, "Appointment Reminder", message)
            booking.reminder_sent = True
        db.commit()
    finally:
        if own_session:
            db.close()
