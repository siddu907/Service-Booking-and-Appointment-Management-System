from sqlalchemy import Boolean, Column, Float, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String, nullable=False)
    duration = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    status = Column(String, nullable=False, default="active")
    provider_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    service_image = Column(String, nullable=True)
    is_deleted = Column(Boolean, default=False)

    provider = relationship("User", foreign_keys=[provider_id])

    @property
    def provider_profile_image(self) -> str | None:
        return self.provider.profile_image if self.provider is not None else None

    @property
    def provider_name(self) -> str | None:
        return self.provider.full_name if self.provider is not None else None

    @property
    @property
    def duration_readable(self) -> str | None:
        # keep a read-only accessor named `duration_readable` for compatibility
        return self.duration
