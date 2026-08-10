from datetime import datetime

from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.repositories.notification_repository import NotificationRepository


class NotificationService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = NotificationRepository(db)

    def create(self, user_id: int, title: str, message: str, booking_id: int | None = None, service_name: str | None = None) -> Notification:
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            booking_id=booking_id,
            service_name=service_name,
            created_at=datetime.utcnow(),
        )
        return self.repo.create(notification)

    def list_for_user(self, user_id: int, skip: int = 0, limit: int = 100):
        return self.repo.get_for_user(user_id, skip=skip, limit=limit)

    def mark_read(self, notification: Notification) -> Notification:
        return self.repo.mark_read(notification)
