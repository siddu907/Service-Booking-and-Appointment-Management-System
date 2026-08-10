from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=False)
    amount = Column(Float, nullable=False)
    payment_method = Column(String, nullable=False, default="Cash")
    payment_date = Column(DateTime, nullable=True)
    status = Column(String, nullable=False, default="Pending")

    booking = relationship("Booking", foreign_keys=[booking_id])
