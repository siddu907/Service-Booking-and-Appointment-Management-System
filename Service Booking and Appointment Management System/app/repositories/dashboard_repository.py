from sqlalchemy.orm import Session

from app.models.booking import Booking
from app.models.payment import Payment
from app.models.review import Review
from app.models.service import Service
from app.models.user import User


class DashboardRepository:
    def __init__(self, db: Session):
        self.db = db

    def admin_stats(self):
        customers = self.db.query(User).filter(User.role == "Customer").count()
        providers = self.db.query(User).filter(User.role == "Service Provider").count()
        services = self.db.query(Service).filter(Service.is_deleted.is_(False)).count()
        bookings = self.db.query(Booking).filter(Booking.is_deleted.is_(False)).count()
        completed = self.db.query(Booking).filter(Booking.status == "Completed", Booking.is_deleted.is_(False)).count()
        cancelled = self.db.query(Booking).filter(Booking.status == "Cancelled", Booking.is_deleted.is_(False)).count()
        revenue = sum(
            p.amount for p in self.db.query(Payment)
            .join(Booking)
            .filter(Payment.status == "Paid", Booking.is_deleted.is_(False))
            .all()
        )
        return {
            "total_customers": customers,
            "total_service_providers": providers,
            "total_services": services,
            "total_bookings": bookings,
            "completed_bookings": completed,
            "cancelled_bookings": cancelled,
            "total_revenue": revenue,
        }

    def provider_stats(self, provider_id: int, today_date):
        today_appointments = self.db.query(Booking).filter(
            Booking.provider_id == provider_id,
            Booking.status == "Confirmed",
            Booking.appointment_date == today_date,
        ).count()
        upcoming = self.db.query(Booking).filter(
            Booking.provider_id == provider_id,
            Booking.status == "Confirmed",
            Booking.appointment_date >= today_date,
        ).count()
        completed = self.db.query(Booking).filter(
            Booking.provider_id == provider_id,
            Booking.status == "Completed",
        ).count()
        earnings = sum(
            p.amount for p in self.db.query(Payment)
            .join(Booking)
            .filter(
                Booking.provider_id == provider_id,
                Booking.is_deleted.is_(False),
                Payment.status == "Paid",
            )
            .all()
        )
        reviews = self.db.query(Review).filter(Review.provider_id == provider_id).all()
        average_rating = sum(r.rating for r in reviews) / len(reviews) if reviews else 0.0
        return {
            "today_appointments": today_appointments,
            "upcoming_appointments": upcoming,
            "completed_appointments": completed,
            "total_earnings": earnings,
            "average_rating": average_rating,
        }
