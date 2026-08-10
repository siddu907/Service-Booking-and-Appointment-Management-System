from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.oauth2 import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.notification import NotificationOut
from app.services.notification_service import NotificationService

router = APIRouter()


@router.get("", response_model=list[NotificationOut])
def list_notifications(
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    return NotificationService(db).list_for_user(current_user.id, skip=skip, limit=limit)


@router.put("/{notification_id}/read", response_model=NotificationOut)
def mark_notification_read(notification_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    service = NotificationService(db)
    notifications = service.list_for_user(current_user.id)
    notification = next((n for n in notifications if n.id == notification_id), None)
    if not notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    return service.mark_read(notification)
