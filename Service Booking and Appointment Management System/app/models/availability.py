from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String, Time
from sqlalchemy.orm import relationship

from app.database import Base


class Availability(Base):
    __tablename__ = "availability"

    id = Column(Integer, primary_key=True, index=True)
    provider_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=True)
    availability_date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    slot_duration_minutes = Column(Integer, nullable=False, default=30)
    status = Column(String, nullable=False, default="available")
    is_deleted = Column(Boolean, default=False)

    provider = relationship("User", foreign_keys=[provider_id])
    service = relationship("Service", foreign_keys=[service_id])

    @property
    def slot_duration(self) -> int:
        return self.slot_duration_minutes
