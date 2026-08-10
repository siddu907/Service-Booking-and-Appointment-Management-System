from sqlalchemy.orm import Session

from app.models.notification import Notification


class NotificationRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, notification: Notification) -> Notification:
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        return notification

    def get_for_user(self, user_id: int, skip: int = 0, limit: int = 100):
        return self.db.query(Notification).filter(Notification.user_id == user_id).order_by(Notification.id.desc()).offset(skip).limit(limit).all()

    def mark_read(self, notification: Notification) -> Notification:
        notification.is_read = True
        self.db.commit()
        self.db.refresh(notification)
        return notification
