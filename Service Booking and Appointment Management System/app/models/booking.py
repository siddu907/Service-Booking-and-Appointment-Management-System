from datetime import datetime

from sqlalchemy import Boolean, Column, Date, DateTime, Float, ForeignKey, Integer, String, Time, UniqueConstraint, Index
from sqlalchemy.orm import relationship

from app.database import Base


class Booking(Base):
    __tablename__ = "bookings"
    __table_args__ = (
        Index("ix_booking_provider_date_time", "provider_id", "appointment_date", "start_time", "end_time"),
    )

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False)
    provider_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    appointment_date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    original_amount = Column(Float, nullable=False)
    discount_amount = Column(Float, nullable=False, default=0.0)
    coupon_code = Column(String, nullable=True)
    total_amount = Column(Float, nullable=False)
    status = Column(String, nullable=False, default="Pending")
    reminder_sent = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_deleted = Column(Boolean, default=False)

    customer = relationship("User", foreign_keys=[customer_id])
    provider = relationship("User", foreign_keys=[provider_id])
    service = relationship("Service", foreign_keys=[service_id])

    @property
    def customer_name(self) -> str | None:
        return self.customer.full_name if self.customer is not None else None

    @property
    def service_name(self) -> str | None:
        return self.service.name if self.service is not None else None

    @property
    def service_provider_name(self) -> str | None:
        return self.provider.full_name if self.provider is not None else None

    @property
    def provider_name(self) -> str | None:
        return self.provider.full_name if self.provider is not None else None
